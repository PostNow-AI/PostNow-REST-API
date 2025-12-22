import logging
from collections import defaultdict

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model

from IdeaBank.models import Post
from IdeaBank.utils.current_week import get_current_week
from IdeaBank.utils.mail_templates.daily_content import daily_content_template
from services.mailjet_service import MailjetService

User = get_user_model()
logger = logging.getLogger(__name__)


class MailDailyIdeasService:
    def __init__(self):
        self.mailjet_service = MailjetService()

    @staticmethod
    async def fetch_users_daily_ideas() -> list:
        """Fetch users with daily ideas to be mailed."""
        week_id = get_current_week()

        return await sync_to_async(list)(
            Post.objects.filter(
                is_active=False,
                further_details=week_id
            ).select_related('user').values(
                'id', 'user__id', 'user__email', 'name', 'type', 'objective', 'created_at', 'ideas__content',
                'ideas__image_url'
            )
        )

    async def mail_daily_ideas(self):
        """Send one email per user with all their generated posts, then activate posts."""
        posts = await self.fetch_users_daily_ideas()
        if not posts:
            return {
                'status': 'completed',
                'total_users': 0,
                'processed': 0,
                'message': 'No posts to process',
            }

        user_posts = defaultdict(list)
        for post in posts:
            user_id = post['user__id']
            user_posts[user_id].append(post)

        processed = 0
        failed = 0

        for user_id, posts_list in user_posts.items():
            try:
                user = await sync_to_async(User.objects.get)(id=user_id)
                await self.send_email_to_user(user, posts_list)
                processed += 1
                post_ids = [p['id'] for p in posts_list]
                await sync_to_async(lambda: Post.objects.filter(id__in=post_ids).update(is_active=True))()
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

            user_name = user.first_name
            subject = "Seus Conteúdos Diários Foram Gerados!"
            feed_image = None
            feed_text = None
            reels_text = None
            story_text = None

            for post in posts:

                post_type = post['type'].lower()
                post_content = post.get('ideas__content', '')

                if post_type == 'feed':
                    feed_text = post_content
                    if post.get('ideas__image_url'):
                        feed_image = post['ideas__image_url']
                elif post_type == 'reels' or post_type == 'reel':
                    reels_text = post_content
                elif post_type == 'story':
                    story_text = post_content

            html_content = daily_content_template(
                user_name=user_name,
                feed_image=feed_image,
                feed_text=feed_text,
                reels_text=reels_text,
                story_text=story_text
            )

            await self.mailjet_service.send_email(
                user.email, subject, html_content, [])

            logger.info(
                f"E-mail enviado com sucesso para o usuário {user.id} - {user.username}")

        except Exception as e:
            logger.error(
                f"Erro ao enviar e-mail para o usuário {user.id}: {str(e)}")
            raise Exception(
                f"Failed to send email to user {user.id}: {str(e)}")
