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

from .post_ai_service import PostAIService

User = get_user_model()
logger = logging.getLogger(__name__)


class DailyContentService:
    def __init__(self):
        self.ai_service = PostAIService()
        self.credit_service = CreditService()
        self.max_concurrent_users = os.getenv('MAX_CONCURRENT_USERS', 50)

    async def process_all_users_async(self) -> Dict[str, Any]:
        """Processa geração de conteúdo para todos os usuários com limite de concorrência."""
        start_time = timezone.now()
        logger.info(
            "Iniciando processamento de conteúdo diário para todos os usuários"
        )

        try:
            eligible_users = await self._get_eligible_users()
            total_users = len(eligible_users)
            logger.info(
                f"Total de usuários a receberem conteúdo: {total_users}")

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

            logger.info(
                f"Processamento concluído: {processed_count} processados, {failed_count} falhas, {skipped_count} pulados em {duration:.2f} segundos"
            )
            return result
        except Exception as e:
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()

            logger.error(f"Erro ao processar usuários: {str(e)}")
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
                logger.error(
                    f"Erro ao processar usuário {users[i]['id']}: {str(result)}")
                processed_results.append({
                    'user_id': users[i]['id'],
                    'status': 'failed',
                    'error': str(result)
                })
            else:
                processed_results.append(result)

        return processed_results

    async def _process_single_user_async(self, user_id: int) -> Dict[str, Any]:
        """Processa geração de conteúdo para um único usuário."""
        try:
            mailjet = MailService()
            subject = "Seu conteúdo diário foi gerado!"
            user_data = await self._get_user_data(user_id)

            if not user_data:
                return {'status': 'failed', 'reason': 'user_not_found', 'user_id': user_id}

            user, creator_profile = user_data
            html_content = f"""<p>Olá {user.first_name},</p>
            <p>Seu conteúdo diário foi gerado com sucesso. Aqui estão os detalhes:</p>
            <ul>
            """

            validation_result = await self._validate_user_eligibility(user)
            logger.info(
                f"Validação de elegibilidade para usuário {user.id} - {user.username}: {validation_result['status']}")
            if validation_result['status'] != 'eligible':
                return {'user_id': user_id,
                        'status': 'skipped',
                        'reason': validation_result['reason']}

            all_content_results = []
            for post_type in ['feed', 'story', 'reels']:
                result = await self._generate_content_for_user(user, creator_profile, post_type)
                if result:
                    all_content_results.append(result)
                    html_content += f"<li><strong>Post ID:</strong> {result['post_id']}<br><strong>Conteúdo:</strong> {result['content']}</li>"
                    logger.info(
                        f"Conteúdo gerado para usuário {user.id} - {user.username}: Post ID {result['post_id']}")
                else:
                    logger.warning(
                        f"Nenhum conteúdo gerado para o usuário {user.id} - {user.username} para o tipo {post_type}")

            html_content += """
            </ul>
            <p>Obrigado por usar nosso serviço!</p>
            """

            print(html_content)
            mailjet.send_email(user.email, subject, html_content)

            return {'user_id': user_id, 'user': user.first_name, 'status': 'success', 'content': all_content_results}

        except Exception as e:
            logger.error(f"Erro ao processar usuário {user_id}: {str(e)}")
            return {
                'user_id': user_id,
                'status': 'failed',
                'error': str(e)
            }

    @sync_to_async
    def _get_eligible_users(self):
        """Get all users eligible for daily content generation"""
        return list(
            User.objects.filter(
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
    def _validate_user_eligibility(self, user) -> Dict[str, str]:
        """Check if user is eligible for content generation."""
        if not self.credit_service.validate_user_subscription(user):
            return {'status': 'ineligible', 'reason': 'no_active_subscription'}

        if not self.credit_service.has_sufficient_credits(user, required_amount=0.02):
            return {'status': 'ineligible', 'reason': 'insufficient_credits'}

        return {'status': 'eligible'}

    @sync_to_async
    def _generate_content_for_user(self, user, creator_profile, post_type) -> Dict[str, Any]:
        """Generate content for a single user."""
        try:
            post_data = {
                'name': f"Conteúdo diário para {user.username}",
                'objective': random.choice(PostObjective.choices),
                'type': post_type,
                'further_details': f"Conteúdo personalizado para {creator_profile.profession}, {creator_profile.specialization}",
                'include_image': False,
            }

            logger.info(
                f"Gerando conteúdo para usuário {user.id} - {user.username}"
            )
            with transaction.atomic():
                post = Post.objects.create(
                    user=user,
                    name=post_data['name'],
                    objective=post_data['objective'],
                    type=post_data['type'],
                    further_details=post_data['further_details'],
                    include_image=post_data['include_image']
                )

                generated_content = self.ai_service.generate_post_content(
                    user, post_data=post_data)
                post_idea = PostIdea.objects.create(
                    post=post,
                    content=generated_content['content']
                )

                return {
                    'post_id': post.id,
                    'post_idea_id': post_idea.id,
                    'content': generated_content['content'],
                    'generated_at': timezone.now().isoformat()
                }
        except Exception as e:
            logger.error(
                f"Erro ao gerar conteúdo para o usuário {user.id}: {str(e)}")
            return {'status': 'error', 'error': str(e)}
