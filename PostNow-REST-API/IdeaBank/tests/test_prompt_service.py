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


class FormatCreatorProfileSectionTest(TestCase):
    """Testes para _format_creator_profile_section."""

    def setUp(self):
        """Criar instância do serviço."""
        self.service = PromptService()

    def test_format_basic_profile(self):
        """Deve formatar dados básicos do perfil."""
        profile_data = {
            'business_name': 'Minha Empresa',
            'specialization': 'Marketing Digital',
            'business_description': 'Agência de marketing',
            'target_audience': 'PMEs',
            'target_interests': 'Crescimento',
            'business_location': 'São Paulo',
            'color_palette': '#8B5CF6, #FFFFFF',
            'voice_tone': 'Profissional',
        }
        result = self.service._format_creator_profile_section(profile_data)

        self.assertIn('Minha Empresa', result)
        self.assertIn('Marketing Digital', result)
        self.assertIn('Profissional', result)

    def test_format_with_phone(self):
        """Deve incluir telefone quando solicitado."""
        profile_data = {
            'business_name': 'Empresa',
            'business_phone': '11999999999',
        }
        result = self.service._format_creator_profile_section(profile_data, include_phone=True)

        self.assertIn('11999999999', result)

    def test_format_without_phone(self):
        """Não deve incluir telefone por padrão."""
        profile_data = {
            'business_name': 'Empresa',
            'business_phone': '11999999999',
        }
        result = self.service._format_creator_profile_section(profile_data, include_phone=False)

        self.assertNotIn('11999999999', result)

    def test_format_missing_fields(self):
        """Deve usar 'Não informado' para campos ausentes."""
        profile_data = {}
        result = self.service._format_creator_profile_section(profile_data)

        self.assertIn('Não informado', result)


class FormatPostDataSectionTest(TestCase):
    """Testes para _format_post_data_section."""

    def setUp(self):
        """Criar instância do serviço."""
        self.service = PromptService()

    def test_format_complete_post_data(self):
        """Deve formatar dados completos do post."""
        post_data = {
            'name': 'Lançamento Produto',
            'objective': 'Vendas',
            'further_details': 'Desconto de 20%',
        }
        result = self.service._format_post_data_section(post_data)

        self.assertIn('Lançamento Produto', result)
        self.assertIn('Vendas', result)
        self.assertIn('Desconto de 20%', result)

    def test_format_without_details(self):
        """Deve mostrar 'Nenhum' quando não há detalhes."""
        post_data = {
            'name': 'Post Simples',
            'objective': 'Engajamento',
        }
        result = self.service._format_post_data_section(post_data)

        self.assertIn('Nenhum', result)

    def test_format_empty_post_data(self):
        """Deve funcionar com dados vazios."""
        post_data = {}
        result = self.service._format_post_data_section(post_data)

        self.assertIn('Assunto:', result)
        self.assertIn('Objetivo:', result)


class BuildContentEditPromptTest(TestCase):
    """Testes para _build_content_edit_prompt (método base)."""

    def setUp(self):
        """Criar instância do serviço."""
        self.service = PromptService()

    def test_build_with_instructions(self):
        """Deve incluir instruções quando fornecidas."""
        result = self.service._build_content_edit_prompt(
            current_content='Texto original',
            instructions='Trocar título para X'
        )

        self.assertIn('Texto original', result)
        self.assertIn('Trocar título para X', result)
        self.assertIn('Alterações solicitadas', result)

    def test_build_without_instructions(self):
        """Não deve incluir seção de alterações quando não há instruções."""
        result = self.service._build_content_edit_prompt(
            current_content='Texto original',
            instructions=None
        )

        self.assertIn('Texto original', result)
        self.assertNotIn('Alterações solicitadas', result)

    def test_contains_editing_rules(self):
        """Deve conter regras de edição."""
        result = self.service._build_content_edit_prompt('Conteúdo')

        self.assertIn('REGRAS PARA EDIÇÃO', result)
        self.assertIn('identidade visual', result)
        self.assertIn('refinar e ajustar', result)


class BuildRegenerationPromptTest(TestCase):
    """Testes para build_regeneration_prompt."""

    def setUp(self):
        """Criar instância do serviço."""
        self.service = PromptService()

    def test_includes_user_prompt(self):
        """Deve incluir o prompt do usuário."""
        result = self.service.build_regeneration_prompt(
            current_content='Copy original',
            user_prompt='Mudar o CTA para algo mais direto'
        )

        self.assertIn('Copy original', result)
        self.assertIn('Mudar o CTA para algo mais direto', result)

    def test_returns_string(self):
        """Deve retornar uma string."""
        result = self.service.build_regeneration_prompt('conteúdo', 'instruções')

        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)


class BuildVariationPromptTest(TestCase):
    """Testes para build_variation_prompt."""

    def setUp(self):
        """Criar instância do serviço."""
        self.service = PromptService()

    def test_includes_content(self):
        """Deve incluir o conteúdo original."""
        result = self.service.build_variation_prompt('Copy para variar')

        self.assertIn('Copy para variar', result)

    def test_no_specific_instructions(self):
        """Não deve ter instruções específicas (variação automática)."""
        result = self.service.build_variation_prompt('Conteúdo')

        self.assertNotIn('Alterações solicitadas', result)

    def test_returns_string(self):
        """Deve retornar uma string."""
        result = self.service.build_variation_prompt('conteúdo')

        self.assertIsInstance(result, str)


class BuildImageRegenerationPromptTest(TestCase):
    """Testes para build_image_regeneration_prompt."""

    def setUp(self):
        """Criar instância do serviço."""
        self.service = PromptService()

    def test_includes_user_prompt(self):
        """Deve incluir instruções do usuário."""
        result = self.service.build_image_regeneration_prompt('Mudar cor do fundo')

        self.assertIn('Mudar cor do fundo', result)

    def test_default_variation_request(self):
        """Deve ter texto padrão quando prompt vazio."""
        result = self.service.build_image_regeneration_prompt('')

        self.assertIn('nova versão', result)

    def test_contains_preservation_rules(self):
        """Deve conter regras de preservação de identidade."""
        result = self.service.build_image_regeneration_prompt('teste')

        self.assertIn('identidade visual', result)
        self.assertIn('layout', result)


class BuildHistoricalAnalysisPromptTest(TestCase):
    """Testes para build_historical_analysis_prompt."""

    def setUp(self):
        """Criar usuário e perfil de teste."""
        self.user = User.objects.create_user(
            username='testuser_historical',
            email='historical@test.com',
            password='testpass123'
        )
        self.profile = CreatorProfile.objects.create(
            user=self.user,
            business_name='Empresa Histórico',
            specialization='Consultoria',
            voice_tone='Inspirador',
        )
        self.service = PromptService()
        self.service.set_user(self.user)

    def test_includes_post_data(self):
        """Deve incluir dados do post."""
        post_data = {
            'name': 'Análise de Mercado',
            'objective': 'Educar',
            'further_details': 'Foco em tendências'
        }
        result = self.service.build_historical_analysis_prompt(post_data)

        self.assertIn('Análise de Mercado', result)
        self.assertIn('Educar', result)

    def test_includes_profile_data(self):
        """Deve incluir dados do perfil."""
        post_data = {'name': 'Teste', 'objective': 'Teste'}
        result = self.service.build_historical_analysis_prompt(post_data)

        self.assertIn('Empresa Histórico', result)
        self.assertIn('Consultoria', result)

    def test_json_output_format(self):
        """Deve especificar formato JSON na saída."""
        post_data = {'name': 'Teste', 'objective': 'Teste'}
        result = self.service.build_historical_analysis_prompt(post_data)

        self.assertIn('JSON', result)
        self.assertIn('historical_analysis', result)
        self.assertIn('avoid_list', result)


class BuildAutomaticPostPromptTest(TestCase):
    """Testes para build_automatic_post_prompt."""

    def setUp(self):
        """Criar usuário e perfil de teste."""
        self.user = User.objects.create_user(
            username='testuser_auto',
            email='auto@test.com',
            password='testpass123'
        )
        self.profile = CreatorProfile.objects.create(
            user=self.user,
            business_name='Empresa Auto',
            specialization='E-commerce',
            voice_tone='Dinâmico',
            target_audience='Jovens adultos',
        )
        self.service = PromptService()
        self.service.set_user(self.user)

    def test_includes_profile_data(self):
        """Deve incluir dados do perfil."""
        result = self.service.build_automatic_post_prompt()

        self.assertIn('Empresa Auto', result)
        self.assertIn('E-commerce', result)
        self.assertIn('Dinâmico', result)

    def test_includes_analysis_data_when_provided(self):
        """Deve incluir dados de análise quando fornecidos."""
        analysis_data = {
            'new_direction': 'Foco em sustentabilidade',
            'new_headline': 'Eco-friendly é o futuro',
        }
        result = self.service.build_automatic_post_prompt(analysis_data)

        self.assertIn('Foco em sustentabilidade', result)

    def test_json_output_format(self):
        """Deve especificar formato JSON na saída."""
        result = self.service.build_automatic_post_prompt()

        self.assertIn('JSON', result)
        self.assertIn('feed_html', result)

    def test_includes_content_structure(self):
        """Deve incluir estrutura AIDA."""
        result = self.service.build_automatic_post_prompt()

        self.assertIn('AIDA', result)


class GetVisualStyleTest(TestCase):
    """Testes para o método _get_visual_style (substituiu _get_random_visual_style)."""

    def setUp(self):
        """Criar usuário, perfil e estilos de teste."""
        self.user = User.objects.create_user(
            username='testuser_style',
            email='style@test.com',
            password='testpass123'
        )
        # Criar estilos visuais
        self.style1 = VisualStylePreference.objects.create(
            name='Minimalista Moderno',
            description='Design clean e moderno'
        )
        self.style2 = VisualStylePreference.objects.create(
            name='Bold Vibrante',
            description='Cores fortes e impactantes'
        )
        self.style3 = VisualStylePreference.objects.create(
            name='Zen Japonês',
            description='Estética zen e equilibrada'
        )

        self.profile = CreatorProfile.objects.create(
            user=self.user,
            business_name='Test Business Style',
            specialization='Design',
            voice_tone='Criativo',
            visual_style_ids=[self.style1.id, self.style2.id, self.style3.id]
        )

        self.service = PromptService()
        self.service.set_user(self.user)

    def test_get_visual_style_returns_first_by_default(self):
        """Sem style_id, deve retornar o primeiro estilo (preferencial)."""
        style = self.service._get_visual_style(self.profile)

        self.assertEqual(style['name'], 'Minimalista Moderno')
        self.assertEqual(style['description'], 'Design clean e moderno')

    def test_get_visual_style_with_specific_id(self):
        """Com style_id específico, deve retornar esse estilo."""
        style = self.service._get_visual_style(self.profile, style_id=self.style2.id)

        self.assertEqual(style['name'], 'Bold Vibrante')
        self.assertEqual(style['description'], 'Cores fortes e impactantes')

    def test_get_visual_style_consistent_multiple_calls(self):
        """Múltiplas chamadas devem retornar o mesmo estilo (não aleatório)."""
        results = [self.service._get_visual_style(self.profile) for _ in range(10)]

        # Todos devem ser iguais (não aleatório)
        names = [r['name'] for r in results]
        self.assertEqual(len(set(names)), 1)
        self.assertEqual(names[0], 'Minimalista Moderno')

    def test_get_visual_style_fallback_invalid_id(self):
        """Com ID inválido, deve usar fallback para o primeiro."""
        style = self.service._get_visual_style(self.profile, style_id=99999)

        # Deve usar o primeiro como fallback
        self.assertEqual(style['name'], 'Minimalista Moderno')

    def test_get_visual_style_empty_list(self):
        """Com lista vazia, deve retornar dict vazio."""
        self.profile.visual_style_ids = []
        self.profile.save()

        style = self.service._get_visual_style(self.profile)

        self.assertEqual(style['name'], '')
        self.assertEqual(style['description'], '')


class SemanticAnalysisPromptTest(TestCase):
    """Testes para semantic_analysis_prompt."""

    def setUp(self):
        """Criar instância do serviço."""
        self.service = PromptService()

    def test_includes_post_data(self):
        """Deve incluir dados do post no prompt."""
        post_data = {
            'name': 'Dicas de Produtividade',
            'objective': 'Engajamento',
            'further_details': 'Foco em home office'
        }
        content = 'Texto sobre produtividade no trabalho remoto...'

        result = self.service.semantic_analysis_prompt(content, post_data)

        self.assertIn('Dicas de Produtividade', result)
        self.assertIn('Engajamento', result)
        self.assertIn('Foco em home office', result)

    def test_includes_content(self):
        """Deve incluir o conteúdo textual."""
        post_data = {'name': 'Teste', 'objective': 'Teste'}
        content = 'Este é o conteúdo do post para análise semântica.'

        result = self.service.semantic_analysis_prompt(content, post_data)

        self.assertIn('Este é o conteúdo do post', result)

    def test_specifies_json_output(self):
        """Deve especificar formato JSON na saída."""
        result = self.service.semantic_analysis_prompt('conteúdo', {'name': 'test'})

        self.assertIn('JSON', result)
        self.assertIn('tema_principal', result)
        self.assertIn('conceitos_visuais', result)
        self.assertIn('emocoes_associadas', result)

    def test_includes_extraction_instructions(self):
        """Deve ter instruções de extração semântica."""
        result = self.service.semantic_analysis_prompt('conteúdo', {'name': 'test'})

        self.assertIn('tema principal', result.lower())
        self.assertIn('emoções', result.lower())
        self.assertIn('elementos visuais', result.lower())


class BuildImagePromptWithSemanticTest(TestCase):
    """Testes para build_image_prompt_with_semantic."""

    def setUp(self):
        """Criar usuário e perfil de teste."""
        self.user = User.objects.create_user(
            username='testuser_semantic',
            email='semantic@test.com',
            password='testpass123'
        )
        self.visual_style = VisualStylePreference.objects.create(
            name='Tech Futurista',
            description='Linhas clean, tons azulados, estética high-tech'
        )
        self.profile = CreatorProfile.objects.create(
            user=self.user,
            business_name='Tech Company',
            specialization='Tecnologia',
            voice_tone='Inovador',
            target_audience='Desenvolvedores',
            color_1='#8B5CF6',
            color_2='#FFFFFF',
            visual_style_ids=[self.visual_style.id]
        )

        self.service = PromptService()
        self.service.set_user(self.user)

    def test_includes_semantic_analysis_data(self):
        """Deve incluir dados da análise semântica no prompt."""
        post_data = {
            'name': 'Inteligência Artificial',
            'objective': 'Educar',
            'type': 'post'
        }
        content = 'Post sobre IA e machine learning...'
        semantic = {
            'tema_principal': 'Transformação digital através da IA',
            'conceitos_visuais': ['redes neurais', 'dados', 'conexões'],
            'emocoes_associadas': ['curiosidade', 'empolgação'],
            'contexto_visual_sugerido': 'Ambiente tecnológico futurista',
            'elementos_concretos': ['circuitos', 'interfaces', 'gráficos'],
            'atmosfera': 'Inovadora e inspiradora'
        }

        result = self.service.build_image_prompt_with_semantic(post_data, content, semantic)

        self.assertIn('Transformação digital através da IA', result)
        self.assertIn('redes neurais', result)
        self.assertIn('curiosidade', result)
        self.assertIn('Ambiente tecnológico futurista', result)

    def test_includes_profile_data(self):
        """Deve incluir dados do perfil."""
        semantic = {'tema_principal': 'Teste'}

        result = self.service.build_image_prompt_with_semantic(
            {'name': 'test'}, 'content', semantic
        )

        self.assertIn('Tech Company', result)
        self.assertIn('Tecnologia', result)

    def test_includes_visual_style(self):
        """Deve incluir estilo visual."""
        semantic = {'tema_principal': 'Teste'}

        result = self.service.build_image_prompt_with_semantic(
            {'name': 'test'}, 'content', semantic
        )

        self.assertIn('Tech Futurista', result)

    def test_includes_color_narratives(self):
        """Deve incluir cores narrativas (não apenas HEX)."""
        semantic = {'tema_principal': 'Teste'}

        result = self.service.build_image_prompt_with_semantic(
            {'name': 'test'}, 'content', semantic
        )

        self.assertIn('Roxo vibrante', result)

    def test_includes_logo_section(self):
        """Deve incluir seção de logo."""
        semantic = {'tema_principal': 'Teste'}

        result = self.service.build_image_prompt_with_semantic(
            {'name': 'test'}, 'content', semantic
        )

        self.assertIn('LOGO (Preserved Element)', result)
        self.assertIn('Tech Company', result)

    def test_respects_visual_style_id_override(self):
        """Deve respeitar visual_style_id do post_data se fornecido."""
        # Criar outro estilo
        other_style = VisualStylePreference.objects.create(
            name='Minimalista',
            description='Design limpo e simples'
        )
        self.profile.visual_style_ids.append(other_style.id)
        self.profile.save()

        post_data = {
            'name': 'test',
            'visual_style_id': other_style.id
        }
        semantic = {'tema_principal': 'Teste'}

        result = self.service.build_image_prompt_with_semantic(
            post_data, 'content', semantic
        )

        self.assertIn('Minimalista', result)


class VisualStyleIdInPostDataTest(TestCase):
    """Testes para verificar que visual_style_id do post_data é usado corretamente."""

    def setUp(self):
        """Criar usuário e perfil com múltiplos estilos."""
        self.user = User.objects.create_user(
            username='testuser_vsid',
            email='vsid@test.com',
            password='testpass123'
        )
        self.style1 = VisualStylePreference.objects.create(
            name='Estilo Um',
            description='Descrição do estilo um'
        )
        self.style2 = VisualStylePreference.objects.create(
            name='Estilo Dois',
            description='Descrição do estilo dois'
        )
        self.profile = CreatorProfile.objects.create(
            user=self.user,
            business_name='Test Business',
            specialization='Marketing',
            voice_tone='Profissional',
            visual_style_ids=[self.style1.id, self.style2.id],
            color_1='#8B5CF6'
        )

        self.service = PromptService()
        self.service.set_user(self.user)

    def test_feed_image_uses_visual_style_id_from_post_data(self):
        """Feed image prompt deve usar visual_style_id do post_data."""
        post_data = {
            'name': 'Teste',
            'objective': 'Engajamento',
            'type': 'post',
            'visual_style_id': self.style2.id
        }

        result = self.service.build_image_prompt(post_data, 'conteúdo')

        self.assertIn('Estilo Dois', result)

    def test_reel_image_uses_visual_style_id_from_post_data(self):
        """Reel image prompt deve usar visual_style_id do post_data."""
        post_data = {
            'name': 'Teste',
            'objective': 'Viralizar',
            'type': 'reel',
            'visual_style_id': self.style2.id
        }

        result = self.service.build_image_prompt(post_data, 'conteúdo')

        self.assertIn('Estilo Dois', result)

    def test_story_image_uses_visual_style_id_from_post_data(self):
        """Story image prompt deve usar visual_style_id do post_data."""
        post_data = {
            'name': 'Teste',
            'objective': 'Engajamento',
            'type': 'story',
            'visual_style_id': self.style2.id
        }

        result = self.service.build_image_prompt(post_data, 'conteúdo')

        self.assertIn('Estilo Dois', result)

    def test_default_to_first_style_without_visual_style_id(self):
        """Sem visual_style_id, deve usar o primeiro estilo."""
        post_data = {
            'name': 'Teste',
            'objective': 'Engajamento',
            'type': 'post'
        }

        result = self.service.build_image_prompt(post_data, 'conteúdo')

        self.assertIn('Estilo Um', result)
