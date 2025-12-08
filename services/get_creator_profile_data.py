import logging
import random

from CreatorProfile.models import CreatorProfile, VisualStylePreference
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


def get_creator_profile_data(user: User) -> dict:
    """Fetch and return the creator profile data for the current user."""

    profile = CreatorProfile.objects.filter(user=user).first()
    if not profile:
        raise CreatorProfile.DoesNotExist
    profile_data = {
        "business_name": profile.business_name,
        "business_phone": profile.business_phone,
        "business_website": profile.business_website,
        "business_instagram_handle": profile.business_instagram_handle,
        "specialization": profile.specialization,
        "business_description": profile.business_description,
        "business_purpose": profile.business_purpose,
        "brand_personality": profile.brand_personality,
        "products_services": profile.products_services,
        "business_location": profile.business_location,
        "target_audience": profile.target_audience,
        "target_interests": profile.target_interests,
        "main_competitors": profile.main_competitors,
        "reference_profiles": profile.reference_profiles,
        "voice_tone": profile.voice_tone,
        "visual_style": get_random_visual_style(profile, user),
        'color_palette': [] if not any([
            profile.color_1, profile.color_2,
            profile.color_3, profile.color_4, profile.color_5
        ]) else [
            profile.color_1, profile.color_2,
            profile.color_3, profile.color_4, profile.color_5
        ],
        'desired_post_types': ['Nenhum'],
    }

    return profile_data


def get_random_visual_style(profile: CreatorProfile, user: User) -> dict:
    """Randomly select and fetch one visual style from the user's visual_style_ids list."""
    if not profile.visual_style_ids or len(profile.visual_style_ids) == 0:
        return {"name": None, "description": None}

    random_style_id = random.choice(profile.visual_style_ids)

    try:
        visual_style = VisualStylePreference.objects.get(
            id=random_style_id)
        return f'{visual_style.name} - {visual_style.description}'
    except VisualStylePreference.DoesNotExist:
        logger.warning(
            f"VisualStylePreference with id {random_style_id} not found for user {user.id if user else 'unknown'}")
        return {"name": None, "description": None}
