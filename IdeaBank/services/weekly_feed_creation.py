import datetime
import json
import logging
from typing import Any, Dict

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.db import connection
from django.utils import timezone
from google.genai import types

from AuditSystem.services import AuditService
from ClientContext.models import ClientContext
from ClientContext.serializers import ClientContextSerializer
from IdeaBank.models import Post, PostIdea
from services.ai_prompt_service import AIPromptService
from services.ai_service import AiService
from services.semaphore_service import SemaphoreService
from services.user_validation_service import UserValidationService

logger = logging.getLogger(__name__)


class WeeklyFeedCreationService:
    def __init__(self):
        self.user_validation_service = UserValidationService()
        self.semaphore_service = SemaphoreService()
        self.ai_service = AiService()
        self.prompt_service = AIPromptService()
        self.audit_service = AuditService()

    @sync_to_async
    def _get_eligible_users(self, offset: int, limit: int) -> list[dict[str, Any]]:
        """Get a batch of users eligible for weekly context generation"""

        if limit is None:
            return list(
                User.objects.extra(
                    where=["weekly_feed_generation_error IS NULL"]
                ).filter(
                    usersubscription__status='active',
                    is_active=True
                ).distinct().values('id', 'email', 'username')[offset:]
            )

        return list(
            User.objects.extra(
                where=["weekly_feed_generation_error IS NULL"]
            ).filter(
                usersubscription__status='active',
                is_active=True
            ).distinct().values('id', 'email', 'username')[offset:offset + limit]
        )

    async def process_weekly_ideas_for_users(self, batch_number: int, batch_size: int) -> Dict[str, Any]:
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

        return await self._process_user_weekly_ideas(user_id)

    async def _process_user_weekly_ideas(self, user_id: int) -> Dict[str, Any]:
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
            await sync_to_async(self.audit_service.log_daily_content_generation)(
                user=user,
                action='daily_content_generation_started',
                status='info',
            )

            content_result = await sync_to_async(self._generate_content_for_user)(user)

            content_json = content_result.replace(
                'json', '', 1).strip('`').strip()
            content_loaded = json.loads(content_json)

            print(content_loaded)
            for post_text_feed in content_loaded:
                print(post_text_feed)
                post_content_feed = f"""{post_text_feed.get('legenda', '').strip()}\n\n\n{' '.join(post_text_feed.get('hashtags', []))}\n\n\n{post_text_feed.get('cta', '').strip()}
                               """

                print(post_content_feed)
                await self._save_text_to_db(user, post_text_feed, post_content_feed, user_posts)

            await self._clear_user_error(user)

            return {'status': 'success', 'user_id': user_id, 'created_posts': user_posts}
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
    async def _save_text_to_db(user: User, post_data: dict, post_content: str, user_posts: list) -> None:
        current_week = datetime.datetime.now().isocalendar()[1]
        week_id = str(post_data.get('id')) + '_week_' + str(current_week)
        post = await sync_to_async(Post.objects.create)(
            user=user,
            name=post_data.get('titulo', 'Conteúdo Diário'),
            type='feed',
            further_details=week_id,
            include_image=True,
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
            'type': 'feed',
            'title': post.name
        })

    def _generate_content_for_user(self, user: User) -> str:
        """AI service call to generate daily ideas for a user."""
        try:
            self.prompt_service.set_user(user)
            context = ClientContext.objects.filter(user=user).first()
            serializer = ClientContextSerializer(context)

            context_data = serializer.data if serializer else {}

            prompt = self.prompt_service.build_feed_prompts(
                context_data)

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
        print(user, error_message)
        await sync_to_async(lambda: connection.cursor().execute(
            "UPDATE auth_user SET weekly_feed_generation_error = %s WHERE id = %s",
            [error_message, user.id]
        ))()

    @staticmethod
    async def _clear_user_error(user):
        """Clear error message from user model after successful generation."""
        print('entrou aqui')
        await sync_to_async(lambda: connection.cursor().execute(
            "UPDATE auth_user SET weekly_feed_generation_error = NULL WHERE id = %s",
            [user.id]
        ))()
