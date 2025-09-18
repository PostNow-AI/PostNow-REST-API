from typing import Dict, List

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
    def reset_profile(user: User) -> bool:
        """Reset user profile."""
        try:
            profile = CreatorProfile.objects.get(user=user)
            profile.delete()
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
    def get_all_suggestions() -> Dict[str, List[str]]:
        """Get all suggestions."""
        return {
            'professions': SuggestionService.get_profession_suggestions(),
            'specializations': SuggestionService.get_specialization_suggestions(),
            'voice_tones': SuggestionService.get_voice_tone_suggestions(),
            'business_cities': SuggestionService.get_business_city_suggestions(),
        }
