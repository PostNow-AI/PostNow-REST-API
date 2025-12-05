from django.contrib.auth.models import User
from django.utils import timezone
from IdeaBank.models import Post
from IdeaBank.serializers import CompletePostWithIdeasSerializer, UserSerializer


class DailyPostAmountService:
    @staticmethod
    def get_daily_post_amounts(date: str = None) -> dict:
        try:
            today = timezone.now().date() if date is None else date

            actual_automatic_posts_amount = 0

            total_users = User.objects.filter(
                is_active=True,
                usersubscription__status='active',
                creator_profile__onboarding_completed=True).distinct()
            total_user_amount = total_users.count()
            expected_posts_amount = 3 * total_user_amount

            users_with_posts = []

            for user_obj in total_users:
                user_daily_posts = Post.objects.filter(
                    user=user_obj,
                    created_at__date=today
                ).prefetch_related('ideas')
                user_obj.daily_posts_count = user_daily_posts.count()
                serialized_posts = CompletePostWithIdeasSerializer(
                    user_daily_posts, many=True).data
                actual_automatic_posts_amount += user_obj.daily_posts_count
                user = UserSerializer(user_obj).data
                user['posts'] = serialized_posts
                users_with_posts.append(user)

            return {
                "date": str(today),
                "user_amount": total_user_amount,
                "automatic_expected_posts_amount": expected_posts_amount,
                "actual_automatic_posts_amount": actual_automatic_posts_amount,
                "users_with_posts": users_with_posts
            }
        except Exception as e:
            raise Exception(f"Error fetching daily post amounts: {e}")
