from typing import Dict, List

from django.contrib.auth.models import User
from django.db import transaction

from core.services import BaseBusinessService

from .models import CreatorProfile


class CreatorProfileService(BaseBusinessService[CreatorProfile]):
    """Service class for CreatorProfile business logic."""

    model = CreatorProfile

    @classmethod
    def validate_business_rules(cls, data: Dict, instance: CreatorProfile = None) -> Dict:
        """
        Validate business rules for creator profile.

        Args:
            data: The data to validate
            instance: Existing instance for updates

        Returns:
            Dict: Validated data

        Raises:
            ValueError: If business rules are violated
        """
        # Validate step progression
        if instance and 'current_step' in data:
            new_step = data['current_step']
            if new_step > instance.current_step + 1:
                raise ValueError("Não é possível pular etapas do onboarding.")

        return data

    @classmethod
    def get_or_create_profile(cls, user: User) -> CreatorProfile:
        """Get existing profile or create new one."""
        profile, created = cls.get_or_create(user=user)
        return profile

    @classmethod
    @transaction.atomic
    def update_profile_data(cls, user: User, data: Dict) -> CreatorProfile:
        """Update profile with provided data."""
        profile = cls.get_or_create_profile(user)

        # Update only the fields that were provided
        for key, value in data.items():
            if hasattr(profile, key):
                # Clean the value before setting
                if isinstance(value, str):
                    value = value.strip() if value else None
                setattr(profile, key, value)

        # Validate business rules before saving
        validated_data = {k: v for k, v in data.items() if hasattr(profile, k)}
        cls.validate_business_rules(validated_data, profile)

        # Force save to trigger the custom save method
        profile.save()

        return profile

    @classmethod
    def reset_profile(cls, user: User) -> bool:
        """Reset user profile."""
        try:
            profile = cls.get_queryset().filter(user=user).first()
            if profile:
                profile.step_1_completed = False
                profile.step_2_completed = False
                profile.step_3_completed = False
                profile.onboarding_completed = False
                profile.save()
                return True
            return False
        except Exception:
            return False

    @classmethod
    def complete_profile(cls, user: User) -> bool:
        """Complete user profile onboarding."""
        try:
            profile = cls.get_queryset().filter(user=user).first()
            if profile:
                profile.step_1_completed = True
                profile.step_2_completed = True
                profile.step_3_completed = True
                profile.onboarding_completed = True
                profile.save()
                return True
            return False
        except Exception:
            return False

    @classmethod
    def get_profiles_by_step(cls, step: int) -> List[CreatorProfile]:
        """Get all profiles currently on a specific step."""
        return cls.get_queryset().filter(current_step=step)

    @classmethod
    def get_completed_profiles(cls) -> List[CreatorProfile]:
        """Get all completed profiles."""
        return cls.get_queryset().filter(onboarding_completed=True)

    @classmethod
    def get_incomplete_profiles(cls) -> List[CreatorProfile]:
        """Get all incomplete profiles."""
        return cls.get_queryset().filter(onboarding_completed=False)


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
