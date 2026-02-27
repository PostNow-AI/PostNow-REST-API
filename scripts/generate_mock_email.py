#!/usr/bin/env python
"""
Script para gerar HTML mockado dos dois e-mails separados:
- Segunda: Oportunidades de Conteúdo (enriquecido)
- Quarta: Inteligência de Mercado

Uso: python scripts/generate_mock_email.py
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock dos dados enriquecidos (Fase 2) - SEGUNDA-FEIRA
MOCK_TENDENCIES_DATA = {
    'polemica': {
        'titulo': 'Polêmicas e Debates Quentes',
        'items': [
            {
                'titulo_ideia': 'IA substituindo designers: realidade ou exagero?',
                'descricao': 'O debate sobre ferramentas de IA como Midjourney e DALL-E está aquecido. Designers questionam se a tecnologia vai substituir profissionais ou ser apenas mais uma ferramenta.',
                'tipo': '🔥 Polêmica',
                'score': 92,
                'url_fonte': 'https://forbes.com.br/tecnologia/ia-design-debate',
                'enriched_sources': [
                    {'url': 'https://medium.com/design-ai-future', 'title': 'The Future of Design with AI'},
                    {'url': 'https://uxdesign.cc/ai-tools-designers', 'title': 'AI Tools Every Designer Should Know'},
                    {'url': 'https://techcrunch.com/ai-creative-industry', 'title': 'AI in Creative Industries: A Deep Dive'},
                ],
                'enriched_analysis': '''Contexto expandido: O debate ganhou força após grandes agências anunciarem redução de equipes criativas. Porém, estudos mostram que designers que dominam IA têm salários 40% maiores.

Ângulos de abordagem:
1. Mostrar casos de designers que aumentaram produtividade com IA
2. Discutir limites éticos do uso de IA em trabalhos criativos
3. Tutorial prático de como integrar IA no workflow sem perder autenticidade

Pontos de atenção: Evitar posicionamento extremista. O público valoriza visão equilibrada com exemplos práticos.'''
            },
            {
                'titulo_ideia': 'Trabalho remoto vs presencial: a guerra continua',
                'descricao': 'Grandes empresas estão forçando retorno ao escritório enquanto funcionários resistem. O tema gera engajamento garantido.',
                'tipo': '🔥 Polêmica',
                'score': 88,
                'url_fonte': 'https://exame.com/carreira/trabalho-remoto-debate',
                'enriched_sources': [
                    {'url': 'https://hbr.org/remote-work-productivity', 'title': 'Remote Work and Productivity: The Data'},
                    {'url': 'https://linkedin.com/pulse/future-work', 'title': 'Future of Work Trends 2026'},
                ],
                'enriched_analysis': '''Contexto expandido: Pesquisa recente mostra que 67% dos profissionais preferem modelo híbrido. Empresas que forçam retorno total estão perdendo talentos.

Ângulos de abordagem:
1. Compartilhar dados de produtividade em diferentes modelos
2. Entrevistar profissionais que mudaram de emprego por flexibilidade
3. Dicas para negociar modelo híbrido com gestores

Pontos de atenção: Tema polarizador - usar dados para embasar opinião.'''
            },
        ]
    },
    'educativo': {
        'titulo': 'Conteúdo Educativo em Alta',
        'items': [
            {
                'titulo_ideia': 'Como usar ChatGPT para criar conteúdo sem parecer genérico',
                'descricao': 'Tutorial prático mostrando técnicas avançadas de prompt engineering para criar conteúdo único e personalizado.',
                'tipo': '🧠 Educativo',
                'score': 95,
                'url_fonte': 'https://rockcontent.com/chatgpt-conteudo',
                'enriched_sources': [
                    {'url': 'https://openai.com/blog/prompt-engineering', 'title': 'Prompt Engineering Guide'},
                    {'url': 'https://learnprompting.org', 'title': 'Learn Prompting - Free Course'},
                    {'url': 'https://github.com/dair-ai/prompt-engineering-guide', 'title': 'Prompt Engineering Guide (GitHub)'},
                ],
                'enriched_analysis': '''Contexto expandido: 78% dos profissionais de marketing já usam IA, mas apenas 23% estão satisfeitos com os resultados. A diferença está na qualidade dos prompts.

Ângulos de abordagem:
1. Criar template de prompts para diferentes tipos de conteúdo
2. Mostrar antes/depois de textos gerados com prompts básicos vs avançados
3. Ensinar técnica de "persona + contexto + restrições"

Pontos de atenção: Incluir exemplos práticos e templates downloadable aumenta engajamento em 3x.'''
            },
        ]
    },
    'newsjacking': {
        'titulo': 'Oportunidades de Newsjacking',
        'items': [
            {
                'titulo_ideia': 'Oscar 2026: como marcas podem surfar a onda sem parecer forçadas',
                'descricao': 'O Oscar acontece em 2 semanas. Momento perfeito para criar conteúdo relacionado a filmes, moda e cultura pop.',
                'tipo': '📰 Newsjacking',
                'score': 91,
                'url_fonte': 'https://meioemensagem.com.br/oscar-marcas',
                'enriched_sources': [
                    {'url': 'https://adweek.com/oscars-marketing', 'title': 'How Brands Win at the Oscars'},
                    {'url': 'https://variety.com/oscars-predictions', 'title': 'Oscar 2026 Predictions'},
                ],
                'enriched_analysis': '''Contexto expandido: Posts relacionados ao Oscar têm 340% mais alcance na semana do evento. Melhor janela: 3 dias antes até 1 dia depois.

Ângulos de abordagem:
1. Criar paralelos entre filmes indicados e seu nicho
2. "O que [filme] ensina sobre [tema do seu negócio]"
3. Memes e referências culturais dos filmes

Pontos de atenção: Evitar spoilers e respeitar direitos autorais de imagens.'''
            }
        ]
    },
    'estudo_caso': {
        'titulo': 'Estudos de Caso Inspiradores',
        'items': [
            {
                'titulo_ideia': 'Como a Nubank conquistou 100M de clientes com conteúdo',
                'descricao': 'Análise da estratégia de conteúdo da Nubank que a tornou a maior fintech da América Latina.',
                'tipo': '💼 Estudo de Caso',
                'score': 93,
                'url_fonte': 'https://infomoney.com.br/nubank-estrategia',
                'enriched_sources': [
                    {'url': 'https://forbes.com/nubank-success-story', 'title': 'Nubank: The Success Story'},
                    {'url': 'https://techcrunch.com/nubank-content-strategy', 'title': 'Inside Nubank Content Strategy'},
                ],
                'enriched_analysis': '''Contexto expandido: Nubank investe 3x mais em conteúdo educativo que em publicidade tradicional. Taxa de retenção de clientes é 40% maior que concorrentes.

Ângulos de abordagem:
1. Decupar a estratégia em etapas replicáveis
2. Comparar com estratégias de concorrentes
3. Extrair lições aplicáveis a pequenos negócios

Pontos de atenção: Adaptar escala - mostrar como aplicar com orçamento menor.'''
            }
        ]
    },
}

# Mock dos dados de inteligência de mercado - QUARTA-FEIRA
MOCK_CONTEXT_DATA = {
    'market_panorama': 'O mercado de marketing digital brasileiro está em expansão acelerada, com investimentos previstos de R$ 35 bilhões em 2026. Pequenas e médias empresas estão aumentando orçamentos em redes sociais em 45% comparado ao ano anterior.',
    'market_tendencies': [
        'Vídeo curto continua dominando (TikTok, Reels, Shorts)',
        'IA generativa integrada em ferramentas de marketing',
        'Busca por autenticidade e conteúdo "imperfeito"',
        'Crescimento do social commerce'
    ],
    'market_challenges': [
        'Saturação de conteúdo nas principais plataformas',
        'Mudanças constantes nos algoritmos',
        'Aumento do custo de mídia paga',
        'Dificuldade em medir ROI de conteúdo orgânico'
    ],
    'market_sources': [
        'https://forbes.com.br/marketing-digital-2026',
        'https://meioemensagem.com.br/tendencias'
    ],
    'competition_main': ['Concorrente A', 'Concorrente B', 'Concorrente C'],
    'competition_strategies': 'Concorrentes estão investindo fortemente em vídeo marketing e parcerias com micro-influenciadores. Nota-se uma tendência de humanização das marcas através de conteúdo behind-the-scenes.',
    'competition_opportunities': 'Há uma lacuna no mercado para conteúdo educativo aprofundado. Concorrentes focam em entretenimento rápido, deixando espaço para quem quer se posicionar como autoridade.',
    'competition_sources': [
        'https://similarweb.com/analysis',
        'https://semrush.com/competitive-research'
    ],
    'target_audience_profile': 'Empreendedores e profissionais de marketing entre 25-45 anos, majoritariamente em capitais brasileiras, com interesse em crescimento profissional e otimização de tempo.',
    'target_audience_behaviors': 'Consumo de conteúdo predominantemente via mobile, em horários de deslocamento (7-9h, 18-20h). Preferência por conteúdo prático e aplicável imediatamente.',
    'target_audience_interests': ['Produtividade', 'Marketing Digital', 'Empreendedorismo', 'Tecnologia', 'Desenvolvimento Pessoal'],
    'target_audience_sources': [
        'https://thinkwithgoogle.com/consumer-insights'
    ],
    'tendencies_popular_themes': ['IA no Marketing', 'Automação', 'Personal Branding', 'Vídeo Marketing'],
    'tendencies_hashtags': ['#MarketingDigital', '#Empreendedorismo', '#IAnoMarketing', '#ContentCreator', '#SocialMedia'],
    'tendencies_keywords': ['inteligência artificial', 'automação marketing', 'criar conteúdo', 'engajamento redes sociais'],
    'tendencies_sources': [
        'https://trends.google.com',
        'https://sparktoro.com/trending'
    ],
    'brand_online_presence': 'Presença consolidada no Instagram e LinkedIn, com crescimento orgânico consistente. Oportunidade de expansão para TikTok e YouTube Shorts.',
    'brand_reputation': 'Percepção positiva como fonte confiável de informação. Alta taxa de recomendação entre seguidores.',
    'brand_communication_style': 'Tom educativo e acessível, equilibrando profundidade técnica com linguagem clara.',
    'brand_sources': [
        'https://mention.com/brand-monitoring'
    ],
    'seasonal_relevant_dates': [
        '08/05 - Dia do Profissional de Marketing',
        '11/05 - Dia das Mães',
        'Maio - Semana do Empreendedor'
    ],
    'seasonal_local_events': [
        'RD Summit (Florianópolis - Outubro)',
        'Social Media Week SP (Junho)'
    ],
    'seasonal_sources': [],
}

MOCK_USER_DATA = {
    'business_name': 'PostNow Marketing Digital',
    'user_name': 'Maria',
    'user__first_name': 'Maria'
}


def main():
    # Set environment variable for frontend URL
    os.environ.setdefault('FRONTEND_URL', 'https://app.postnow.com.br')

    # Import after setting up path
    from ClientContext.utils.opportunities_email import generate_opportunities_email_template
    from ClientContext.utils.weekly_context import generate_weekly_context_email_template

    output_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Generate MONDAY email (Opportunities)
    monday_html = generate_opportunities_email_template(MOCK_TENDENCIES_DATA, MOCK_USER_DATA)
    monday_path = os.path.join(output_dir, 'mock_email_monday_opportunities.html')
    with open(monday_path, 'w', encoding='utf-8') as f:
        f.write(monday_html)
    print(f"✅ Segunda-feira (Oportunidades): {monday_path}")

    # Generate WEDNESDAY email (Market Intelligence)
    wednesday_html = generate_weekly_context_email_template(MOCK_CONTEXT_DATA, MOCK_USER_DATA)
    wednesday_path = os.path.join(output_dir, 'mock_email_wednesday_market_intelligence.html')
    with open(wednesday_path, 'w', encoding='utf-8') as f:
        f.write(wednesday_html)
    print(f"✅ Quarta-feira (Inteligência de Mercado): {wednesday_path}")

    print(f"\n📧 Dois e-mails gerados com sucesso!")
    print(f"\nPara visualizar:")
    print(f"  open {monday_path}")
    print(f"  open {wednesday_path}")


if __name__ == '__main__':
    main()
