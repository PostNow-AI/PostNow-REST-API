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
            
            # Collect images for attachment and generate content IDs
            attachments = []
            image_mappings = {}  # Map post_id to content_id for inline images
            
            logger.info(f"Processing {len(posts)} posts for user {user.id}")
            
            for post in posts:
                logger.info(f"Post {post['id']}: type={post['type']}, has_image={bool(post.get('ideas__image_url'))}")
                if post['type'].lower() == 'feed' and post.get('ideas__image_url'):
                    image_url = post['ideas__image_url']
                    logger.info(f"Adding image attachment for post {post['id']}: {image_url}")
                    
                    # Generate unique content ID for this image
                    content_id = f"image_post_{post['id']}"
                    image_mappings[post['id']] = content_id
                    
                    # Determine content type and extension from image URL
                    if image_url.startswith('data:image/'):
                        # Extract content type from data URL
                        content_type = image_url.split(';')[0].replace('data:', '')
                        extension = 'png' if 'png' in content_type else 'jpg'
                    else:
                        # Default for regular URLs
                        content_type = 'image/jpeg'
                        extension = 'jpg'
                    
                    # Add to attachments list
                    attachments.append({
                        'url': image_url,
                        'filename': f"post_image_{post['id']}.{extension}",
                        'content_type': content_type
                    })
            
            logger.info(f"Total attachments to process: {len(attachments)}")
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Seu Conteúdo Diário - PostNow</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #f8f9fa;
                    }}
                    .container {{
                        background-color: white;
                        border-radius: 12px;
                        padding: 30px;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                        padding-bottom: 20px;
                        border-bottom: 2px solid #e9ecef;
                    }}
                    .header h1 {{
                        color: #2c3e50;
                        font-size: 28px;
                        margin: 0;
                        font-weight: 600;
                    }}
                    .greeting {{
                        font-size: 18px;
                        color: #495057;
                        margin-bottom: 20px;
                    }}
                    .post-item {{
                        margin-bottom: 30px;
                        border: 1px solid #e0e0e0;
                        border-radius: 12px;
                        padding: 25px;
                        background-color: #f8f9fa;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    }}
                    .post-header {{
                        font-size: 20px;
                        font-weight: 600;
                        color: #2c3e50;
                        margin-bottom: 15px;
                        display: flex;
                        align-items: center;
                        gap: 10px;
                    }}
                    .post-objective {{
                        font-size: 14px;
                        color: #6c757d;
                        margin-bottom: 15px;
                        font-style: italic;
                    }}
                    .post-content {{
                        margin: 15px 0;
                        padding: 20px;
                        background-color: white;
                        border-left: 4px solid #007bff;
                        border-radius: 8px;
                        font-size: 16px;
                        line-height: 1.7;
                    }}
                    .post-image {{
                        margin: 20px 0;
                        text-align: center;
                        background-color: white;
                        padding: 20px;
                        border-radius: 8px;
                    }}
                    .post-image h4 {{
                        margin-top: 0;
                        margin-bottom: 15px;
                        color: #2c3e50;
                        font-size: 16px;
                    }}
                    .post-image img {{
                        max-width: 100%;
                        max-height: 400px;
                        height: auto;
                        border-radius: 8px;
                        border: 2px solid #e9ecef;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                        display: block;
                        margin: 0 auto;
                    }}
                    .no-image {{
                        padding: 15px;
                        background-color: #f1f3f4;
                        border-radius: 8px;
                        color: #6c757d;
                        font-style: italic;
                        text-align: center;
                    }}
                    .footer {{
                        background-color: #f8f9fa;
                        padding: 25px;
                        text-align: center;
                        border-top: 2px solid #e9ecef;
                        margin-top: 30px;
                        border-radius: 8px;
                    }}
                    .footer p {{
                        margin: 10px 0;
                        color: #6c757d;
                    }}
                    @media (max-width: 600px) {{
                        body {{ padding: 10px; }}
                        .container {{ padding: 20px; }}
                        .header h1 {{ font-size: 24px; }}
                        .post-header {{ font-size: 18px; }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>� PostNow</h1>
                    </div>
                    
                    <div class="greeting">
                        Olá <strong>{user.first_name}</strong>! 👋
                    </div>
                    
                    <p>Seu conteúdo diário foi gerado com sucesso! Aqui estão os posts criados para você:</p>
            """

            for post in posts:
                # Get post type emoji
                type_emoji = {
                    'feed': '📝',
                    'reels': '🎬',
                    'story': '📱'
                }.get(post['type'].lower(), '📄')

                html_content += f"""
                    <div class="post-item">
                        <div class="post-header">
                            <span>{type_emoji}</span>
                            <span>{post['type'].title()} - Post #{post['id']}</span>
                        </div>
                        <div class="post-objective">
                            <strong>Objetivo:</strong> {post.get('objective', 'Não especificado')}
                        </div>
                        
                        <div class="post-content">
                            {post['ideas__content']}
                        </div>
                """

                # Add embedded image for feed posts only
                if post['type'].lower() == 'feed' and post.get('ideas__image_url'):
                    content_id = image_mappings.get(post['id'])
                    if content_id:
                        html_content += f"""
                        <div class="post-image">
                            <h4>🖼️ Imagem Gerada:</h4>
                            <img src="cid:{content_id}" 
                                 alt="Imagem do post {post['id']}" 
                                 style="max-width: 100%; height: auto;">
                        </div>
                        """
                elif post['type'].lower() == 'feed':
                    html_content += """
                        <div class="no-image">
                            📷 Imagem não foi gerada para este post
                        </div>
                    """

                html_content += "</div>"

            html_content += """
                    <div class="footer">
                        <p>🚀 <strong>Obrigado por usar PostNow!</strong></p>
                        <p><small>Este é um e-mail automático. Para dúvidas, entre em contato conosco.</small></p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Send email with attachments
            status_code, response = mailjet.send_email(user.email, subject, html_content, attachments if attachments else None)
            
            if status_code and status_code == 200:
                logger.info(f"E-mail enviado com sucesso para o usuário {user.id} - {user.username} com {len(attachments)} imagens anexadas")
            else:
                logger.error(f"Falha ao enviar e-mail para o usuário {user.id}: Status {status_code}, Response: {response}")
                # Try sending without attachments as fallback
                if attachments:
                    logger.info(f"Tentando reenviar e-mail sem anexos para o usuário {user.id}")
                    fallback_html = html_content.replace('src="cid:', 'src="#broken-image" data-original-cid="')
                    fallback_status, fallback_response = mailjet.send_email(user.email, subject, fallback_html, None)
                    if fallback_status == 200:
                        logger.info(f"E-mail de fallback enviado com sucesso para o usuário {user.id}")
                    else:
                        logger.error(f"Falha no envio de fallback para o usuário {user.id}: {fallback_response}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail para o usuário {user.id}: {str(e)}")

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
            user_data = await self._get_user_data(user_id)

            if not user_data:
                return {'status': 'failed', 'reason': 'user_not_found', 'user_id': user_id}

            user, creator_profile = user_data

            validation_result = await self._validate_user_eligibility(user)
            logger.info(
                f"Validação de elegibilidade para usuário {user.id} - {user.username}: {validation_result['status']}")
            if validation_result['status'] != 'eligible':
                return {'user_id': user_id,
                        'status': 'skipped',
                        'reason': validation_result['reason']}

            # Generate campaign content (creates feed, reels, and story posts)
            post_objective = random.choice(PostObjective.choices)
            result = await self._generate_content_for_user(user, creator_profile, 'campaign', post_objective)

            if result:
                # Handle campaign mode result
                if result.get('campaign_mode', False):
                    posts_created = result.get('posts', [])
                    logger.info(
                        f"Campanha gerada para usuário {user.id} - {user.username}: {len(posts_created)} posts criados")
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
                logger.warning(
                    f"Nenhum conteúdo gerado para o usuário {user.id} - {user.username}")
                return {
                    'user_id': user_id,
                    'status': 'failed',
                    'reason': 'no_content_generated'
                }

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

            logger.info(
                f"Gerando conteúdo para usuário {user.id} - {user.username}"
            )
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
            logger.error(
                f"Erro ao gerar conteúdo para o usuário {user.id}: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    async def process_users_batch_async(self, batch_number: int, batch_size: int) -> Dict[str, Any]:
        """Process a specific batch of users for daily content generation."""
        start_time = timezone.now()
        logger.info(f"Processing batch {batch_number} with size {batch_size}")

        try:
            # Calculate offset based on batch number
            offset = (batch_number - 1) * batch_size

            eligible_users = await self._get_eligible_users_batch(offset, batch_size)
            total_users = len(eligible_users)

            logger.info(
                f"Batch {batch_number}: Processing {total_users} users")

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

            logger.info(
                f"Batch {batch_number} completed: {processed_count} processed in {duration:.2f} seconds")
            return result

        except Exception as e:
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()

            logger.error(f"Error processing batch {batch_number}: {str(e)}")
            return {
                'status': 'error',
                'batch': batch_number,
                'error': str(e),
                'duration_seconds': duration,
            }

    @sync_to_async
    def _get_eligible_users_batch(self, offset: int, limit: int):
        """Get a batch of users eligible for daily content generation"""
        return list(
            User.objects.filter(
                usersubscription__status='active',
                is_active=True,
                email='msallesblanco@gmail.com'
            ).distinct().values('id', 'email', 'username')[offset:offset + limit]
        )
