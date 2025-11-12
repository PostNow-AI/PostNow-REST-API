import asyncio
import logging
import os
import random
from typing import Any, Dict, List

from asgiref.sync import sync_to_async
from CreatorProfile.models import CreatorProfile
from CreditSystem.services.credit_service import CreditService
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from IdeaBank.models import Post, PostIdea, PostObjective
from IdeaBank.services.mail_service import MailService
from IdeaBank.utils.mail_templates.daily_content import daily_content_template

from .post_ai_service import PostAIService

User = get_user_model()
logger = logging.getLogger(__name__)


class DailyContentService:
    def __init__(self):
        self.ai_service = PostAIService()
        self.credit_service = CreditService()
        self.max_concurrent_users = os.getenv('MAX_CONCURRENT_USERS', 50)

    async def mail_all_generated_content(self) -> Dict[str, Any]:
        """Send one email per user with all their generated posts, then activate posts."""
        posts = await self.fetch_users_automatic_posts()
        if not posts:
            return {
                'status': 'completed',
                'total_users': 0,
                'processed': 0,
                'message': 'No posts to process',
            }

        # Group posts by user
        from collections import defaultdict
        user_posts = defaultdict(list)
        for post in posts:
            user_id = post['user__id']
            user_posts[user_id].append(post)

        processed = 0
        failed = 0

        for user_id, posts_list in user_posts.items():
            try:
                # Fetch user instance
                user = await sync_to_async(User.objects.get)(id=user_id)
                await self.send_email_to_user(user, posts_list)
                processed += 1
                # Update posts to is_active=True
                post_ids = [p['id'] for p in posts_list]
                await sync_to_async(Post.objects.filter(id__in=post_ids).update)(is_active=True)
            except Exception as e:
                logger.error(f"Failed to process user {user_id}: {str(e)}")
                failed += 1

        if failed > 0:
            logger.warning(
                f"Failed to process {failed} users out of {len(user_posts)}")
            failed_users = await sync_to_async(list)(
                User.objects.filter(id__in=user_posts.keys()).values('email'))
            await self.send_fallback_email_to_admins(
                f"{failed} processos, de um total de {len(user_posts)} usuários, obtiveram falha ao enviar emails durante o envio de conteúdo diário. Emails de usuários: " +
                ", ".join(str(user['email']) for user in failed_users)
            )

        return {
            'status': 'completed',
            'total_users': len(user_posts),
            'processed': processed,
            'failed': failed,
        }

    async def send_email_to_user(self, user, posts):
        """Send email to a single user with their generated posts."""
        try:
            mailjet = MailService()
            subject = "Seu conteúdo diário foi gerado!"

            # Extract user name
            user_name = user.first_name

            # Initialize variables for different post types
            feed_image = None
            feed_text = None
            reels_text = None
            story_text = None

            # Extract content by post type
            for post in posts:
                post_type = post['type'].lower()
                post_content = post.get('ideas__content', '')

                if post_type == 'feed':
                    feed_text = post_content
                    if post.get('ideas__image_url'):
                        feed_image = post['ideas__image_url']
                elif post_type == 'reels':
                    reels_text = post_content
                elif post_type == 'story':
                    story_text = post_content

            # Prepare attachments for inline images
            attachments = []

            # Add feed image attachment if available
            if feed_image:
                if feed_image.startswith('data:image/'):
                    # Handle base64 images
                    content_type = feed_image.split(
                        ';')[0].replace('data:', '')
                    extension = 'png' if 'png' in content_type else 'jpg'
                    attachments.append({
                        'url': feed_image,
                        'filename': f'feed_image.{extension}',
                        'content_type': content_type,
                        'content_id': 'feed_image'
                    })
                else:
                    # Handle regular URL images
                    attachments.append({
                        'url': feed_image,
                        'filename': 'feed_image.jpg',
                        'content_type': 'image/jpeg',
                        'content_id': 'feed_image'
                    })

            # Generate HTML content using the template
            html_content = daily_content_template(
                user_name=user_name,
                feed_image=feed_image,
                feed_text=feed_text,
                reels_text=reels_text,
                story_text=story_text
            )

            # Send email with attachments for inline images
            status_code, response = mailjet.send_email(
                user.email, subject, html_content, attachments)

            if status_code and status_code == 200:
                logger.info(
                    f"E-mail enviado com sucesso para o usuário {user.id} - {user.username} com {len(attachments)} imagens anexadas")
            else:
                logger.error(
                    f"Falha ao enviar e-mail para o usuário {user.id}: Status {status_code}, Response: {response}")

        except Exception as e:
            logger.error(
                f"Erro ao enviar e-mail para o usuário {user.id}: {str(e)}")

    async def send_fallback_email_to_admins(self, error_message: str):
        """Send fallback email to admins in case of critical failure."""
        try:
            mailjet = MailService()
            subject = "Falha na Geração de Conteúdo Diário"
            admin_emails = os.getenv(
                'ADMIN_EMAILS', '').split(',')
            html_content = f"""
            <h1>Falha na Geração de Conteúdo Diário</h1>
            <p>Ocorreu um erro durante o processo de geração de conteúdo diário:</p>
            <pre>{error_message or 'Erro interno de servidor'}</pre>
            """
            for admin_email in admin_emails:
                mailjet.send_email(
                    admin_email.strip(), subject, html_content)

        except Exception as e:
            logger.error(
                f"Erro ao enviar e-mail de fallback para administradores: {str(e)}")

    @sync_to_async
    def _send_fallback_email_sync(self, error_message: str):
        """Synchronous wrapper for sending fallback emails to admins."""
        import asyncio
        try:
            # Create a new event loop if one doesn't exist
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, we need to handle this differently
                    # For now, just log the error without sending email
                    logger.warning(f"Could not send admin email due to running event loop: {error_message[:100]}...")
                    return
            except RuntimeError:
                # No event loop, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Run the async email sending
            loop.run_until_complete(self.send_fallback_email_to_admins(error_message))
        except Exception as e:
            logger.error(f"Failed to send admin email: {str(e)}")

    async def fetch_users_automatic_posts(self) -> List[Dict[str, Any]]:
        """Recupera todos os posts automáticos gerados para usuários."""
        return await sync_to_async(list)(
            Post.objects.filter(
                is_active=False
            ).select_related('user').values(
                'id', 'user__id', 'user__email', 'name', 'type', 'objective', 'created_at', 'ideas__content', 'ideas__image_url'
            )
        )

    async def process_all_users_async(self) -> Dict[str, Any]:
        """Processa geração de conteúdo para todos os usuários com limite de concorrência."""
        start_time = timezone.now()

        try:
            eligible_users = await self._get_eligible_users()
            total_users = len(eligible_users)
            if total_users == 0:
                return {
                    'status': 'completed',
                    'total_users': 0,
                    'processed': 0,
                    'message': 'No eligible users found',
                }

            results = await self._process_users_concurrently(eligible_users)

            processed_count = sum(
                1 for r in results if r.get('status') == 'success')
            failed_count = sum(
                1 for r in results if r.get('status') == 'failed')
            skipped_count = sum(
                1 for r in results if r.get('status') == 'skipped')

            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                'status': 'completed',
                'total_users': total_users,
                'processed': processed_count,
                'failed': failed_count,
                'skipped': skipped_count,
                'duration_seconds': duration,
                'details': results,
            }

            return result
        except Exception as e:
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()

            return {
                'status': 'error',
                'error': str(e),
                'processed': 0,
                'message': 'Error processing users',
                'duration_seconds': duration,
            }

    async def _process_users_concurrently(self, users: List[Dict]) -> List[Dict[str, Any]]:
        """Processa usuários com limite de concorrência."""
        semaphore = asyncio.Semaphore(int(self.max_concurrent_users))

        async def process_with_semaphore(user_data: Dict):
            async with semaphore:
                return await self._process_single_user_async(user_data['id'])

        tasks = [process_with_semaphore(user) for user in users]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'user_id': users[i]['id'],
                    'user': users[i]['first_name'],
                    'status': 'failed',
                    'error': str(result)
                })

            else:
                processed_results.append(result)

        return processed_results

    async def _process_single_user_async(self, user_id: int) -> Dict[str, Any]:
        """Processa geração de conteúdo para um único usuário."""
        try:
            user_data = await self._get_user_data(user_id)
            if not user_data:
                return {'status': 'failed', 'reason': 'user_not_found', 'user_id': user_id}

            user, creator_profile = user_data

            validation_result = await self._validate_user_eligibility(user, user_data)
            if validation_result['status'] != 'eligible':
                return {'user_id': user_id,
                        'status': 'skipped',
                        'reason': validation_result['reason']}

            # Generate campaign content (creates feed, reels, and story posts)
            post_objective = random.choice(PostObjective.choices)
            result = await self._generate_content_for_user(user, creator_profile, 'campaign', post_objective)

            if result and result.get('status') != 'error':
                # Success - clear any previous error
                await self._clear_user_error(user)

                # Handle campaign mode result
                if result.get('campaign_mode', False):
                    return {
                        'user_id': user_id,
                        'user': user.first_name,
                        'status': 'success',
                        'campaign_mode': True
                    }
                else:
                    # Regular single post mode
                    return {
                        'user_id': user_id,
                        'user': user.first_name,
                        'status': 'success',
                    }
            else:
                error_message = result.get(
                    'error', 'content_generation_failed') if result else 'no_content_generated'
                # Store error in user profile
                await self._store_user_error(user, error_message)

                return {
                    'user_id': user_id,
                    'status': 'failed',
                    'reason': error_message
                }

        except Exception as e:
            error_message = str(e)
            # Store error in user profile
            user_data = await self._get_user_data(user_id)
            if user_data:
                user, _ = user_data
                await self._store_user_error(user, error_message)

            return {
                'user_id': user_id,
                'status': 'failed',
                'error': error_message
            }

    @sync_to_async
    def _get_eligible_users(self):
        """Get all users eligible for daily content generation (excluding those with errors)"""
        return list(
            User.objects.extra(
                where=["daily_generation_error IS NULL"]
            ).filter(
                usersubscription__status='active',
                is_active=True
            ).distinct().values('id', 'email', 'username')
        )

    @sync_to_async
    def _get_user_data(self, user_id: int):
        """Fetch user data needed for content generation."""
        try:
            user = User.objects.select_related(
                'creator_profile').get(id=user_id)
            return user, user.creator_profile
        except (User.DoesNotExist, CreatorProfile.DoesNotExist):
            return None

    @sync_to_async
    def _validate_user_eligibility(self, user, user_data) -> Dict[str, str]:
        """Check if user is eligible for content generation."""
        if not self.credit_service.validate_user_subscription(user):
            return {'status': 'ineligible', 'reason': 'no_active_subscription'}

        if not self.credit_service.has_sufficient_credits(user, required_amount=0.02):
            return {'status': 'ineligible', 'reason': 'insufficient_credits'}

        if not user_data[1].onboarding_completed:
            return {'status': 'ineligible', 'reason': 'incomplete_onboarding'}

        return {'status': 'eligible'}

    @sync_to_async
    def _generate_content_for_user(self, user, creator_profile, post_type, post_objective) -> Dict[str, Any]:
        """Generate content for a single user."""
        try:
            post_data = {
                'name': f"Conteúdo diário para {user.username}",
                'objective': post_objective,
                'type': post_type,
                'further_details': f"Conteúdo personalizado para {creator_profile.profession}, {creator_profile.specialization}",
                'include_image': False,
            }

            with transaction.atomic():
                # Add campaign-specific data to post_data
                post_data.update({
                    'is_automatically_generated': True,
                    'is_active': False
                })

                generated_content = self.ai_service.generate_post_content(
                    user, post_data=post_data)

                # Handle campaign mode (creates multiple posts) vs regular mode
                if generated_content.get('campaign_mode', False):
                    # Campaign mode - posts were already created by PostAIService
                    return {
                        'posts': generated_content['posts'],
                        'campaign_mode': True,
                        'generated_at': timezone.now().isoformat()
                    }
                else:
                    # Regular mode - create Post and PostIdea manually
                    post = Post.objects.create(
                        user=user,
                        name=post_data['name'],
                        objective=post_data['objective'],
                        type=post_data['type'],
                        further_details=post_data['further_details'],
                        include_image=post_data['include_image'],
                        is_automatically_generated=True,
                        is_active=False
                    )

                    post_idea = PostIdea.objects.create(
                        post=post,
                        content=generated_content['content'],
                        image_url=generated_content.get('image_url', '')
                    )

                    result = {
                        'post_id': post.id,
                        'post_idea_id': post_idea.id,
                        'generated_at': timezone.now().isoformat()
                    }

                    return result
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    async def process_users_batch_async(self, batch_number: int, batch_size: int) -> Dict[str, Any]:
        """Process a specific batch of users for daily content generation."""
        start_time = timezone.now()

        try:
            # Calculate offset based on batch number
            offset = (batch_number - 1) * batch_size

            eligible_users = await self._get_eligible_users_batch(offset, batch_size)
            total_users = len(eligible_users)

            if total_users == 0:
                return {
                    'status': 'completed',
                    'batch': batch_number,
                    'total_users': 0,
                    'processed': 0,
                    'message': 'No users in this batch',
                }

            results = await self._process_users_concurrently(eligible_users)

            processed_count = sum(
                1 for r in results if r.get('status') == 'success')
            failed_count = sum(
                1 for r in results if r.get('status') == 'failed')
            skipped_count = sum(
                1 for r in results if r.get('status') == 'skipped')

            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                'status': 'completed',
                'batch': batch_number,
                'total_users': total_users,
                'processed': processed_count,
                'failed': failed_count,
                'skipped': skipped_count,
                'duration_seconds': duration,
                'details': results,
            }

            return result

        except Exception as e:
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()

            return {
                'status': 'error',
                'batch': batch_number,
                'error': str(e),
                'duration_seconds': duration,
            }

    @sync_to_async
    def _get_eligible_users_batch(self, offset: int, limit: int):
        """Get a batch of users eligible for daily content generation (excluding those with errors)"""
        return list(
            User.objects.extra(
                where=["daily_generation_error IS NULL"]
            ).filter(
                usersubscription__status='active',
                is_active=True
            ).distinct().values('id', 'email', 'username')[offset:offset + limit]
        )

    @sync_to_async
    def _store_user_error(self, user, error_message: str):
        """Store error message in user model for retry processing."""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE auth_user SET daily_generation_error = %s, daily_generation_error_date = %s WHERE id = %s",
                    [error_message, timezone.now(), user.id]
                )
            self._send_fallback_email_sync(
                f"Usuário {user.first_name} ({user.email}) falhou ao gerar conteúdo durante o envio de conteúdo diário. Motivo: {error_message}"
            )
            logger.info(
                f"Stored error for user {user.id}: {error_message[:100]}...")
        except Exception as e:
            logger.error(f"Failed to store error for user {user.id}: {str(e)}")

    @sync_to_async
    def _clear_user_error(self, user):
        """Clear error message from user model after successful generation."""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE auth_user SET daily_generation_error = NULL, daily_generation_error_date = NULL WHERE id = %s",
                    [user.id]
                )
            logger.info(f"Cleared error for user {user.id}")
        except Exception as e:
            logger.error(f"Failed to clear error for user {user.id}: {str(e)}")

    @sync_to_async
    def _get_users_with_errors(self):
        """Get all users who have daily generation errors."""
        return list(
            User.objects.extra(
                where=["daily_generation_error IS NOT NULL"]
            ).filter(
                usersubscription__status='active',
                is_active=True
            ).distinct().values('id', 'email', 'username', 'first_name')
        )

    async def retry_failed_users_async(self) -> Dict[str, Any]:
        """Retry daily content generation for users who had errors."""
        start_time = timezone.now()

        try:
            failed_users = await self._get_users_with_errors()
            total_users = len(failed_users)

            if total_users == 0:
                return {
                    'status': 'completed',
                    'total_users': 0,
                    'processed': 0,
                    'message': 'No users with errors found',
                }

            logger.info(
                f"Starting retry process for {total_users} users with errors")

            results = await self._process_users_concurrently(failed_users)

            processed_count = sum(
                1 for r in results if r.get('status') == 'success')
            failed_count = sum(
                1 for r in results if r.get('status') == 'failed')
            skipped_count = sum(
                1 for r in results if r.get('status') == 'skipped')

            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                'status': 'completed',
                'total_users': total_users,
                'processed': processed_count,
                'failed': failed_count,
                'skipped': skipped_count,
                'duration_seconds': duration,
                'details': results,
            }

            logger.info(
                f"Retry completed: {processed_count} successful, {failed_count} failed, {skipped_count} skipped")
            return result

        except Exception as e:
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()

            logger.error(f"Error in retry process: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'processed': 0,
                'message': 'Error processing retry users',
                'duration_seconds': duration,
            }
