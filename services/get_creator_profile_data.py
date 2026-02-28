import logging
import random
from typing import Optional

from CreatorProfile.models import CreatorProfile, VisualStylePreference
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


def get_creator_profile_data(user: User, style_id: Optional[int] = None) -> dict:
    """
    Fetch and return the creator profile data for the current user.

    Args:
        user: The user to fetch profile data for.
        style_id: Optional specific visual style ID to use. If provided, uses this style
                  instead of randomly selecting from user's saved styles.
    """

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
        "visual_style": get_visual_style(profile, user, style_id),
        'color_palette': [] if not any([
            profile.color_1, profile.color_2,
            profile.color_3, profile.color_4, profile.color_5
        ]) else [
            profile.color_1, profile.color_2,
            profile.color_3, profile.color_4, profile.color_5
        ],
    }

    return profile_data


def get_visual_style(profile: CreatorProfile, user: User, style_id: Optional[int] = None) -> str:
    """
    Get visual style for content generation.

    If style_id is provided, uses that specific style.
    Otherwise, randomly selects from user's saved visual_style_ids.

    Args:
        profile: The user's creator profile.
        user: The user.
        style_id: Optional specific style ID to use.

    Returns:
        String with style name and description, or empty string if not found.
    """
    # If specific style_id is provided, use it
    if style_id is not None:
        try:
            visual_style = VisualStylePreference.objects.get(id=style_id)
            return f'{visual_style.name} - {visual_style.description}'
        except VisualStylePreference.DoesNotExist:
            logger.warning(
                f"VisualStylePreference with id {style_id} not found, falling back to random selection")
            # Fall through to random selection

    # Fallback: random selection from user's saved styles
    return get_random_visual_style(profile, user)


def get_random_visual_style(profile: CreatorProfile, user: User) -> str:
    """Randomly select and fetch one visual style from the user's visual_style_ids list."""
    if not profile.visual_style_ids or len(profile.visual_style_ids) == 0:
        return ""

    random_style_id = random.choice(profile.visual_style_ids)

    try:
        visual_style = VisualStylePreference.objects.get(
            id=random_style_id)
        return f'{visual_style.name} - {visual_style.description}'
    except VisualStylePreference.DoesNotExist:
        logger.warning(
            f"VisualStylePreference with id {random_style_id} not found for user {user.id if user else 'unknown'}")
        return ""
