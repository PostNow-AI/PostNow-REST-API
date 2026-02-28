"""
Testes para a feature de style_id na geracao de posts.
Verifica que o estilo visual especifico e usado corretamente.
"""
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

from IdeaBank.serializers import PostGenerationRequestSerializer
from CreatorProfile.models import CreatorProfile, VisualStylePreference


def create_test_user(email, password="testpass123"):
    """Helper para criar usuario de teste."""
    username = email.split("@")[0]
    return User.objects.create_user(
        username=username,
        email=email,
        password=password
    )


def create_visual_style(name, description):
    """Helper para criar estilo visual de teste."""
    return VisualStylePreference.objects.create(
        name=name,
        description=description
    )


class TestPostGenerationRequestSerializerStyleId(TestCase):
    """Testa o campo style_id no serializer de geracao de posts."""

    def test_style_id_is_optional(self):
        """style_id deve ser opcional."""
        data = {
            "name": "Test Post",
            "objective": "branding",
            "type": "feed",
            "include_image": True
        }
        serializer = PostGenerationRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertIsNone(serializer.validated_data.get("style_id"))

    def test_style_id_accepts_integer(self):
        """style_id deve aceitar inteiros."""
        data = {
            "name": "Test Post",
            "objective": "branding",
            "type": "feed",
            "include_image": True,
            "style_id": 5
        }
        serializer = PostGenerationRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data.get("style_id"), 5)

    def test_style_id_accepts_null(self):
        """style_id deve aceitar null."""
        data = {
            "name": "Test Post",
            "objective": "branding",
            "type": "feed",
            "include_image": True,
            "style_id": None
        }
        serializer = PostGenerationRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertIsNone(serializer.validated_data.get("style_id"))

    def test_style_id_rejects_string(self):
        """style_id deve rejeitar strings."""
        data = {
            "name": "Test Post",
            "objective": "branding",
            "type": "feed",
            "include_image": True,
            "style_id": "invalid"
        }
        serializer = PostGenerationRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("style_id", serializer.errors)


class TestGetCreatorProfileDataWithStyleId(TestCase):
    """Testa get_creator_profile_data com style_id especifico."""

    def setUp(self):
        """Configura dados de teste."""
        self.user = create_test_user("test@example.com")
        self.profile = CreatorProfile.objects.create(
            user=self.user,
            business_name="Test Business",
            specialization="Marketing Digital",
            visual_style_ids=[1, 2, 3]
        )
        self.style1 = create_visual_style(
            "Minimalista Moderno",
            "Design limpo e minimalista"
        )
        self.style2 = create_visual_style(
            "Bold Vibrante",
            "Cores fortes e vibrantes"
        )

    def test_returns_specific_style_when_style_id_provided(self):
        """Retorna estilo especifico quando style_id e fornecido."""
        from services.get_creator_profile_data import get_creator_profile_data

        result = get_creator_profile_data(self.user, style_id=self.style1.id)

        expected = f"{self.style1.name} - {self.style1.description}"
        self.assertEqual(result["visual_style"], expected)

    def test_returns_different_style_for_different_id(self):
        """Retorna estilo diferente para ID diferente."""
        from services.get_creator_profile_data import get_creator_profile_data

        result = get_creator_profile_data(self.user, style_id=self.style2.id)

        expected = f"{self.style2.name} - {self.style2.description}"
        self.assertEqual(result["visual_style"], expected)

    def test_fallback_to_random_when_style_not_found(self):
        """Usa estilo aleatorio quando style_id nao existe."""
        from services.get_creator_profile_data import get_creator_profile_data

        # Atualiza profile para ter estilos validos
        self.profile.visual_style_ids = [self.style1.id, self.style2.id]
        self.profile.save()

        result = get_creator_profile_data(self.user, style_id=99999)

        # Deve retornar algum estilo (fallback)
        self.assertTrue(
            result["visual_style"] == "" or
            self.style1.name in result["visual_style"] or
            self.style2.name in result["visual_style"]
        )

    def test_random_style_when_no_style_id(self):
        """Usa estilo aleatorio quando style_id e None."""
        from services.get_creator_profile_data import get_creator_profile_data

        self.profile.visual_style_ids = [self.style1.id]
        self.profile.save()

        result = get_creator_profile_data(self.user, style_id=None)

        # Deve retornar o estilo do profile
        self.assertIn(self.style1.name, result["visual_style"])


class TestGetVisualStyleFunction(TestCase):
    """Testa a funcao get_visual_style isoladamente."""

    def setUp(self):
        """Configura dados de teste."""
        self.user = create_test_user("test2@example.com")
        self.profile = CreatorProfile.objects.create(
            user=self.user,
            business_name="Test Business 2"
        )
        self.style = create_visual_style(
            "Tech Futurista",
            "Estilo tecnologico e futurista"
        )

    def test_get_visual_style_with_valid_id(self):
        """Retorna estilo formatado para ID valido."""
        from services.get_creator_profile_data import get_visual_style

        result = get_visual_style(self.profile, self.user, self.style.id)

        self.assertEqual(result, f"{self.style.name} - {self.style.description}")

    def test_get_visual_style_with_invalid_id_no_fallback(self):
        """Retorna vazio quando ID invalido e sem estilos salvos."""
        from services.get_creator_profile_data import get_visual_style

        self.profile.visual_style_ids = []
        self.profile.save()

        result = get_visual_style(self.profile, self.user, 99999)

        self.assertEqual(result, "")

    def test_get_visual_style_none_uses_random(self):
        """Usa selecao aleatoria quando style_id e None."""
        from services.get_creator_profile_data import get_visual_style

        self.profile.visual_style_ids = [self.style.id]
        self.profile.save()

        result = get_visual_style(self.profile, self.user, None)

        self.assertIn(self.style.name, result)


class TestAIPromptServiceStyleId(TestCase):
    """Testa AIPromptService com style_id."""

    def setUp(self):
        """Configura dados de teste."""
        self.user = create_test_user("test3@example.com")
        self.profile = CreatorProfile.objects.create(
            user=self.user,
            business_name="Test Business 3"
        )
        self.style = create_visual_style(
            "Elegante Editorial",
            "Estilo editorial sofisticado"
        )
        self.profile.visual_style_ids = [self.style.id]
        self.profile.save()

    def test_set_user_stores_style_id(self):
        """set_user armazena style_id corretamente."""
        from services.ai_prompt_service import AIPromptService

        service = AIPromptService()
        service.set_user(self.user, style_id=self.style.id)

        self.assertEqual(service.user, self.user)
        self.assertEqual(service.style_id, self.style.id)

    def test_set_user_without_style_id(self):
        """set_user funciona sem style_id."""
        from services.ai_prompt_service import AIPromptService

        service = AIPromptService()
        service.set_user(self.user)

        self.assertEqual(service.user, self.user)
        self.assertIsNone(service.style_id)

    def test_get_profile_data_uses_style_id(self):
        """_get_profile_data usa style_id configurado."""
        from services.ai_prompt_service import AIPromptService

        service = AIPromptService()
        service.set_user(self.user, style_id=self.style.id)

        profile_data = service._get_profile_data()

        expected = f"{self.style.name} - {self.style.description}"
        self.assertEqual(profile_data["visual_style"], expected)
