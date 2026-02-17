"""Servico para geracao diaria de ideias de conteudo."""

import json
import logging
from typing import Any, Dict, Optional

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from google.genai import types

from AuditSystem.services import AuditService
from ClientContext.services.context_stats_service import ContextStatsService
from CreatorProfile.models import CreatorProfile
from IdeaBank.models import Post, PostIdea
from IdeaBank.services.daily_error_service import DailyErrorService
from IdeaBank.services.weekly_feed_creation import WeeklyFeedCreationService
from IdeaBank.utils.current_week import get_current_week
from services.ai_prompt_service import AIPromptService
from services.ai_service import AiService
from services.s3_sevice import S3Service
from services.semaphore_service import SemaphoreService
from services.user_validation_service import UserValidationService

logger = logging.getLogger(__name__)


class DailyIdeasService:
    """Service for generating daily content ideas for users.

    Supports dependency injection for testing and flexibility (DIP).
    """

    def __init__(
        self,
        user_validation_service: Optional[UserValidationService] = None,
        semaphore_service: Optional[SemaphoreService] = None,
        weekly_feed_creation_service: Optional[WeeklyFeedCreationService] = None,
        ai_service: Optional[AiService] = None,
        prompt_service: Optional[AIPromptService] = None,
        audit_service: Optional[AuditService] = None,
        s3_service: Optional[S3Service] = None,
        error_service: Optional[DailyErrorService] = None,
        stats_service: Optional[ContextStatsService] = None,
    ):
        self.user_validation_service = user_validation_service or UserValidationService()
        self.semaphore_service = semaphore_service or SemaphoreService()
        self.weekly_feed_creation_service = weekly_feed_creation_service or WeeklyFeedCreationService()
        self.ai_service = ai_service or AiService()
        self.prompt_service = prompt_service or AIPromptService()
        self.audit_service = audit_service or AuditService()
        self.s3_service = s3_service or S3Service()
        self.error_service = error_service or DailyErrorService()
        self.stats_service = stats_service or ContextStatsService()

    async def process_daily_ideas_for_users(self, batch_number: int, batch_size: int) -> Dict[str, Any]:
        """Process daily ideas generation for a batch of users."""
        start_time = timezone.now()

        offset = (batch_number - 1) * batch_size
        limit = batch_size if batch_size > 0 else None
        if batch_size == 0:
            offset = 0

        eligible_users = await self.error_service.get_users_without_errors(offset=offset, limit=limit)
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

            end_time = timezone.now()
            stats = self.stats_service.calculate_batch_results(results, start_time, end_time)

            # Adiciona contagem de posts criados (especifico para daily ideas)
            created_posts_count = sum(
                len(r.get('created_posts', [])) for r in results if r.get('status') == 'success'
            )

            result = self.stats_service.build_completion_result(stats, total, details=results)
            result['created_posts'] = created_posts_count

            return result

        except Exception as e:
            return {
                'status': 'error',
                'processed': 0,
                'total_users': total,
                'message': f'Error processing users: {str(e)}',
            }

    async def process_single_user(self, user_data: dict) -> Dict[str, Any]:
        """Process daily ideas generation for a single user."""
        user_id = user_data.get('id') or user_data.get('user_id')
        if not user_data:
            return {'status': 'failed', 'reason': 'no_user_data'}
        if not user_id:
            return {'status': 'failed', 'reason': 'no_user_id', 'user_data': user_data}

        return await self._process_user_daily_ideas(user_id)

    async def _process_user_daily_ideas(self, user_id: int) -> Dict[str, Any]:
        """Generate daily ideas to the user."""
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

            feed_base_post = await sync_to_async(Post.objects.filter(
                user=user,
                type='feed',
                further_details=week_id
            ).first)()

            if not feed_base_post:
                await self.weekly_feed_creation_service.process_user_weekly_ideas(user_id)
                feed_base_post = await sync_to_async(Post.objects.filter(
                    user=user,
                    type='feed',
                    further_details=week_id
                ).first)()

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

            await self.error_service.clear_error(user)

            return {'status': 'success', 'user_id': user_id, 'created_posts': []}
        except Exception as e:
            await self.error_service.store_error(user, str(e))
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
            name=post_data.get('titulo', 'Conteudo Diario'),
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
