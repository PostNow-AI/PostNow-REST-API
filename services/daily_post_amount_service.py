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
                creator_profile__step_1_completed=True).distinct()
            total_user_amount = total_users.count()
            expected_posts_amount = 3 * total_user_amount

            users_with_posts = []

            for user_obj in total_users:
                user_daily_story_reels_posts = Post.objects.filter(
                    user=user_obj,
                    created_at__date=today
                ).prefetch_related('ideas')
                user_daily_feed_post = Post.objects.filter(
                    user=user_obj,
                    type='feed',
                    further_details=user_daily_story_reels_posts[0].further_details,
                ).prefetch_related('ideas')
                serialized_posts = CompletePostWithIdeasSerializer(
                    user_daily_story_reels_posts, many=True).data
                serialized_feed_post = CompletePostWithIdeasSerializer(
                    user_daily_feed_post, many=True).data

                user_obj.daily_posts_count = user_daily_story_reels_posts.count() + user_daily_feed_post.count()
                actual_automatic_posts_amount += user_obj.daily_posts_count

                user = UserSerializer(user_obj).data
                user['posts'] = serialized_posts + serialized_feed_post
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
