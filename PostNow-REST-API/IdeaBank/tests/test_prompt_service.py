"""
Testes para PromptService.

Cobertura:
- _format_colors_for_logo: conversão de HEX para narrativa
- _build_logo_prompt_section: geração de seção de logo
- build_content_prompt: roteamento por tipo de post
- build_image_prompt: roteamento por tipo de imagem
- get_creator_profile_data: casos de erro e sucesso
"""

from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock

from IdeaBank.services.prompt_service import (
    PromptService,
    _format_colors_for_logo,
    _build_logo_prompt_section,
    HEX_TO_COLOR_NAME,
)
from CreatorProfile.models import CreatorProfile, VisualStylePreference


class FormatColorsForLogoTest(TestCase):
    """Testes para a função _format_colors_for_logo."""

    def test_format_known_colors(self):
        """Deve converter cores HEX conhecidas para nomes narrativos."""
        colors = ['#8B5CF6', '#FFFFFF', '#4B4646']
        result = _format_colors_for_logo(colors)

        self.assertIn('Roxo vibrante', result)
        self.assertIn('Branco puro', result)
        self.assertIn('Cinza carvão escuro', result)

    def test_format_unknown_colors(self):
        """Deve criar fallback para cores não mapeadas."""
        colors = ['#123456']
        result = _format_colors_for_logo(colors)

        self.assertIn('Cor personalizada (#123456)', result)

    def test_format_empty_list(self):
        """Deve retornar mensagem padrão para lista vazia."""
        result = _format_colors_for_logo([])

        self.assertEqual(result, '- Cores não definidas')

    def test_format_none(self):
        """Deve retornar mensagem padrão para None."""
        result = _format_colors_for_logo(None)

        self.assertEqual(result, '- Cores não definidas')

    def test_format_mixed_case(self):
        """Deve funcionar com cores em lowercase."""
        colors = ['#8b5cf6', '#ffffff']
        result = _format_colors_for_logo(colors)

        self.assertIn('Roxo vibrante', result)
        self.assertIn('Branco puro', result)

    def test_format_with_empty_string(self):
        """Deve ignorar strings vazias na lista."""
        colors = ['#8B5CF6', '', '#FFFFFF']
        result = _format_colors_for_logo(colors)

        # String vazia deve gerar fallback
        self.assertIn('Roxo vibrante', result)
        self.assertIn('Branco puro', result)


class BuildLogoPromptSectionTest(TestCase):
    """Testes para a função _build_logo_prompt_section."""

    def test_basic_section_generation(self):
        """Deve gerar seção de logo com nome e cores."""
        result = _build_logo_prompt_section(
            business_name='TestBrand',
            color_palette=['#8B5CF6', '#FFFFFF']
        )

        self.assertIn('TestBrand', result)
        self.assertIn('LOGO (Preserved Element)', result)
        self.assertIn('Roxo vibrante', result)
        self.assertIn('PRESERVE EXACTLY', result)

    def test_custom_position(self):
        """Deve usar posição customizada."""
        result = _build_logo_prompt_section(
            business_name='TestBrand',
            color_palette=['#FFFFFF'],
            position='top-left corner'
        )

        self.assertIn('top-left corner', result)

    def test_default_position(self):
        """Deve usar posição padrão (bottom-right corner)."""
        result = _build_logo_prompt_section(
            business_name='TestBrand',
            color_palette=['#FFFFFF']
        )

        self.assertIn('bottom-right corner', result)

    def test_empty_palette(self):
        """Deve funcionar com paleta vazia."""
        result = _build_logo_prompt_section(
            business_name='TestBrand',
            color_palette=[]
        )

        self.assertIn('TestBrand', result)
        self.assertIn('Cores não definidas', result)

    def test_contains_preservation_instructions(self):
        """Deve conter instruções de preservação."""
        result = _build_logo_prompt_section(
            business_name='TestBrand',
            color_palette=['#8B5CF6']
        )

        self.assertIn('PRESERVE EXACTLY', result)
        self.assertIn('Change ONLY', result)
        self.assertIn('Keep the logo unchanged', result)


class PromptServiceBasicTest(TestCase):
    """Testes básicos do PromptService."""

    def setUp(self):
        """Criar usuário e perfil de teste."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.profile = CreatorProfile.objects.create(
            user=self.user,
            business_name='Test Business',
            specialization='Marketing Digital',
            business_description='Uma empresa de teste',
            target_audience='Empreendedores',
            voice_tone='Profissional',
            color_1='#8B5CF6',
            color_2='#FFFFFF',
            color_3='#4B4646',
        )
        self.visual_style = VisualStylePreference.objects.create(
            name='Minimalista Moderno',
            description='Design clean e moderno'
        )
        self.profile.visual_style_ids = [self.visual_style.id]
        self.profile.save()

        self.service = PromptService()
        self.service.set_user(self.user)

    def test_set_user(self):
        """Deve definir o usuário corretamente."""
        service = PromptService()
        service.set_user(self.user)

        self.assertEqual(service.user, self.user)

    def test_get_creator_profile_data_success(self):
        """Deve retornar dados do perfil corretamente."""
        data = self.service.get_creator_profile_data()

        self.assertEqual(data['business_name'], 'Test Business')
        self.assertEqual(data['specialization'], 'Marketing Digital')
        self.assertEqual(data['voice_tone'], 'Profissional')
        self.assertIn('#8B5CF6', data['color_palette'])

    def test_get_creator_profile_data_no_user(self):
        """Deve lançar erro se usuário não definido."""
        service = PromptService()

        with self.assertRaises(ValueError) as context:
            service.get_creator_profile_data()

        self.assertIn('User is not set', str(context.exception))

    def test_get_creator_profile_data_no_profile(self):
        """Deve lançar erro se perfil não existe."""
        new_user = User.objects.create_user(
            username='newuser',
            email='new@test.com',
            password='testpass123'
        )
        service = PromptService()
        service.set_user(new_user)

        with self.assertRaises(ValueError) as context:
            service.get_creator_profile_data()

        self.assertIn('CreatorProfile not found', str(context.exception))


class BuildContentPromptTest(TestCase):
    """Testes para build_content_prompt (roteamento)."""

    def setUp(self):
        """Criar usuário e perfil de teste."""
        self.user = User.objects.create_user(
            username='testuser2',
            email='test2@test.com',
            password='testpass123'
        )
        self.profile = CreatorProfile.objects.create(
            user=self.user,
            business_name='Test Business',
            specialization='Marketing Digital',
            voice_tone='Profissional',
        )
        self.service = PromptService()
        self.service.set_user(self.user)

    def test_route_to_feed_post(self):
        """Deve rotear para feed post."""
        post_data = {
            'type': 'post',
            'name': 'Teste',
            'objective': 'Engajamento'
        }
        result = self.service.build_content_prompt(post_data)

        self.assertIn('copywriting', result.lower())
        self.assertIn('Feed', result)

    def test_route_to_reel(self):
        """Deve rotear para reel."""
        post_data = {
            'type': 'reel',
            'name': 'Teste',
            'objective': 'Viralizar'
        }
        result = self.service.build_content_prompt(post_data)

        self.assertIn('roteiro', result.lower())
        self.assertIn('Reels', result)

    def test_route_to_story(self):
        """Deve rotear para story."""
        post_data = {
            'type': 'story',
            'name': 'Teste',
            'objective': 'Engajamento'
        }
        result = self.service.build_content_prompt(post_data)

        self.assertIn('Stories', result)

    def test_route_unknown_type(self):
        """Deve retornar vazio para tipo desconhecido."""
        post_data = {
            'type': 'unknown',
            'name': 'Teste'
        }
        result = self.service.build_content_prompt(post_data)

        self.assertEqual(result, '')

    def test_case_insensitive_routing(self):
        """Deve funcionar com tipos em maiúsculo."""
        post_data = {
            'type': 'POST',
            'name': 'Teste',
            'objective': 'Engajamento'
        }
        result = self.service.build_content_prompt(post_data)

        self.assertIn('Feed', result)


class BuildImagePromptTest(TestCase):
    """Testes para build_image_prompt."""

    def setUp(self):
        """Criar usuário e perfil de teste."""
        self.user = User.objects.create_user(
            username='testuser3',
            email='test3@test.com',
            password='testpass123'
        )
        self.profile = CreatorProfile.objects.create(
            user=self.user,
            business_name='Test Business',
            specialization='Marketing Digital',
            voice_tone='Profissional',
            color_1='#8B5CF6',
        )
        self.visual_style = VisualStylePreference.objects.create(
            name='Bold Vibrante',
            description='Cores fortes e impactantes'
        )
        self.profile.visual_style_ids = [self.visual_style.id]
        self.profile.save()

        self.service = PromptService()
        self.service.set_user(self.user)

    def test_feed_image_prompt_contains_logo_section(self):
        """Deve incluir seção de logo no prompt de imagem de feed."""
        post_data = {
            'type': 'post',
            'name': 'Teste',
            'objective': 'Vendas'
        }
        result = self.service.build_image_prompt(post_data, 'conteúdo teste')

        self.assertIn('LOGO (Preserved Element)', result)
        self.assertIn('Test Business', result)

    def test_reel_image_prompt_contains_logo_section(self):
        """Deve incluir seção de logo no prompt de capa de reel."""
        post_data = {
            'type': 'reel',
            'name': 'Teste',
            'objective': 'Viralizar'
        }
        result = self.service.build_image_prompt(post_data, 'conteúdo teste')

        self.assertIn('LOGO (Preserved Element)', result)

    def test_story_image_prompt_contains_logo_section(self):
        """Deve incluir seção de logo no prompt de story."""
        post_data = {
            'type': 'story',
            'name': 'Teste',
            'objective': 'Engajamento'
        }
        result = self.service.build_image_prompt(post_data, 'conteúdo teste')

        self.assertIn('LOGO (Preserved Element)', result)

    def test_image_prompt_contains_color_palette(self):
        """Deve incluir paleta de cores no prompt."""
        post_data = {
            'type': 'post',
            'name': 'Teste',
            'objective': 'Vendas'
        }
        result = self.service.build_image_prompt(post_data, 'conteúdo teste')

        self.assertIn('#8B5CF6', result)

    def test_image_prompt_contains_visual_style(self):
        """Deve incluir estilo visual no prompt."""
        post_data = {
            'type': 'post',
            'name': 'Teste',
            'objective': 'Vendas'
        }
        result = self.service.build_image_prompt(post_data, 'conteúdo teste')

        # Pode ter o nome do estilo ou descrição
        self.assertTrue(
            'Bold Vibrante' in result or 'Cores fortes' in result,
            "Estilo visual não encontrado no prompt"
        )


class FormatColorPaletteTest(TestCase):
    """Testes para _format_color_palette."""

    def test_format_palette(self):
        """Deve formatar paleta como string."""
        service = PromptService()
        result = service._format_color_palette(['#8B5CF6', '#FFFFFF'])

        self.assertEqual(result, '#8B5CF6, #FFFFFF')

    def test_format_empty_palette(self):
        """Deve retornar mensagem padrão para paleta vazia."""
        service = PromptService()
        result = service._format_color_palette([])

        self.assertEqual(result, 'Não definida')

    def test_format_none_palette(self):
        """Deve retornar mensagem padrão para None."""
        service = PromptService()
        result = service._format_color_palette(None)

        self.assertEqual(result, 'Não definida')
