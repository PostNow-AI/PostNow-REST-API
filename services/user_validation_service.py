
from asgiref.sync import sync_to_async
from CreatorProfile.models import CreatorProfile
from CreditSystem.services.credit_service import CreditService
from django.contrib.auth.models import User


class UserValidationService:
    def __init__(self):
        self.credit_service = CreditService()

    @sync_to_async
    def get_user_data(self, user_id: int) -> tuple[User, CreatorProfile] | None:
        """Fetch user data by user ID."""
        try:
            user = User.objects.select_related(
                'creator_profile').get(id=user_id)
            return user, user.creator_profile
        except (User.DoesNotExist, CreatorProfile.DoesNotExist):
            return None

    @sync_to_async
    def validate_user_eligibility(self, user: dict) -> dict:
        """Validate if the user is eligible for processing."""
        if not user:
            return {"status": "ineligible", "reason": "user_not_found"}

        if not user[1].step_1_completed:
            return {'status': 'ineligible', 'reason': 'incomplete_onboarding'}

        if not self.credit_service.validate_user_subscription(user[0]):
            return {"status": "ineligible", "reason": "no_active_subscription"}

        return {"status": "eligible", "user": user[0], "profile": user[1]}
