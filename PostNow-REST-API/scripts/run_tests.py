#!/usr/bin/env python
"""
Script de testes para PromptService e CreatorProfile.

Uso:
    cd PostNow-REST-API
    source venv/bin/activate
    python scripts/run_tests.py
"""

import os
import sys
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sonora_REST_API.settings')
os.environ['USE_SQLITE'] = 'True'

import django
django.setup()

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from IdeaBank.services.prompt_service import (
    PromptService,
    _format_colors_for_logo,
    _build_logo_prompt_section,
    HEX_TO_COLOR_NAME,
)
from CreatorProfile.models import (
    CreatorProfile,
    VisualStylePreference,
    validate_hex_color,
    validate_visual_style_ids,
)


class TestResults:
    """Rastreia resultados dos testes."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add_pass(self, name):
        self.passed += 1
        print(f"  ✅ {name}")

    def add_fail(self, name, error):
        self.failed += 1
        self.errors.append((name, error))
        print(f"  ❌ {name}: {error}")

    def summary(self):
        total = self.passed + self.failed
        print()
        print("=" * 60)
        print(f"RESULTADOS: {self.passed}/{total} testes passaram")
        print("=" * 60)
        if self.errors:
            print("\nFalhas:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
        return self.failed == 0


def run_test(results, name, test_func):
    """Executa um teste e registra o resultado."""
    try:
        test_func()
        results.add_pass(name)
    except AssertionError as e:
        results.add_fail(name, str(e))
    except Exception as e:
        results.add_fail(name, f"Erro inesperado: {e}")


# =============================================================================
# TESTES: _format_colors_for_logo
# =============================================================================
def test_format_colors_known():
    """Deve converter cores HEX conhecidas para nomes narrativos."""
    colors = ['#8B5CF6', '#FFFFFF', '#4B4646']
    result = _format_colors_for_logo(colors)
    assert 'Roxo vibrante' in result, f"Esperado 'Roxo vibrante' em: {result}"
    assert 'Branco puro' in result, f"Esperado 'Branco puro' em: {result}"
    assert 'Cinza carvão escuro' in result, f"Esperado 'Cinza carvão escuro' em: {result}"


def test_format_colors_unknown():
    """Deve criar fallback para cores não mapeadas."""
    colors = ['#123456']
    result = _format_colors_for_logo(colors)
    assert 'Cor personalizada (#123456)' in result, f"Esperado fallback em: {result}"


def test_format_colors_empty():
    """Deve retornar mensagem padrão para lista vazia."""
    result = _format_colors_for_logo([])
    assert result == '- Cores não definidas', f"Esperado '- Cores não definidas', obtido: {result}"


def test_format_colors_none():
    """Deve retornar mensagem padrão para None."""
    result = _format_colors_for_logo(None)
    assert result == '- Cores não definidas', f"Esperado '- Cores não definidas', obtido: {result}"


def test_format_colors_lowercase():
    """Deve funcionar com cores em lowercase."""
    colors = ['#8b5cf6', '#ffffff']
    result = _format_colors_for_logo(colors)
    assert 'Roxo vibrante' in result, f"Esperado 'Roxo vibrante' em: {result}"
    assert 'Branco puro' in result, f"Esperado 'Branco puro' em: {result}"


# =============================================================================
# TESTES: _build_logo_prompt_section
# =============================================================================
def test_logo_section_basic():
    """Deve gerar seção de logo com nome e cores."""
    result = _build_logo_prompt_section(
        business_name='TestBrand',
        color_palette=['#8B5CF6', '#FFFFFF']
    )
    assert 'TestBrand' in result, "Nome da marca não encontrado"
    assert 'LOGO (Preserved Element)' in result, "Título da seção não encontrado"
    assert 'Roxo vibrante' in result, "Cor não encontrada"
    assert 'PRESERVE EXACTLY' in result, "Instrução de preservação não encontrada"


def test_logo_section_custom_position():
    """Deve usar posição customizada."""
    result = _build_logo_prompt_section(
        business_name='TestBrand',
        color_palette=['#FFFFFF'],
        position='top-left corner'
    )
    assert 'top-left corner' in result, "Posição customizada não encontrada"


def test_logo_section_default_position():
    """Deve usar posição padrão (bottom-right corner)."""
    result = _build_logo_prompt_section(
        business_name='TestBrand',
        color_palette=['#FFFFFF']
    )
    assert 'bottom-right corner' in result, "Posição padrão não encontrada"


def test_logo_section_empty_palette():
    """Deve funcionar com paleta vazia."""
    result = _build_logo_prompt_section(
        business_name='TestBrand',
        color_palette=[]
    )
    assert 'TestBrand' in result, "Nome da marca não encontrado"
    assert 'Cores não definidas' in result, "Mensagem de cores vazias não encontrada"


def test_logo_section_preservation_instructions():
    """Deve conter instruções de preservação completas."""
    result = _build_logo_prompt_section(
        business_name='TestBrand',
        color_palette=['#8B5CF6']
    )
    assert 'PRESERVE EXACTLY' in result, "PRESERVE EXACTLY não encontrado"
    assert 'Change ONLY' in result, "Change ONLY não encontrado"
    assert 'Keep the logo unchanged' in result, "Keep the logo unchanged não encontrado"


# =============================================================================
# TESTES: PromptService._format_color_palette
# =============================================================================
def test_format_palette_basic():
    """Deve formatar paleta como string."""
    service = PromptService()
    result = service._format_color_palette(['#8B5CF6', '#FFFFFF'])
    assert result == '#8B5CF6, #FFFFFF', f"Esperado '#8B5CF6, #FFFFFF', obtido: {result}"


def test_format_palette_empty():
    """Deve retornar mensagem padrão para paleta vazia."""
    service = PromptService()
    result = service._format_color_palette([])
    assert result == 'Não definida', f"Esperado 'Não definida', obtido: {result}"


def test_format_palette_none():
    """Deve retornar mensagem padrão para None."""
    service = PromptService()
    result = service._format_color_palette(None)
    assert result == 'Não definida', f"Esperado 'Não definida', obtido: {result}"


# =============================================================================
# TESTES: PromptService básico
# =============================================================================
def test_prompt_service_init():
    """Deve inicializar sem usuário."""
    service = PromptService()
    assert service.user is None, "Usuário deveria ser None"


def test_prompt_service_set_user():
    """Deve definir usuário corretamente."""
    user = User.objects.filter(username='test_runner_user').first()
    if not user:
        user = User.objects.create_user(
            username='test_runner_user',
            email='test_runner@test.com',
            password='testpass123'
        )
    service = PromptService()
    service.set_user(user)
    assert service.user == user, "Usuário não foi definido corretamente"


def test_prompt_service_no_user_error():
    """Deve lançar erro se usuário não definido."""
    service = PromptService()
    try:
        service.get_creator_profile_data()
        assert False, "Deveria ter lançado ValueError"
    except ValueError as e:
        assert 'User is not set' in str(e), f"Mensagem de erro incorreta: {e}"


# =============================================================================
# TESTES: Validadores de CreatorProfile
# =============================================================================
def test_validate_hex_color_valid():
    """Deve aceitar cores HEX válidas."""
    validate_hex_color('#8B5CF6')  # 6 dígitos
    validate_hex_color('#FFF')     # 3 dígitos
    validate_hex_color('#abc')     # lowercase
    validate_hex_color('')         # vazio (campo opcional)


def test_validate_hex_color_invalid():
    """Deve rejeitar cores HEX inválidas."""
    invalid_colors = ['8B5CF6', '#GGG', '#12345', 'red', '123456']
    for color in invalid_colors:
        try:
            validate_hex_color(color)
            assert False, f"Deveria ter rejeitado: {color}"
        except ValidationError:
            pass  # Esperado


def test_validate_visual_style_ids_valid():
    """Deve aceitar lista de inteiros positivos."""
    validate_visual_style_ids([1, 2, 3])
    validate_visual_style_ids([1])
    validate_visual_style_ids([])  # Lista vazia é válida


def test_validate_visual_style_ids_invalid():
    """Deve rejeitar valores inválidos."""
    invalid_values = [
        'not a list',
        [0],        # Zero não é válido
        [-1],       # Negativo não é válido
        ['a', 'b'], # Strings não são válidas
        [1.5],      # Float não é válido
    ]
    for value in invalid_values:
        try:
            validate_visual_style_ids(value)
            assert False, f"Deveria ter rejeitado: {value}"
        except ValidationError:
            pass  # Esperado


# =============================================================================
# TESTES: build_content_prompt routing
# =============================================================================
def test_build_content_prompt_feed():
    """Deve rotear para feed post."""
    user = User.objects.filter(username='test_runner_user2').first()
    if not user:
        user = User.objects.create_user(
            username='test_runner_user2',
            email='test_runner2@test.com',
            password='testpass123'
        )
    profile = CreatorProfile.objects.filter(user=user).first()
    if not profile:
        profile = CreatorProfile.objects.create(
            user=user,
            business_name='Test Business',
            specialization='Marketing',
            voice_tone='Profissional',
        )

    service = PromptService()
    service.set_user(user)

    post_data = {'type': 'post', 'name': 'Teste', 'objective': 'Engajamento'}
    result = service.build_content_prompt(post_data)

    assert 'Feed' in result, "Deveria conter 'Feed' no prompt"


def test_build_content_prompt_unknown():
    """Deve retornar vazio para tipo desconhecido."""
    user = User.objects.filter(username='test_runner_user2').first()
    service = PromptService()
    service.set_user(user)

    post_data = {'type': 'unknown', 'name': 'Teste'}
    result = service.build_content_prompt(post_data)

    assert result == '', f"Esperado string vazia, obtido: {result[:50]}..."


# =============================================================================
# TESTES: Métodos auxiliares de formatação
# =============================================================================
def test_format_creator_profile_section():
    """Deve formatar seção de perfil corretamente."""
    service = PromptService()
    profile_data = {
        'business_name': 'Minha Empresa',
        'specialization': 'Marketing',
        'business_description': 'Uma empresa de marketing',
        'target_audience': 'Empreendedores',
        'target_interests': 'Negócios, Vendas',
        'business_location': 'São Paulo',
        'color_palette': ['#8B5CF6'],
        'voice_tone': 'Profissional',
    }

    result = service._format_creator_profile_section(profile_data)

    assert 'Minha Empresa' in result, "Nome do negócio não encontrado"
    assert 'Marketing' in result, "Especialização não encontrada"
    assert 'Empreendedores' in result, "Público-alvo não encontrado"
    assert 'Profissional' in result, "Tom de voz não encontrado"


def test_format_creator_profile_section_with_phone():
    """Deve incluir telefone quando solicitado."""
    service = PromptService()
    profile_data = {
        'business_name': 'Teste',
        'business_phone': '(11) 99999-9999',
    }

    result = service._format_creator_profile_section(profile_data, include_phone=True)

    assert '(11) 99999-9999' in result, "Telefone não encontrado"


def test_format_creator_profile_section_without_phone():
    """Não deve incluir telefone por padrão."""
    service = PromptService()
    profile_data = {
        'business_name': 'Teste',
        'business_phone': '(11) 99999-9999',
    }

    result = service._format_creator_profile_section(profile_data, include_phone=False)

    assert '(11) 99999-9999' not in result, "Telefone não deveria estar presente"


def test_format_post_data_section():
    """Deve formatar seção de dados do post corretamente."""
    service = PromptService()
    post_data = {
        'name': 'Título do Post',
        'objective': 'Aumentar engajamento',
        'further_details': 'Detalhes adicionais aqui',
    }

    result = service._format_post_data_section(post_data)

    assert 'Título do Post' in result, "Assunto não encontrado"
    assert 'Aumentar engajamento' in result, "Objetivo não encontrado"
    assert 'Detalhes adicionais aqui' in result, "Detalhes não encontrados"


def test_format_post_data_section_no_details():
    """Deve mostrar 'Nenhum' quando não há detalhes."""
    service = PromptService()
    post_data = {
        'name': 'Título',
        'objective': 'Objetivo',
    }

    result = service._format_post_data_section(post_data)

    assert 'Nenhum' in result, "Deveria mostrar 'Nenhum' para detalhes vazios"


# =============================================================================
# TESTES: CreatorProfile Model
# =============================================================================
def test_creator_profile_create():
    """Deve criar perfil com campos básicos."""
    import uuid
    unique_username = f'test_profile_{uuid.uuid4().hex[:8]}'

    user = User.objects.create_user(
        username=unique_username,
        email=f'{unique_username}@test.com',
        password='testpass123'
    )
    profile = CreatorProfile.objects.create(
        user=user,
        business_name='Minha Empresa',
        specialization='Marketing',
        voice_tone='Profissional',
        color_1='#8B5CF6',
        color_2='#FFFFFF',
    )

    assert profile.id is not None, "Perfil deveria ter ID"
    assert profile.business_name == 'Minha Empresa', "Nome incorreto"
    assert profile.color_1 == '#8B5CF6', "Cor 1 incorreta"


def test_creator_profile_str():
    """Deve retornar representação string correta."""
    user = User.objects.filter(username='test_profile_str').first()
    if not user:
        user = User.objects.create_user(
            username='test_profile_str',
            email='profile_str@test.com',
            password='testpass123'
        )
    profile = CreatorProfile.objects.filter(user=user).first()
    if not profile:
        profile = CreatorProfile.objects.create(
            user=user,
            business_name='TestBiz',
        )

    result = str(profile)
    assert 'TestBiz' in result, f"Esperado 'TestBiz' em: {result}"
    assert 'test_profile_str' in result, f"Esperado username em: {result}"


def test_creator_profile_color_validation():
    """Deve validar cores HEX corretamente."""
    import uuid
    unique_username = f'test_color_{uuid.uuid4().hex[:8]}'

    user = User.objects.create_user(
        username=unique_username,
        email=f'{unique_username}@test.com',
        password='testpass123'
    )

    # Cor válida - deve funcionar
    profile = CreatorProfile(
        user=user,
        business_name='Test',
        color_1='#8B5CF6',
    )
    profile.full_clean()  # Não deve lançar exceção

    # Cor inválida - deve lançar ValidationError
    profile.color_1 = 'invalid'
    try:
        profile.full_clean()
        assert False, "Deveria ter lançado ValidationError para cor inválida"
    except ValidationError as e:
        assert 'color_1' in str(e), f"Erro deveria mencionar color_1: {e}"


def test_creator_profile_visual_style_ids_validation():
    """Deve validar visual_style_ids corretamente."""
    import uuid
    unique_username = f'test_style_{uuid.uuid4().hex[:8]}'

    user = User.objects.create_user(
        username=unique_username,
        email=f'{unique_username}@test.com',
        password='testpass123'
    )

    # IDs válidos
    profile = CreatorProfile(
        user=user,
        business_name='Test',
        visual_style_ids=[1, 2, 3],
    )
    profile.full_clean()  # Não deve lançar exceção

    # IDs inválidos
    profile.visual_style_ids = ['a', 'b']
    try:
        profile.full_clean()
        assert False, "Deveria ter lançado ValidationError para IDs inválidos"
    except ValidationError as e:
        assert 'visual_style_ids' in str(e), f"Erro deveria mencionar visual_style_ids: {e}"


def test_creator_profile_phone_validation():
    """Deve validar telefone corretamente."""
    import uuid
    unique_username = f'test_phone_{uuid.uuid4().hex[:8]}'

    user = User.objects.create_user(
        username=unique_username,
        email=f'{unique_username}@test.com',
        password='testpass123'
    )

    # Telefone válido
    profile = CreatorProfile(
        user=user,
        business_name='Test',
        business_phone='(11) 99999-9999',
    )
    profile.full_clean()  # Não deve lançar exceção

    # Telefone inválido (muito curto)
    profile.business_phone = '123'
    try:
        profile.full_clean()
        assert False, "Deveria ter lançado ValidationError para telefone inválido"
    except ValidationError as e:
        assert 'business_phone' in str(e), f"Erro deveria mencionar business_phone: {e}"


def test_creator_profile_onboarding_fields():
    """Deve ter campos de onboarding com defaults corretos."""
    import uuid
    unique_username = f'test_onboard_{uuid.uuid4().hex[:8]}'

    user = User.objects.create_user(
        username=unique_username,
        email=f'{unique_username}@test.com',
        password='testpass123'
    )
    profile = CreatorProfile.objects.create(
        user=user,
        business_name='Test',
    )

    assert profile.step_1_completed == False, "step_1_completed deveria ser False"
    assert profile.step_2_completed == False, "step_2_completed deveria ser False"
    assert profile.onboarding_completed == False, "onboarding_completed deveria ser False"
    assert profile.onboarding_completed_at is None, "onboarding_completed_at deveria ser None"


# =============================================================================
# TESTES: _get_visual_style (novo - substitui _get_random_visual_style)
# =============================================================================
def test_get_visual_style_returns_first_by_default():
    """Sem style_id, deve retornar o primeiro estilo (preferencial, não aleatório)."""
    import uuid
    unique_username = f'test_vs_{uuid.uuid4().hex[:8]}'

    user = User.objects.create_user(
        username=unique_username,
        email=f'{unique_username}@test.com',
        password='testpass123'
    )

    # Criar estilos
    style1 = VisualStylePreference.objects.create(
        name=f'Estilo Um {unique_username}',
        description='Primeiro estilo'
    )
    style2 = VisualStylePreference.objects.create(
        name=f'Estilo Dois {unique_username}',
        description='Segundo estilo'
    )

    profile = CreatorProfile.objects.create(
        user=user,
        business_name='Test VS',
        visual_style_ids=[style1.id, style2.id]
    )

    service = PromptService()
    result = service._get_visual_style(profile)

    assert result['name'] == f'Estilo Um {unique_username}', f"Esperado primeiro estilo, obtido: {result['name']}"


def test_get_visual_style_with_specific_id():
    """Com style_id específico, deve retornar esse estilo."""
    import uuid
    unique_username = f'test_vs_spec_{uuid.uuid4().hex[:8]}'

    user = User.objects.create_user(
        username=unique_username,
        email=f'{unique_username}@test.com',
        password='testpass123'
    )

    style1 = VisualStylePreference.objects.create(
        name=f'Primeiro {unique_username}',
        description='Primeiro'
    )
    style2 = VisualStylePreference.objects.create(
        name=f'Segundo {unique_username}',
        description='Segundo'
    )

    profile = CreatorProfile.objects.create(
        user=user,
        business_name='Test',
        visual_style_ids=[style1.id, style2.id]
    )

    service = PromptService()
    result = service._get_visual_style(profile, style_id=style2.id)

    assert result['name'] == f'Segundo {unique_username}', f"Esperado segundo estilo, obtido: {result['name']}"


def test_get_visual_style_consistent_multiple_calls():
    """Múltiplas chamadas devem retornar o mesmo estilo (não aleatório)."""
    import uuid
    unique_username = f'test_vs_cons_{uuid.uuid4().hex[:8]}'

    user = User.objects.create_user(
        username=unique_username,
        email=f'{unique_username}@test.com',
        password='testpass123'
    )

    style1 = VisualStylePreference.objects.create(
        name=f'Style A {unique_username}',
        description='Style A'
    )
    style2 = VisualStylePreference.objects.create(
        name=f'Style B {unique_username}',
        description='Style B'
    )

    profile = CreatorProfile.objects.create(
        user=user,
        business_name='Test',
        visual_style_ids=[style1.id, style2.id]
    )

    service = PromptService()
    results = [service._get_visual_style(profile)['name'] for _ in range(10)]

    # Todos devem ser iguais (não aleatório)
    unique_results = set(results)
    assert len(unique_results) == 1, f"Deveria ter apenas 1 resultado único, obtido: {unique_results}"


def test_get_visual_style_empty_list():
    """Com lista vazia, deve retornar dict vazio."""
    import uuid
    unique_username = f'test_vs_empty_{uuid.uuid4().hex[:8]}'

    user = User.objects.create_user(
        username=unique_username,
        email=f'{unique_username}@test.com',
        password='testpass123'
    )

    profile = CreatorProfile.objects.create(
        user=user,
        business_name='Test',
        visual_style_ids=[]
    )

    service = PromptService()
    result = service._get_visual_style(profile)

    assert result['name'] == '', f"Nome deveria ser vazio, obtido: {result['name']}"
    assert result['description'] == '', f"Descrição deveria ser vazia, obtido: {result['description']}"


# =============================================================================
# TESTES: semantic_analysis_prompt (novo)
# =============================================================================
def test_semantic_analysis_prompt_includes_content():
    """Deve incluir conteúdo textual no prompt."""
    service = PromptService()
    post_data = {'name': 'Dicas de Produtividade', 'objective': 'Engajamento'}
    content = 'Texto sobre produtividade no trabalho remoto...'

    result = service.semantic_analysis_prompt(content, post_data)

    assert 'Dicas de Produtividade' in result, "Assunto não encontrado"
    assert 'Engajamento' in result, "Objetivo não encontrado"
    assert 'produtividade no trabalho remoto' in result, "Conteúdo não encontrado"


def test_semantic_analysis_prompt_json_format():
    """Deve especificar formato JSON na saída."""
    service = PromptService()

    result = service.semantic_analysis_prompt('conteúdo', {'name': 'test'})

    assert 'JSON' in result, "Deveria mencionar JSON"
    assert 'tema_principal' in result, "Deveria ter campo tema_principal"
    assert 'conceitos_visuais' in result, "Deveria ter campo conceitos_visuais"
    assert 'emocoes_associadas' in result, "Deveria ter campo emocoes_associadas"


# =============================================================================
# TESTES: build_image_prompt_with_semantic (novo)
# =============================================================================
def test_build_image_prompt_with_semantic_includes_analysis():
    """Deve incluir dados da análise semântica no prompt."""
    import uuid
    unique_username = f'test_semantic_{uuid.uuid4().hex[:8]}'

    user = User.objects.create_user(
        username=unique_username,
        email=f'{unique_username}@test.com',
        password='testpass123'
    )

    style = VisualStylePreference.objects.create(
        name=f'Tech Style {unique_username}',
        description='High-tech aesthetic'
    )

    profile = CreatorProfile.objects.create(
        user=user,
        business_name='Tech Company',
        specialization='Tecnologia',
        voice_tone='Inovador',
        color_1='#8B5CF6',
        visual_style_ids=[style.id]
    )

    service = PromptService()
    service.set_user(user)

    post_data = {'name': 'IA', 'objective': 'Educar', 'type': 'post'}
    content = 'Post sobre IA...'
    semantic = {
        'tema_principal': 'Inteligência Artificial transformando negócios',
        'conceitos_visuais': ['redes neurais', 'dados'],
        'emocoes_associadas': ['curiosidade'],
        'contexto_visual_sugerido': 'Ambiente futurista',
        'elementos_concretos': ['circuitos'],
        'atmosfera': 'Inovadora'
    }

    result = service.build_image_prompt_with_semantic(post_data, content, semantic)

    assert 'Inteligência Artificial transformando negócios' in result, "Tema principal não encontrado"
    assert 'redes neurais' in result, "Conceitos visuais não encontrados"
    assert 'curiosidade' in result, "Emoções não encontradas"


def test_build_image_prompt_with_semantic_includes_logo():
    """Deve incluir seção de logo."""
    import uuid
    unique_username = f'test_logo_sem_{uuid.uuid4().hex[:8]}'

    user = User.objects.create_user(
        username=unique_username,
        email=f'{unique_username}@test.com',
        password='testpass123'
    )

    profile = CreatorProfile.objects.create(
        user=user,
        business_name='Logo Test Company',
        color_1='#8B5CF6'
    )

    service = PromptService()
    service.set_user(user)

    semantic = {'tema_principal': 'Teste'}
    result = service.build_image_prompt_with_semantic({'name': 'test'}, 'content', semantic)

    assert 'LOGO (Preserved Element)' in result, "Seção de logo não encontrada"
    assert 'Logo Test Company' in result, "Nome da empresa não encontrado"


# =============================================================================
# TESTES: visual_style_id em post_data (novo)
# =============================================================================
def test_feed_image_respects_visual_style_id():
    """Feed image prompt deve usar visual_style_id do post_data."""
    import uuid
    unique_username = f'test_vsid_{uuid.uuid4().hex[:8]}'

    user = User.objects.create_user(
        username=unique_username,
        email=f'{unique_username}@test.com',
        password='testpass123'
    )

    style1 = VisualStylePreference.objects.create(
        name=f'Primeiro Estilo {unique_username}',
        description='Primeiro'
    )
    style2 = VisualStylePreference.objects.create(
        name=f'Segundo Estilo {unique_username}',
        description='Segundo'
    )

    profile = CreatorProfile.objects.create(
        user=user,
        business_name='Test',
        specialization='Marketing',
        color_1='#8B5CF6',
        visual_style_ids=[style1.id, style2.id]
    )

    service = PromptService()
    service.set_user(user)

    # Passar visual_style_id do SEGUNDO estilo
    post_data = {
        'name': 'Teste',
        'objective': 'Engajamento',
        'type': 'post',
        'visual_style_id': style2.id
    }

    result = service.build_image_prompt(post_data, 'conteúdo')

    assert f'Segundo Estilo {unique_username}' in result, f"Deveria usar segundo estilo, resultado: {result[:500]}"


def test_get_creator_profile_data_with_style_id():
    """get_creator_profile_data deve respeitar visual_style_id."""
    import uuid
    unique_username = f'test_gcpd_{uuid.uuid4().hex[:8]}'

    user = User.objects.create_user(
        username=unique_username,
        email=f'{unique_username}@test.com',
        password='testpass123'
    )

    style1 = VisualStylePreference.objects.create(
        name=f'Style Alpha {unique_username}',
        description='Alpha'
    )
    style2 = VisualStylePreference.objects.create(
        name=f'Style Beta {unique_username}',
        description='Beta'
    )

    profile = CreatorProfile.objects.create(
        user=user,
        business_name='Test GCPD',
        visual_style_ids=[style1.id, style2.id]
    )

    service = PromptService()
    service.set_user(user)

    # Sem style_id - deve retornar primeiro
    data1 = service.get_creator_profile_data()
    assert data1['visual_style']['name'] == f'Style Alpha {unique_username}', "Sem style_id deveria usar primeiro"

    # Com style_id - deve retornar específico
    data2 = service.get_creator_profile_data(visual_style_id=style2.id)
    assert data2['visual_style']['name'] == f'Style Beta {unique_username}', "Com style_id deveria usar o específico"


# =============================================================================
# TESTES: VisualStylePreference Model
# =============================================================================
def test_visual_style_create():
    """Deve criar estilo visual corretamente."""
    style = VisualStylePreference.objects.filter(name='Test Style Temp').first()
    if style:
        style.delete()

    style = VisualStylePreference.objects.create(
        name='Test Style Temp',
        description='Descrição do estilo de teste',
        preview_image_url='https://example.com/image.png'
    )

    assert style.id is not None, "Estilo deveria ter ID"
    assert style.name == 'Test Style Temp', "Nome incorreto"


def test_visual_style_str():
    """Deve retornar nome como representação string."""
    style = VisualStylePreference.objects.filter(name='Test Style Str').first()
    if not style:
        style = VisualStylePreference.objects.create(
            name='Test Style Str',
            description='Teste',
        )

    result = str(style)
    assert result == 'Test Style Str', f"Esperado 'Test Style Str', obtido: {result}"


# =============================================================================
# MAIN
# =============================================================================
def main():
    print("=" * 60)
    print("TESTES: PromptService & CreatorProfile")
    print("=" * 60)
    print()

    results = TestResults()

    # _format_colors_for_logo
    print("📦 _format_colors_for_logo:")
    run_test(results, "cores conhecidas", test_format_colors_known)
    run_test(results, "cores desconhecidas", test_format_colors_unknown)
    run_test(results, "lista vazia", test_format_colors_empty)
    run_test(results, "None", test_format_colors_none)
    run_test(results, "lowercase", test_format_colors_lowercase)
    print()

    # _build_logo_prompt_section
    print("📦 _build_logo_prompt_section:")
    run_test(results, "seção básica", test_logo_section_basic)
    run_test(results, "posição customizada", test_logo_section_custom_position)
    run_test(results, "posição padrão", test_logo_section_default_position)
    run_test(results, "paleta vazia", test_logo_section_empty_palette)
    run_test(results, "instruções de preservação", test_logo_section_preservation_instructions)
    print()

    # _format_color_palette
    print("📦 PromptService._format_color_palette:")
    run_test(results, "formatação básica", test_format_palette_basic)
    run_test(results, "lista vazia", test_format_palette_empty)
    run_test(results, "None", test_format_palette_none)
    print()

    # PromptService básico
    print("📦 PromptService básico:")
    run_test(results, "inicialização", test_prompt_service_init)
    run_test(results, "set_user", test_prompt_service_set_user)
    run_test(results, "erro sem usuário", test_prompt_service_no_user_error)
    print()

    # Validadores
    print("📦 Validadores CreatorProfile:")
    run_test(results, "hex color válido", test_validate_hex_color_valid)
    run_test(results, "hex color inválido", test_validate_hex_color_invalid)
    run_test(results, "visual_style_ids válido", test_validate_visual_style_ids_valid)
    run_test(results, "visual_style_ids inválido", test_validate_visual_style_ids_invalid)
    print()

    # Routing
    print("📦 build_content_prompt routing:")
    run_test(results, "rotear para feed", test_build_content_prompt_feed)
    run_test(results, "tipo desconhecido", test_build_content_prompt_unknown)
    print()

    # Métodos auxiliares de formatação
    print("📦 Métodos auxiliares de formatação:")
    run_test(results, "format_creator_profile_section", test_format_creator_profile_section)
    run_test(results, "format_creator_profile_section com telefone", test_format_creator_profile_section_with_phone)
    run_test(results, "format_creator_profile_section sem telefone", test_format_creator_profile_section_without_phone)
    run_test(results, "format_post_data_section", test_format_post_data_section)
    run_test(results, "format_post_data_section sem detalhes", test_format_post_data_section_no_details)
    print()

    # CreatorProfile Model
    print("📦 CreatorProfile Model:")
    run_test(results, "criar perfil", test_creator_profile_create)
    run_test(results, "representação string", test_creator_profile_str)
    run_test(results, "validação de cor", test_creator_profile_color_validation)
    run_test(results, "validação de visual_style_ids", test_creator_profile_visual_style_ids_validation)
    run_test(results, "validação de telefone", test_creator_profile_phone_validation)
    run_test(results, "campos de onboarding", test_creator_profile_onboarding_fields)
    print()

    # VisualStylePreference Model
    print("📦 VisualStylePreference Model:")
    run_test(results, "criar estilo", test_visual_style_create)
    run_test(results, "representação string", test_visual_style_str)
    print()

    # _get_visual_style (novo - substitui _get_random_visual_style)
    print("📦 _get_visual_style (consistência, não aleatório):")
    run_test(results, "retorna primeiro por padrão", test_get_visual_style_returns_first_by_default)
    run_test(results, "aceita style_id específico", test_get_visual_style_with_specific_id)
    run_test(results, "múltiplas chamadas consistentes", test_get_visual_style_consistent_multiple_calls)
    run_test(results, "lista vazia retorna dict vazio", test_get_visual_style_empty_list)
    print()

    # semantic_analysis_prompt (novo)
    print("📦 semantic_analysis_prompt:")
    run_test(results, "inclui conteúdo textual", test_semantic_analysis_prompt_includes_content)
    run_test(results, "especifica formato JSON", test_semantic_analysis_prompt_json_format)
    print()

    # build_image_prompt_with_semantic (novo)
    print("📦 build_image_prompt_with_semantic:")
    run_test(results, "inclui dados da análise semântica", test_build_image_prompt_with_semantic_includes_analysis)
    run_test(results, "inclui seção de logo", test_build_image_prompt_with_semantic_includes_logo)
    print()

    # visual_style_id em post_data (novo)
    print("📦 visual_style_id em post_data:")
    run_test(results, "feed image respeita visual_style_id", test_feed_image_respects_visual_style_id)
    run_test(results, "get_creator_profile_data com style_id", test_get_creator_profile_data_with_style_id)

    success = results.summary()
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
