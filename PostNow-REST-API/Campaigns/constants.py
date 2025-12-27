"""
Constantes e configurações para Campanhas.
Define estruturas narrativas, fases, e configurações padrão.
"""

# Estruturas de Campanha Disponíveis
CAMPAIGN_STRUCTURES = {
    'aida': {
        'name': 'AIDA (Clássico)',
        'description': 'Framework de conversão testado: Atenção → Interesse → Desejo → Ação',
        'phases': [
            {
                'name': 'Atenção',
                'key': 'awareness',
                'weight': 0.25,
                'objective': 'awareness',
                'description': 'Capturar atenção com gancho forte'
            },
            {
                'name': 'Interesse',
                'key': 'interest',
                'weight': 0.25,
                'objective': 'engagement',
                'description': 'Desenvolver interesse no problema/solução'
            },
            {
                'name': 'Desejo',
                'key': 'desire',
                'weight': 0.30,
                'objective': 'branding',
                'description': 'Criar desejo através de benefícios e prova social'
            },
            {
                'name': 'Ação',
                'key': 'action',
                'weight': 0.20,
                'objective': 'sales',
                'description': 'Call-to-action claro e urgente'
            },
        ],
        'ideal_duration_days': 12,
        'min_duration_days': 7,
        'max_duration_days': 16,
        'ideal_posts': (8, 12),
        'posts_per_week': (3, 4),
        'best_for': ['sales', 'launch', 'branding', 'lead_generation'],
        'success_rate': 0.87,
        'sample_size': 340,
        'source': 'PostNow Internal Data 2024'
    },
    
    'pas': {
        'name': 'PAS (Problem-Agitate-Solve)',
        'description': 'Identificar dor, amplificar consequências, apresentar solução',
        'phases': [
            {
                'name': 'Problema',
                'key': 'problem',
                'weight': 0.30,
                'objective': 'awareness',
                'description': 'Identificar problema específico do público'
            },
            {
                'name': 'Agitação',
                'key': 'agitate',
                'weight': 0.30,
                'objective': 'engagement',
                'description': 'Amplificar consequências e urgência'
            },
            {
                'name': 'Solução',
                'key': 'solve',
                'weight': 0.40,
                'objective': 'sales',
                'description': 'Apresentar solução completa'
            },
        ],
        'ideal_duration_days': 8,
        'min_duration_days': 5,
        'max_duration_days': 12,
        'ideal_posts': (6, 10),
        'posts_per_week': (4, 5),
        'best_for': ['sales', 'problem_solving', 'services'],
        'success_rate': 0.72,
        'sample_size': 156,
        'source': 'PostNow Internal Data 2024'
    },
    
    'funil': {
        'name': 'Funil de Conteúdo',
        'description': 'Educar progressivamente do topo ao fundo do funil',
        'phases': [
            {
                'name': 'Topo do Funil',
                'key': 'top',
                'weight': 0.40,
                'objective': 'awareness',
                'description': 'Educação e awareness sobre problema'
            },
            {
                'name': 'Meio do Funil',
                'key': 'middle',
                'weight': 0.35,
                'objective': 'education',
                'description': 'Soluções e consideração'
            },
            {
                'name': 'Fundo do Funil',
                'key': 'bottom',
                'weight': 0.25,
                'objective': 'lead_generation',
                'description': 'Conversão e ação'
            },
        ],
        'ideal_duration_days': 18,
        'min_duration_days': 14,
        'max_duration_days': 21,
        'ideal_posts': (12, 16),
        'posts_per_week': (3, 4),
        'best_for': ['education', 'lead_generation', 'authority_building'],
        'success_rate': 0.81,
        'sample_size': 174,
        'source': 'PostNow Internal Data 2024'
    },
    
    'bab': {
        'name': 'Before-After-Bridge',
        'description': 'Mostrar transformação: Antes → Depois → Como chegar lá',
        'phases': [
            {
                'name': 'Before (Estado Atual)',
                'key': 'before',
                'weight': 0.30,
                'objective': 'awareness',
                'description': 'Estado problemático atual'
            },
            {
                'name': 'After (Estado Ideal)',
                'key': 'after',
                'weight': 0.30,
                'objective': 'branding',
                'description': 'Visão do estado desejado'
            },
            {
                'name': 'Bridge (Como Chegar)',
                'key': 'bridge',
                'weight': 0.40,
                'objective': 'sales',
                'description': 'Caminho/solução para transformação'
            },
        ],
        'ideal_duration_days': 10,
        'min_duration_days': 7,
        'max_duration_days': 14,
        'ideal_posts': (6, 10),
        'posts_per_week': (3, 4),
        'best_for': ['transformation', 'services', 'results_focused'],
        'success_rate': 0.76,
        'sample_size': 98,
        'source': 'PostNow Internal Data 2024'
    },
    
    'storytelling': {
        'name': 'Jornada do Herói',
        'description': 'Narrativa completa: Apresentação → Desafio → Superação → Transformação',
        'phases': [
            {
                'name': 'Mundo Comum',
                'key': 'ordinary_world',
                'weight': 0.15,
                'objective': 'awareness',
                'description': 'Como era antes, situação inicial'
            },
            {
                'name': 'Chamado e Desafios',
                'key': 'challenges',
                'weight': 0.35,
                'objective': 'engagement',
                'description': 'Problemas enfrentados, jornada'
            },
            {
                'name': 'Superação',
                'key': 'overcome',
                'weight': 0.30,
                'objective': 'education',
                'description': 'Como superou, aprendizados'
            },
            {
                'name': 'Transformação',
                'key': 'transformation',
                'weight': 0.20,
                'objective': 'branding',
                'description': 'Novo estado, convite ao público'
            },
        ],
        'ideal_duration_days': 16,
        'min_duration_days': 12,
        'max_duration_days': 21,
        'ideal_posts': (10, 14),
        'posts_per_week': (3, 4),
        'best_for': ['branding', 'personal_brand', 'storytelling'],
        'success_rate': 0.82,
        'sample_size': 145,
        'source': 'PostNow Internal Data 2024'
    },
    
    'simple': {
        'name': 'Sequência Simples',
        'description': 'Para iniciantes: Apresentação → Demonstração → Convite',
        'phases': [
            {
                'name': 'Apresentação',
                'key': 'introduction',
                'weight': 0.33,
                'objective': 'awareness',
                'description': 'Quem você é, o que faz'
            },
            {
                'name': 'Demonstração',
                'key': 'demonstration',
                'weight': 0.34,
                'objective': 'education',
                'description': 'Como você trabalha, valor que entrega'
            },
            {
                'name': 'Convite',
                'key': 'invitation',
                'weight': 0.33,
                'objective': 'engagement',
                'description': 'Como te contatar, próximos passos'
            },
        ],
        'ideal_duration_days': 14,
        'min_duration_days': 7,
        'max_duration_days': 21,
        'ideal_posts': (6, 8),
        'posts_per_week': (2, 3),
        'best_for': ['beginners', 'simple_campaigns', 'introduction'],
        'success_rate': 0.89,
        'sample_size': 234,
        'source': 'PostNow Internal Data 2024'
    },
}


# Configurações Padrão por Tipo de Campanha
CAMPAIGN_DEFAULTS = {
    'branding': {
        'recommended_structure': 'storytelling',
        'alternative_structures': ['aida', 'funil'],
        'duration_days': 16,
        'post_count': 12,
        'content_mix': {'feed': 0.50, 'reel': 0.30, 'story': 0.20},
    },
    'sales': {
        'recommended_structure': 'aida',
        'alternative_structures': ['pas', 'bab'],
        'duration_days': 10,
        'post_count': 8,
        'content_mix': {'feed': 0.30, 'reel': 0.50, 'story': 0.20},
    },
    'launch': {
        'recommended_structure': 'aida',
        'alternative_structures': ['bab', 'storytelling'],
        'duration_days': 12,
        'post_count': 10,
        'content_mix': {'feed': 0.40, 'reel': 0.40, 'story': 0.20},
    },
    'education': {
        'recommended_structure': 'funil',
        'alternative_structures': ['simple', 'storytelling'],
        'duration_days': 18,
        'post_count': 12,
        'content_mix': {'feed': 0.60, 'reel': 0.20, 'story': 0.20},
    },
    'engagement': {
        'recommended_structure': 'simple',
        'alternative_structures': ['storytelling'],
        'duration_days': 14,
        'post_count': 8,
        'content_mix': {'feed': 0.20, 'reel': 0.40, 'story': 0.40},
    },
    'lead_generation': {
        'recommended_structure': 'funil',
        'alternative_structures': ['aida', 'pas'],
        'duration_days': 14,
        'post_count': 10,
        'content_mix': {'feed': 0.40, 'reel': 0.40, 'story': 0.20},
    },
    'portfolio': {
        'recommended_structure': 'storytelling',
        'alternative_structures': ['simple'],
        'duration_days': 21,
        'post_count': 14,
        'content_mix': {'feed': 0.50, 'reel': 0.30, 'story': 0.20},
    },
}


# Perguntas Contextuais por Tipo de Campanha
CONTEXTUAL_QUESTIONS = {
    'sales': [
        {
            'key': 'has_offer',
            'question': 'Tem alguma oferta ou desconto específico?',
            'type': 'boolean',
            'follow_up': {
                'key': 'offer_details',
                'question': 'Qual o desconto/oferta?',
                'type': 'text',
                'placeholder': 'Ex: 50% OFF, Compre 2 Leve 3'
            }
        },
        {
            'key': 'featured_product',
            'question': 'Qual produto/serviço em destaque?',
            'type': 'text',
            'optional': True
        },
        {
            'key': 'urgency',
            'question': 'Tem prazo de validade?',
            'type': 'boolean',
            'follow_up': {
                'key': 'deadline',
                'question': 'Até quando?',
                'type': 'date'
            }
        },
    ],
    'branding': [
        {
            'key': 'brand_aspect',
            'question': 'Qual aspecto da marca quer reforçar?',
            'type': 'select',
            'options': ['Valores', 'História', 'Diferencial', 'Missão', 'Equipe'],
            'optional': True
        },
        {
            'key': 'recent_milestone',
            'question': 'Tem algum marco ou conquista recente para compartilhar?',
            'type': 'text',
            'optional': True
        },
    ],
    'launch': [
        {
            'key': 'launch_date',
            'question': 'Qual a data de lançamento?',
            'type': 'date',
            'required': True
        },
        {
            'key': 'has_materials',
            'question': 'Já tem materiais promocionais (fotos, vídeos)?',
            'type': 'boolean'
        },
        {
            'key': 'product_differential',
            'question': 'Qual o principal diferencial deste produto/serviço?',
            'type': 'text',
            'required': True
        },
    ],
    'education': [
        {
            'key': 'main_doubt',
            'question': 'Qual a principal dúvida do seu público que quer responder?',
            'type': 'text',
            'required': True
        },
        {
            'key': 'has_cases',
            'question': 'Tem cases ou exemplos práticos?',
            'type': 'boolean',
            'follow_up': {
                'key': 'cases_description',
                'question': 'Pode resumir 1-2 casos?',
                'type': 'textarea'
            }
        },
    ],
    'engagement': [
        {
            'key': 'engagement_type',
            'question': 'Quer fazer perguntas ao público ou criar discussão?',
            'type': 'select',
            'options': ['Perguntas', 'Enquetes', 'Desafios', 'Discussões']
        },
    ],
    'lead_generation': [
        {
            'key': 'lead_magnet',
            'question': 'Qual material vai oferecer?',
            'type': 'select',
            'options': ['Ebook', 'Consulta Gratuita', 'Diagnóstico', 'Webinar', 'Checklist'],
            'required': True
        },
        {
            'key': 'landing_page',
            'question': 'Já tem landing page pronta?',
            'type': 'boolean'
        },
    ],
    'portfolio': [
        {
            'key': 'projects_count',
            'question': 'Quantos projetos quer destacar?',
            'type': 'number',
            'min': 1,
            'max': 10
        },
        {
            'key': 'has_photos',
            'question': 'Tem fotos dos projetos?',
            'type': 'boolean',
            'required': True
        },
    ],
}


# Horários Padrão por Tipo de Conteúdo
DEFAULT_POSTING_TIMES = {
    'feed': ['09:00:00', '13:00:00', '18:00:00'],
    'reel': ['11:00:00', '18:00:00', '20:00:00'],
    'story': ['08:00:00', '12:00:00', '19:00:00', '21:00:00'],
}


# Dias da Semana Preferidos (distribuição)
PREFERRED_WEEKDAYS = {
    'branding': [0, 2, 4],  # Segunda, Quarta, Sexta
    'sales': [0, 2, 3, 5],  # Segunda, Quarta, Quinta, Sábado
    'education': [0, 2, 4],  # Segunda, Quarta, Sexta
    'engagement': [2, 3, 4, 6],  # Quarta, Quinta, Sexta, Domingo
}


# Validação de Qualidade (Thresholds)
QUALITY_THRESHOLDS = {
    'min_text_length': 50,
    'max_text_length': 400,
    'ideal_text_length': (150, 280),
    'min_contrast_score': 0.30,
    'ideal_contrast_score': (0.30, 0.70),
    'min_brand_consistency': 0.60,
    'min_harmony_score': 60,
    'ideal_harmony_score': 75,
}


# Estimativas de Custo (Créditos)
CAMPAIGN_COST_ESTIMATES = {
    'text_per_post': 0.02,  # R$ 0,02 por texto
    'image_per_post': 0.23,  # R$ 0,23 por imagem
}


def calculate_campaign_cost(post_count, include_images=True):
    """Calcula custo estimado de uma campanha."""
    text_cost = post_count * CAMPAIGN_COST_ESTIMATES['text_per_post']
    image_cost = post_count * CAMPAIGN_COST_ESTIMATES['image_per_post'] if include_images else 0
    return text_cost + image_cost

