import json
import logging
from typing import Any, Dict

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.db import connection
from django.utils import timezone
from google.genai import types

from AuditSystem.services import AuditService
from CreatorProfile.models import CreatorProfile
from IdeaBank.models import Post, PostIdea
from IdeaBank.utils.current_week import get_current_week
from services.ai_prompt_service import AIPromptService
from services.ai_service import AiService
from services.s3_sevice import S3Service
from services.semaphore_service import SemaphoreService
from services.user_validation_service import UserValidationService

logger = logging.getLogger(__name__)


class DailyIdeasService:
    def __init__(self):
        self.user_validation_service = UserValidationService()
        self.semaphore_service = SemaphoreService()
        self.ai_service = AiService()
        self.prompt_service = AIPromptService()
        self.audit_service = AuditService()
        self.s3_service = S3Service()

    @sync_to_async
    def _get_eligible_users(self, offset: int, limit: int) -> list[dict[str, Any]]:
        """Get a batch of users eligible for weekly context generation"""

        if limit is None:
            return list(
                User.objects.extra(
                    where=["daily_generation_error IS NULL"]
                ).filter(
                    usersubscription__status='active',
                    is_active=True
                ).distinct().values('id', 'email', 'username')[offset:]
            )

        return list(
            User.objects.extra(
                where=["daily_generation_error IS NULL"]
            ).filter(
                usersubscription__status='active',
                is_active=True
            ).distinct().values('id', 'email', 'username')[offset:offset + limit]
        )

    async def process_daily_ideas_for_users(self, batch_number: int, batch_size: int) -> Dict[str, Any]:
        """Process daily ideas generation for a batch of users"""
        start_time = timezone.now()
        offset = (batch_number - 1) * batch_size
        limit = batch_size

        if batch_size == 0:
            offset = 0
            limit = None  # Process all users

        eligible_users = await self._get_eligible_users(offset=offset, limit=limit)
        total = len(eligible_users)

        if total == 0:
            return {
                'status': 'completed',
                'processed': 0,
                'total_users': 0,
                'message': 'No eligible users found',
            }

        try:
            results = await self.semaphore_service.process_concurrently(
                users=eligible_users,
                function=self.process_single_user
            )

            processed_count = sum(
                1 for r in results if r.get('status') == 'success')
            failed_count = sum(
                1 for r in results if r.get('status') == 'failed')
            skipped_count = sum(
                1 for r in results if r.get('status') == 'skipped')
            created_posts_count = sum(
                len(r.get('created_posts', [])) for r in results if r.get('status') == 'success'
            )

            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                'status': 'completed',
                'processed': processed_count,
                'created_posts': created_posts_count,
                'failed': failed_count,
                'skipped': skipped_count,
                'total_users': total,
                'duration_seconds': duration,
                'details': results,
            }

            return result
        except Exception as e:
            return {
                'status': 'error',
                'processed': 0,
                'total_users': total,
                'message': f'Error processing users: {str(e)}',
            }

    async def process_single_user(self, user_data: dict) -> Dict[str, Any]:
        """Process daily ideas generation for a single user"""
        user_id = user_data.get('id') or user_data.get('user_id')
        if not user_data:
            return {'status': 'failed', 'reason': 'no_user_data'}
        if not user_id:
            return {'status': 'failed', 'reason': 'no_user_id', 'user_data': user_data}

        return await self._process_user_daily_ideas(user_id)

    async def _process_user_daily_ideas(self, user_id: int) -> Dict[str, Any]:
        """Generate daily ideas to the user"""
        user = await sync_to_async(User.objects.get)(id=user_id)
        try:
            user_data = await self.user_validation_service.get_user_data(user_id)
            if not user_data:
                return {'status': 'failed', 'reason': 'user_not_found', 'user_id': user_id}

            validation_result = await self.user_validation_service.validate_user_eligibility(user_data)
            if validation_result['status'] != 'eligible':
                return {
                    'status': 'skipped',
                    'reason': validation_result['reason'],
                    'user_id': user_id
                }

            user_posts = []

            week_id = get_current_week()

            feed_base_post = await sync_to_async(Post.objects.get)(
                user=user,
                further_details=week_id)

            post_idea = await sync_to_async(lambda: feed_base_post.ideas.first())()

            post_text_feed = {
                'titulo': feed_base_post.name,
                'type': 'feed',
                'content': post_idea.content,
            }

            await sync_to_async(self.audit_service.log_daily_content_generation)(
                user=user,
                action='daily_content_generation_started',
                status='info',
            )

            content_result = await sync_to_async(self._generate_content_for_user)(user, post_text_feed)

            content_json = content_result.replace(
                'json', '', 1).strip('`').strip()
            content_loaded = json.loads(content_json)

            post_text_stories = content_loaded.get('post_text_stories')
            post_text_reels = content_loaded.get('post_text_reels')

            post_content_stories = f"""{post_text_stories.get('roteiro', '').strip()}"""
            post_content_reels = f"""{post_text_reels.get('roteiro', '').strip()}\n\n\n"""

            await sync_to_async(self._generate_image_for_feed_post)(
                user, post_idea, post_text_feed['content'])

            await self._save_text_to_db(user, post_text_stories, post_content_stories, user_posts, week_id, 'story')
            await self._save_text_to_db(user, post_text_reels, post_content_reels, user_posts, week_id, 'reels')

            await self._clear_user_error(user)

            return {'status': 'success', 'user_id': user_id, 'created_posts': []}
        except Exception as e:
            await self._store_user_error(user, str(e))
            await sync_to_async(self.audit_service.log_daily_content_generation)(
                user=user,
                action='daily_content_generation_failed',
                details={'error': str(e)}
            )
            return {
                'status': 'failed',
                'error': str(e),
                'user_id': user_id
            }

    @staticmethod
    async def _save_text_to_db(
            user: User,
            post_data: dict,
            post_content: str,
            user_posts: list,
            week_id: str,
            post_type: str) -> None:
        post = await sync_to_async(Post.objects.create)(
            user=user,
            name=post_data.get('titulo', 'Conteúdo Diário'),
            type=post_type,
            further_details=week_id,
            include_image=True if post_type == 'feed' else False,
            is_automatically_generated=True,
            is_active=False
        )

        post_idea = await sync_to_async(PostIdea.objects.create)(
            post=post,
            content=post_content,
            image_url='',
            image_description=''
        )

        user_posts.append({
            'post_id': post_idea.id,
            'post_idea_id': post_idea.id,
            'type': post.type,
            'title': post.name
        })

    def _generate_image_for_feed_post(self, user: User, post_idea: PostIdea, post_content: str) -> str:
        """AI service call to generate image for feed post."""
        try:
            user_logo = CreatorProfile.objects.filter(user=user).first().logo

            if user_logo and "data:image/" in user_logo and ";base64," in user_logo:
                user_logo = user_logo.split(",")[1]

            image_url = ''
            self.prompt_service.set_user(user)

            semantic_prompt = self.prompt_service.semantic_analysis_prompt(
                post_content)
            semantic_result = self.ai_service.generate_text(
                semantic_prompt, user)
            semantic_json = semantic_result.replace(
                'json', '', 1).strip('`').strip()
            semantic_loaded = json.loads(semantic_json)

            semantic_analysis = semantic_loaded.get(
                'analise_semantica', {})

            image_prompt = self.prompt_service.image_generation_prompt(
                semantic_analysis)

            image_result = self.ai_service.generate_image(image_prompt, user_logo, user, types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.9,
                response_modalities=[
                    "IMAGE",
                ],
                image_config=types.ImageConfig(
                    aspect_ratio="4:5",
                ),
            ))

            if not image_result:
                image_url = ''
            else:
                image_url = self.s3_service.upload_image(
                    user, image_result)

            post_idea.image_description = json.dumps(semantic_analysis)
            post_idea.image_url = image_url
            post_idea.save()

            return image_url
        except Exception as e:
            raise Exception(
                f"Failed to generate image for user {user.id}: {str(e)}")

    def _generate_content_for_user(self, user: User, post_text_feed: dict) -> str:
        """AI service call to generate daily ideas for a user."""
        try:
            self.prompt_service.set_user(user)

            prompt = self.prompt_service.build_campaign_prompts(
                post_text_feed)

            content_result = self.ai_service.generate_text(prompt, user, types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.9,
                response_modalities=[
                    "TEXT",
                ],
            ))

            return content_result
        except Exception as e:
            raise Exception(
                f"Failed to generate context for user {user.id}: {str(e)}")

    @staticmethod
    async def _store_user_error(user, error_message: str):
        """Store error message in user model for retry processing."""
        await sync_to_async(lambda: connection.cursor().execute(
            "UPDATE auth_user SET daily_generation_error = %s, daily_generation_error_date = %s WHERE id = %s",
            [error_message, timezone.now(), user.id]
        ))()

    @staticmethod
    async def _clear_user_error(user):
        """Clear error message from user model after successful generation."""
        await sync_to_async(lambda: connection.cursor().execute(
            "UPDATE auth_user SET daily_generation_error = NULL, daily_generation_error_date = NULL WHERE id = %s",
            [user.id]
        ))()
