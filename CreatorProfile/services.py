import base64
from typing import Dict, List, Optional, Tuple

from django.contrib.auth.models import User
from django.db import transaction

from .models import CreatorProfile


class CreatorProfileService:
    """Service class for CreatorProfile business logic."""

    @staticmethod
    def get_or_create_profile(user: User) -> CreatorProfile:
        """Get existing profile or create new one."""
        profile, created = CreatorProfile.objects.get_or_create(user=user)
        return profile

    @staticmethod
    def update_profile_data(user: User, data: Dict) -> CreatorProfile:
        """Update profile with provided data."""
        with transaction.atomic():
            profile = CreatorProfileService.get_or_create_profile(user)

            # Update only the fields that were provided
            for key, value in data.items():
                if hasattr(profile, key):
                    # Clean the value before setting
                    if isinstance(value, str):
                        value = value.strip() if value else None
                    setattr(profile, key, value)

            # Force save to trigger the custom save method
            profile.save()

        return profile

    @staticmethod
    def calculate_onboarding_status(profile: CreatorProfile) -> Dict:
        """Calculate onboarding completion status."""
        onboarding_fields = [
            'professional_name', 'profession', 'specialization',
            'linkedin_url', 'instagram_username', 'youtube_channel', 'tiktok_username',
            'primary_color', 'secondary_color', 'accent_color_1', 'accent_color_2', 'accent_color_3',
            'primary_font', 'secondary_font',
        ]

        filled_fields = sum(
            1 for field in onboarding_fields
            if getattr(profile, field, None) and str(getattr(profile, field)).strip()
        )

        # Ensure onboarding is only marked as completed if there are actual filled fields
        # and the profile wasn't manually marked as completed
        actual_onboarding_completed = filled_fields > 0 and profile.onboarding_completed

        return {
            'onboarding_completed': actual_onboarding_completed,
            'onboarding_skipped': profile.onboarding_skipped,
            'has_data': filled_fields > 0,
            'filled_fields_count': filled_fields,
            'total_fields_count': len(onboarding_fields),
        }

    @staticmethod
    def skip_onboarding(user: User) -> CreatorProfile:
        """Mark onboarding as skipped."""
        with transaction.atomic():
            profile = CreatorProfileService.get_or_create_profile(user)
            profile.onboarding_skipped = True
            profile.save()
        return profile

    @staticmethod
    def reset_profile(user: User) -> bool:
        """Reset user profile."""
        try:
            profile = CreatorProfile.objects.get(user=user)
            profile.delete()
            return True
        except CreatorProfile.DoesNotExist:
            return False


class UserProfileService:
    """Service class for User profile operations."""

    @staticmethod
    def update_user_profile(user: User, first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
        """Update user's basic profile information."""
        if first_name is not None:
            user.first_name = first_name.strip()
        if last_name is not None:
            user.last_name = last_name.strip()

        user.save()
        return user


class AvatarService:
    """Service class for avatar operations."""

    VALID_IMAGE_FORMATS = [
        b'\xff\xd8\xff',  # JPEG
        b'\x89PNG\r\n\x1a\n',  # PNG
        b'GIF87a',  # GIF
        b'GIF89a',  # GIF
    ]

    MAX_SIZE_BYTES = 1048576  # 1MB

    @staticmethod
    def validate_avatar_data(avatar_data: str) -> Tuple[bool, str]:
        """Validate avatar data format and size."""
        if not avatar_data:
            return False, "Avatar data is required"

        if not avatar_data.startswith('data:image/'):
            return False, "Invalid image format. Must be base64 encoded image."

        try:
            base64_data = avatar_data.split(',')[1]
            image_bytes = base64.b64decode(base64_data)
        except Exception:
            return False, "Invalid base64 encoding"

        if len(image_bytes) > AvatarService.MAX_SIZE_BYTES:
            return False, "Image size exceeds 1MB limit"

        image_header = image_bytes[:8]
        is_valid_format = any(image_header.startswith(fmt)
                              for fmt in AvatarService.VALID_IMAGE_FORMATS)

        if not is_valid_format:
            return False, "Invalid image format. Only JPEG, PNG, and GIF are supported."

        return True, ""

    @staticmethod
    def save_avatar(user: User, avatar_data: str) -> CreatorProfile:
        """Save avatar to user's profile."""
        with transaction.atomic():
            profile = CreatorProfileService.get_or_create_profile(user)
            profile.avatar = avatar_data
            profile.save()
        return profile


class SuggestionService:
    """Service class for providing suggestions."""

    @staticmethod
    def get_profession_suggestions() -> List[str]:
        """Get popular profession suggestions."""
        return [
            'Advogado', 'Coach', 'Consultor', 'Médico', 'Psicólogo',
            'Dentista', 'Contador', 'Arquiteto', 'Designer', 'Programador',
            'Professor', 'Fisioterapeuta', 'Nutricionista', 'Personal Trainer',
        ]

    @staticmethod
    def get_specialization_suggestions() -> List[str]:
        """Get popular specialization suggestions."""
        return [
            'Tributário', 'Trabalhista', 'Civil', 'Executivo', 'Empresarial',
            'Financeiro', 'Digital', 'Estratégico', 'Cardiologia', 'Ortopedia',
            'Psicologia Clínica', 'Psicologia Organizacional', 'Endodontia', 'Ortodontia',
            'Contabilidade Tributária', 'Contabilidade Societária', 'Arquitetura Residencial',
            'Arquitetura Comercial', 'Design Gráfico', 'Design de Produto',
            'Desenvolvimento Web', 'Desenvolvimento Mobile', 'Clínica Geral', 'Pediatria',
            'Educação Física', 'Nutrição Esportiva', 'Nutrição Clínica',
        ]

    @staticmethod
    def get_font_suggestions() -> List[str]:
        """Get popular font suggestions."""
        return [
            'Inter', 'Roboto', 'Open Sans', 'Poppins', 'Montserrat',
            'Lato', 'Source Sans Pro', 'Nunito', 'Ubuntu', 'Raleway',
            'Playfair Display', 'Merriweather', 'PT Sans', 'Noto Sans', 'Work Sans',
        ]

    @staticmethod
    def get_color_suggestions() -> List[str]:
        """Get popular color suggestions."""
        return [
            '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
            '#F97316', '#06B6D4', '#EC4899', '#84CC16', '#6366F1',
            '#F43F5E', '#14B8A6', '#FBBF24', '#A855F7', '#22C55E',
        ]

    @staticmethod
    def get_all_suggestions() -> Dict[str, List[str]]:
        """Get all suggestions."""
        return {
            'professions': SuggestionService.get_profession_suggestions(),
            'specializations': SuggestionService.get_specialization_suggestions(),
            'fonts': SuggestionService.get_font_suggestions(),
            'colors': SuggestionService.get_color_suggestions(),
        }
