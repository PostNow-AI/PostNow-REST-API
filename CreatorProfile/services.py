import logging
from typing import Dict, List, Optional

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from .models import CreatorProfile, OnboardingTempData, OnboardingStepTracking

logger = logging.getLogger(__name__)


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
                    # Special handling for JSONField arrays
                    if key == 'visual_style_ids':
                        # For JSONField, we can directly set the list of IDs
                        setattr(profile, key, value if value else [])
                    else:
                        # Clean the value before setting
                        if isinstance(value, str):
                            value = value.strip() if value else None
                        setattr(profile, key, value)

            # Force save to trigger the custom save method
            profile.save()

        return profile

    @staticmethod
    def reset_profile(user: User) -> bool:
        """Reset user profile."""
        try:
            CreatorProfile.objects.filter(user=user).update(
                step_1_completed=False,
                step_2_completed=False,
                onboarding_completed=False,
            )

            return True
        except CreatorProfile.DoesNotExist:
            return False

    @staticmethod
    def complete_profile(user: User) -> bool:
        """Complete user profile onboarding."""
        try:
            CreatorProfile.objects.filter(user=user).update(
                step_1_completed=True,
                step_2_completed=True,
                onboarding_completed=True,
            )

            return True
        except CreatorProfile.DoesNotExist:
            return False


class SuggestionService:
    """Service class for providing suggestions."""

    @staticmethod
    def get_profession_suggestions() -> List[str]:
        """Get popular profession suggestions."""
        return [
            'Advogado', 'Coach', 'Consultor', 'Médico', 'Psicólogo',
            'Dentista', 'Contador', 'Arquiteto', 'Designer', 'Programador',
            'Professor', 'Fisioterapeuta', 'Nutricionista', 'Personal Trainer',
            'Enfermeiro', 'Veterinário', 'Engenheiro', 'Administrador',
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
            'Marketing Digital', 'Gestão de Pessoas', 'Vendas'
        ]

    @staticmethod
    def get_voice_tone_suggestions() -> List[str]:
        """Get popular voice tone suggestions."""
        return [
            'Profissional', 'Descontraído', 'Amigável', 'Autoritário',
            'Inspirador', 'Educativo', 'Conversacional', 'Técnico',
            'Divertido', 'Sério', 'Caloroso', 'Direto'
        ]

    @staticmethod
    def get_business_city_suggestions() -> List[str]:
        """Get popular business city suggestions."""
        return [
            'Remoto', 'São Paulo', 'Rio de Janeiro', 'Belo Horizonte',
            'Brasília', 'Salvador', 'Fortaleza', 'Curitiba', 'Recife',
            'Porto Alegre', 'Goiânia', 'Belém', 'Manaus', 'Florianópolis'
        ]

    @staticmethod
    def get_target_gender_suggestions() -> List[str]:
        """Get target gender suggestions."""
        return [
            'Masculino', 'Feminino', 'Todos', 'Não-binário', 'Outro'
        ]

    @staticmethod
    def get_target_age_range_suggestions() -> List[str]:
        """Get target age range suggestions."""
        return [
            '18-24 anos', '25-34 anos', '35-44 anos', '45-54 anos',
            '55-64 anos', '65+ anos', 'Todas as idades'
        ]

    @staticmethod
    def get_target_location_suggestions() -> List[str]:
        """Get target location suggestions."""
        return [
            'Nacional', 'São Paulo', 'Rio de Janeiro', 'Belo Horizonte',
            'Brasília', 'Salvador', 'Fortaleza', 'Curitiba', 'Recife',
            'Porto Alegre', 'Goiânia', 'Belém', 'Manaus', 'Florianópolis',
            'Região Sudeste', 'Região Sul', 'Região Nordeste', 'Região Norte', 'Região Centro-Oeste'
        ]

    @staticmethod
    def get_all_suggestions() -> Dict[str, List[str]]:
        """Get all suggestions."""
        return {
            'professions': SuggestionService.get_profession_suggestions(),
            'specializations': SuggestionService.get_specialization_suggestions(),
            'voice_tones': SuggestionService.get_voice_tone_suggestions(),
            'business_cities': SuggestionService.get_business_city_suggestions(),
            'target_genders': SuggestionService.get_target_gender_suggestions(),
            'target_age_ranges': SuggestionService.get_target_age_range_suggestions(),
            'target_locations': SuggestionService.get_target_location_suggestions(),
        }


class OnboardingDataService:
    """Service for handling temporary onboarding data and linking to users after signup."""

    # Fields that belong to Step 1 (Business)
    BUSINESS_FIELDS = [
        'business_name', 'business_phone', 'business_website',
        'business_instagram_handle', 'specialization', 'business_description',
        'business_purpose', 'brand_personality', 'products_services',
        'business_location', 'target_audience', 'target_interests',
        'main_competitors', 'reference_profiles'
    ]

    # Fields that belong to Step 2 (Branding)
    BRANDING_FIELDS = [
        'logo', 'voice_tone', 'color_1', 'color_2', 'color_3',
        'color_4', 'color_5', 'visual_style_ids'
    ]

    @classmethod
    def save_temp_data(cls, session_id: str, data: Dict) -> OnboardingTempData:
        """
        Save or update temporary onboarding data for a session.

        Args:
            session_id: Unique session identifier
            data: Dictionary with onboarding data

        Returns:
            OnboardingTempData instance
        """
        # Separate data into business and branding
        business_data = {k: v for k, v in data.items() if k in cls.BUSINESS_FIELDS}
        branding_data = {k: v for k, v in data.items() if k in cls.BRANDING_FIELDS}

        temp_data, created = OnboardingTempData.objects.get_or_create(
            session_id=session_id,
            defaults={
                'business_data': business_data,
                'branding_data': branding_data,
            }
        )

        if not created:
            # Merge with existing data
            if business_data:
                temp_data.business_data.update(business_data)
            if branding_data:
                temp_data.branding_data.update(branding_data)
            temp_data.save()

        logger.info(f"Saved temp onboarding data for session {session_id}")
        return temp_data

    @classmethod
    def get_temp_data(cls, session_id: str) -> Optional[OnboardingTempData]:
        """Get temporary data for a session."""
        try:
            return OnboardingTempData.objects.get(
                session_id=session_id,
                expires_at__gt=timezone.now()
            )
        except OnboardingTempData.DoesNotExist:
            return None

    @classmethod
    @transaction.atomic
    def link_data_to_user(cls, user: User, session_id: str) -> Optional[CreatorProfile]:
        """
        Link temporary onboarding data to a newly registered user.

        This method:
        1. Finds temp data by session_id
        2. Creates/updates CreatorProfile with the data
        3. Links OnboardingStepTracking records to the user
        4. Deletes the temp data

        Args:
            user: The newly registered user
            session_id: The onboarding session ID

        Returns:
            CreatorProfile if data was found and linked, None otherwise
        """
        if not session_id:
            logger.warning(f"No session_id provided for user {user.email}")
            return None

        # Get temporary data
        temp_data = cls.get_temp_data(session_id)
        if not temp_data:
            logger.info(f"No temp data found for session {session_id}")
            return None

        # Get or create profile
        profile, created = CreatorProfile.objects.get_or_create(user=user)

        # Apply all temporary data to profile
        all_data = temp_data.get_all_data()
        for field, value in all_data.items():
            if hasattr(profile, field) and value:
                if isinstance(value, str):
                    value = value.strip()
                setattr(profile, field, value)

        profile.save()
        logger.info(f"Applied temp data to profile for user {user.email}")

        # Link OnboardingStepTracking records to user
        updated_count = OnboardingStepTracking.objects.filter(
            session_id=session_id
        ).update(user=user)
        logger.info(f"Linked {updated_count} tracking records to user {user.email}")

        # Delete temporary data
        temp_data.delete()
        logger.info(f"Deleted temp data for session {session_id}")

        return profile

    @classmethod
    def cleanup_expired_data(cls) -> int:
        """Delete expired temporary data. Returns count of deleted records."""
        deleted_count, _ = OnboardingTempData.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired temp data records")
        return deleted_count
