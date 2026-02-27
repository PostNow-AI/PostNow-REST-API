#!/usr/bin/env python
"""
Mockup de proposta visual unificada para os dois e-mails.
"""

import os

# Estilo unificado
UNIFIED_STYLES = {
    'primary_color': '#8b5cf6',  # Roxo PostNow
    'secondary_color': '#6366f1',  # Índigo
    'dark_bg': '#0f172a',  # Header escuro
    'light_bg': '#f8fafc',  # Fundo claro
    'card_bg': '#ffffff',
    'text_primary': '#1e293b',
    'text_secondary': '#475569',
    'text_muted': '#64748b',
    'border_color': '#e2e8f0',
}

def generate_unified_header(title: str, subtitle: str, emoji: str) -> str:
    """Header unificado para ambos os e-mails."""
    return f'''
    <tr>
        <td style="background: linear-gradient(135deg, {UNIFIED_STYLES['dark_bg']} 0%, #1e293b 100%); padding: 32px; text-align: center;">
            <img src="https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/postnow_logo_white.png" alt="PostNow Logo" style="width: 114px; height: 32px; margin-bottom: 16px;">
            <h1 style="margin: 0; color: {UNIFIED_STYLES['primary_color']}; font-size: 22px; font-weight: 700;">
                {emoji} {title}
            </h1>
            <p style="margin: 8px 0 0 0; color: #94a3b8; font-size: 14px;">
                {subtitle}
            </p>
        </td>
    </tr>
    '''

def generate_unified_footer(next_email_info: str) -> str:
    """Footer unificado para ambos os e-mails."""
    return f'''
    <tr>
        <td style="padding: 24px; background-color: {UNIFIED_STYLES['light_bg']}; border-top: 1px solid {UNIFIED_STYLES['border_color']}; text-align: center;">
            <p style="margin: 0 0 8px 0; color: {UNIFIED_STYLES['text_muted']}; font-size: 12px;">
                {next_email_info}
            </p>
            <p style="margin: 0; color: #94a3b8; font-size: 11px;">
                © 2025 PostNow. Transformando dados em conteúdo.
            </p>
        </td>
    </tr>
    '''

def generate_unified_cta(text: str, button_text: str, url: str) -> str:
    """CTA unificado para ambos os e-mails."""
    return f'''
    <table role="presentation" style="width: 100%; background: linear-gradient(135deg, {UNIFIED_STYLES['secondary_color']} 0%, {UNIFIED_STYLES['primary_color']} 100%); border-radius: 12px; margin-top: 24px;">
        <tr>
            <td style="padding: 24px; text-align: center;">
                <p style="margin: 0 0 12px 0; color: rgba(255,255,255,0.9); font-size: 15px;">
                    {text}
                </p>
                <a href="{url}" style="display: inline-block; background-color: #ffffff; color: {UNIFIED_STYLES['primary_color']}; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px;">
                    {button_text}
                </a>
            </td>
        </tr>
    </table>
    '''

def generate_section_card(title: str, emoji: str, color: str, content: str) -> str:
    """Card de seção unificado."""
    return f'''
    <table role="presentation" style="width: 100%; margin-bottom: 20px; border: 1px solid {UNIFIED_STYLES['border_color']}; border-radius: 12px; overflow: hidden;">
        <tr>
            <td style="background-color: {color}; padding: 14px 20px;">
                <h3 style="margin: 0; color: white; font-size: 16px; font-weight: 600;">{emoji} {title}</h3>
            </td>
        </tr>
        <tr>
            <td style="padding: 20px; background-color: {UNIFIED_STYLES['card_bg']};">
                {content}
            </td>
        </tr>
    </table>
    '''

def generate_opportunity_item(item: dict, colors: dict, index: int) -> str:
    """Item de oportunidade formatado."""
    titulo = item.get('titulo_ideia', '')
    descricao = item.get('descricao', '')
    score = item.get('score', 0)
    url_fonte = item.get('url_fonte', '')
    enriched_sources = item.get('enriched_sources', [])
    enriched_analysis = item.get('enriched_analysis', '')

    separator = 'border-top: 1px solid #e5e7eb; padding-top: 16px; margin-top: 16px;' if index > 0 else ''

    sources_html = ''
    if url_fonte:
        sources_html += f'<a href="{url_fonte}" target="_blank" style="display: inline-block; background-color: {UNIFIED_STYLES["light_bg"]}; color: #3b82f6; padding: 4px 10px; border-radius: 4px; font-size: 11px; text-decoration: none; margin-right: 6px; margin-bottom: 6px;">Fonte principal</a>'

    for j, source in enumerate(enriched_sources[:3]):
        source_url = source.get('url', '')
        source_title = source.get('title', f'Fonte {j + 2}')
        if len(source_title) > 25:
            source_title = source_title[:22] + '...'
        if source_url:
            sources_html += f'<a href="{source_url}" target="_blank" style="display: inline-block; background-color: {UNIFIED_STYLES["light_bg"]}; color: #3b82f6; padding: 4px 10px; border-radius: 4px; font-size: 11px; text-decoration: none; margin-right: 6px; margin-bottom: 6px;">{source_title}</a>'

    analysis_html = ''
    if enriched_analysis:
        analysis_html = f'''
        <div style="background-color: {UNIFIED_STYLES['light_bg']}; border-left: 3px solid {colors['border']}; padding: 12px; margin: 12px 0; border-radius: 0 6px 6px 0;">
            <p style="margin: 0 0 4px 0; color: {colors['text']}; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">💡 Análise</p>
            <p style="margin: 0; color: {UNIFIED_STYLES['text_secondary']}; font-size: 13px; line-height: 1.5; white-space: pre-line;">{enriched_analysis}</p>
        </div>
        '''

    return f'''
    <div style="{separator}">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
            <h4 style="margin: 0; color: {UNIFIED_STYLES['text_primary']}; font-size: 15px; font-weight: 600; flex: 1; line-height: 1.4;">{titulo}</h4>
            <span style="background-color: {colors['border']}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; margin-left: 12px; white-space: nowrap;">Score {score}</span>
        </div>
        <p style="margin: 0 0 12px 0; color: {UNIFIED_STYLES['text_secondary']}; font-size: 14px; line-height: 1.5;">{descricao}</p>
        {analysis_html}
        <div style="margin-top: 10px;">
            {sources_html}
        </div>
    </div>
    '''

def generate_monday_email(tendencies_data: dict, user_data: dict) -> str:
    """E-mail de Segunda - Oportunidades (estilo unificado)."""
    business_name = user_data.get('business_name', 'Sua Empresa')
    user_name = user_data.get('user_name', 'Usuário')
    frontend_url = os.getenv('FRONTEND_URL', 'https://app.postnow.com.br')

    category_colors = {
        'polemica': {'bg': '#fef2f2', 'border': '#ef4444', 'text': '#dc2626', 'emoji': '🔥'},
        'educativo': {'bg': '#f0fdf4', 'border': '#22c55e', 'text': '#16a34a', 'emoji': '🧠'},
        'newsjacking': {'bg': '#fefce8', 'border': '#eab308', 'text': '#ca8a04', 'emoji': '📰'},
        'entretenimento': {'bg': '#fdf4ff', 'border': '#d946ef', 'text': '#c026d3', 'emoji': '😂'},
        'estudo_caso': {'bg': '#eff6ff', 'border': '#3b82f6', 'text': '#2563eb', 'emoji': '💼'},
        'futuro': {'bg': '#f5f3ff', 'border': '#8b5cf6', 'text': '#7c3aed', 'emoji': '🔮'},
        'outros': {'bg': '#f8fafc', 'border': '#64748b', 'text': '#475569', 'emoji': '⚡'},
    }

    opportunities_html = ''
    for category_key, category_data in tendencies_data.items():
        if not isinstance(category_data, dict):
            continue
        titulo = category_data.get('titulo', '')
        items = category_data.get('items', [])
        if not items:
            continue

        colors = category_colors.get(category_key, category_colors['outros'])

        items_html = ''
        for i, item in enumerate(items[:3]):
            items_html += generate_opportunity_item(item, colors, i)

        opportunities_html += f'''
        <table role="presentation" style="width: 100%; margin-bottom: 20px; border: 1px solid {colors['border']}20; border-radius: 12px; overflow: hidden;">
            <tr>
                <td style="background-color: {colors['border']}; padding: 12px 16px;">
                    <h3 style="margin: 0; color: white; font-size: 15px; font-weight: 600;">{colors['emoji']} {titulo}</h3>
                </td>
            </tr>
            <tr>
                <td style="padding: 16px; background-color: {colors['bg']}15;">
                    {items_html}
                </td>
            </tr>
        </table>
        '''

    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PostNow - Oportunidades de Conteúdo</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: {UNIFIED_STYLES['light_bg']};">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 20px;">
                <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: {UNIFIED_STYLES['card_bg']}; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">

                    {generate_unified_header('Oportunidades de Conteúdo', f'Ideias ranqueadas para {business_name}', '🎯')}

                    <tr>
                        <td style="padding: 24px;">
                            <p style="margin: 0 0 20px 0; color: {UNIFIED_STYLES['text_secondary']}; font-size: 15px; line-height: 1.6;">
                                Olá, <strong>{user_name}</strong>! Preparamos as <strong>melhores oportunidades</strong> da semana,
                                cada uma com análise aprofundada e fontes extras.
                            </p>

                            {opportunities_html}

                            {generate_unified_cta('Pronto para transformar essas ideias em posts?', 'Criar Conteúdo', frontend_url)}
                        </td>
                    </tr>

                    {generate_unified_footer('📬 Toda <strong>segunda-feira</strong> você recebe oportunidades. Na <strong>quarta</strong>, inteligência de mercado.')}

                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''

def generate_wednesday_email(context_data: dict, user_data: dict) -> str:
    """E-mail de Quarta - Inteligência de Mercado (estilo unificado)."""
    business_name = user_data.get('business_name', 'Sua Empresa')
    user_name = user_data.get('user_name', 'Usuário')
    frontend_url = os.getenv('FRONTEND_URL', 'https://app.postnow.com.br')

    # Market section
    market_content = f'''
    <p style="margin: 0 0 16px 0; color: {UNIFIED_STYLES['text_secondary']}; font-size: 14px; line-height: 1.6;">
        {context_data.get('market_panorama', 'Dados do mercado não disponíveis.')}
    </p>
    '''

    tendencias = context_data.get('market_tendencies', [])
    if tendencias:
        market_content += f'<p style="margin: 0 0 8px 0; color: {UNIFIED_STYLES["text_primary"]}; font-size: 13px; font-weight: 600;">📈 Tendências:</p><ul style="margin: 0 0 16px 0; padding-left: 20px; color: {UNIFIED_STYLES["text_secondary"]}; font-size: 13px; line-height: 1.6;">'
        for t in tendencias:
            market_content += f'<li style="margin-bottom: 4px;">{t}</li>'
        market_content += '</ul>'

    desafios = context_data.get('market_challenges', [])
    if desafios:
        market_content += f'<p style="margin: 0 0 8px 0; color: {UNIFIED_STYLES["text_primary"]}; font-size: 13px; font-weight: 600;">⚠️ Desafios:</p><ul style="margin: 0; padding-left: 20px; color: {UNIFIED_STYLES["text_secondary"]}; font-size: 13px; line-height: 1.6;">'
        for d in desafios:
            market_content += f'<li style="margin-bottom: 4px;">{d}</li>'
        market_content += '</ul>'

    # Competition section
    competition_content = ''
    principais = context_data.get('competition_main', [])
    if principais:
        competition_content += '<div style="margin-bottom: 12px;">'
        for p in principais:
            competition_content += f'<span style="display: inline-block; background-color: {UNIFIED_STYLES["light_bg"]}; color: {UNIFIED_STYLES["text_secondary"]}; padding: 4px 12px; border-radius: 16px; font-size: 12px; margin-right: 6px; margin-bottom: 6px;">{p}</span>'
        competition_content += '</div>'

    competition_content += f'''
    <p style="margin: 0 0 12px 0; color: {UNIFIED_STYLES['text_secondary']}; font-size: 14px; line-height: 1.6;">
        <strong>Estratégias:</strong> {context_data.get('competition_strategies', 'Não disponível.')}
    </p>
    <div style="background-color: #f0fdf4; border-left: 3px solid #22c55e; padding: 12px; border-radius: 0 6px 6px 0;">
        <p style="margin: 0; color: #166534; font-size: 13px; line-height: 1.5;">
            <strong>💡 Oportunidade:</strong> {context_data.get('competition_opportunities', 'Não disponível.')}
        </p>
    </div>
    '''

    # Audience section
    audience_content = f'''
    <p style="margin: 0 0 12px 0; color: {UNIFIED_STYLES['text_secondary']}; font-size: 14px; line-height: 1.6;">
        <strong>Perfil:</strong> {context_data.get('target_audience_profile', 'Não disponível.')}
    </p>
    <p style="margin: 0 0 12px 0; color: {UNIFIED_STYLES['text_secondary']}; font-size: 14px; line-height: 1.6;">
        <strong>Comportamento:</strong> {context_data.get('target_audience_behaviors', 'Não disponível.')}
    </p>
    '''
    interesses = context_data.get('target_audience_interests', [])
    if interesses:
        audience_content += '<div>'
        for i in interesses:
            audience_content += f'<span style="display: inline-block; background-color: #fff7ed; color: #c2410c; padding: 4px 12px; border-radius: 16px; font-size: 12px; margin-right: 6px; margin-bottom: 6px;">{i}</span>'
        audience_content += '</div>'

    # Trends section
    trends_content = ''
    temas = context_data.get('tendencies_popular_themes', [])
    if temas:
        trends_content += '<div style="margin-bottom: 12px;">'
        for t in temas:
            trends_content += f'<span style="display: inline-block; background-color: #f3e8ff; color: #7c3aed; padding: 6px 14px; border-radius: 16px; font-size: 13px; font-weight: 500; margin-right: 6px; margin-bottom: 6px;">{t}</span>'
        trends_content += '</div>'

    hashtags = context_data.get('tendencies_hashtags', [])
    if hashtags:
        trends_content += f'<p style="margin: 12px 0 8px 0; color: {UNIFIED_STYLES["text_primary"]}; font-size: 13px; font-weight: 600;"># Hashtags em Alta:</p><div>'
        for h in hashtags:
            trends_content += f'<span style="display: inline-block; background-color: #dbeafe; color: #1e40af; padding: 4px 10px; border-radius: 16px; font-size: 12px; font-family: monospace; margin-right: 6px; margin-bottom: 6px;">{h}</span>'
        trends_content += '</div>'

    # Calendar section
    calendar_content = ''
    datas = context_data.get('seasonal_relevant_dates', [])
    if datas:
        calendar_content += f'<p style="margin: 0 0 8px 0; color: {UNIFIED_STYLES["text_primary"]}; font-size: 13px; font-weight: 600;">📆 Datas Importantes:</p><ul style="margin: 0 0 12px 0; padding-left: 20px; color: {UNIFIED_STYLES["text_secondary"]}; font-size: 13px; line-height: 1.6;">'
        for d in datas:
            calendar_content += f'<li style="margin-bottom: 4px;">{d}</li>'
        calendar_content += '</ul>'

    eventos = context_data.get('seasonal_local_events', [])
    if eventos:
        calendar_content += f'<p style="margin: 0 0 8px 0; color: {UNIFIED_STYLES["text_primary"]}; font-size: 13px; font-weight: 600;">🎪 Eventos:</p><ul style="margin: 0; padding-left: 20px; color: {UNIFIED_STYLES["text_secondary"]}; font-size: 13px; line-height: 1.6;">'
        for e in eventos:
            calendar_content += f'<li style="margin-bottom: 4px;">{e}</li>'
        calendar_content += '</ul>'

    if not calendar_content:
        calendar_content = f'<p style="margin: 0; color: {UNIFIED_STYLES["text_muted"]}; font-size: 14px;">Nenhum evento relevante identificado esta semana.</p>'

    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PostNow - Inteligência de Mercado</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: {UNIFIED_STYLES['light_bg']};">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 20px;">
                <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: {UNIFIED_STYLES['card_bg']}; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">

                    {generate_unified_header('Inteligência de Mercado', f'Insights semanais para {business_name}', '📊')}

                    <tr>
                        <td style="padding: 24px;">
                            <p style="margin: 0 0 20px 0; color: {UNIFIED_STYLES['text_secondary']}; font-size: 15px; line-height: 1.6;">
                                Olá, <strong>{user_name}</strong>! Aqui está seu resumo semanal com as principais tendências
                                e insights do mercado.
                            </p>

                            {generate_section_card('Panorama do Mercado', '🏢', UNIFIED_STYLES['primary_color'], market_content)}

                            {generate_section_card('Análise da Concorrência', '🎯', '#059669', competition_content)}

                            {generate_section_card('Insights do Público', '👥', '#ea580c', audience_content)}

                            {generate_section_card('Tendências da Semana', '🔥', '#7c3aed', trends_content)}

                            {generate_section_card('Calendário Estratégico', '📅', '#be185d', calendar_content)}

                            {generate_unified_cta('Use esses insights para criar conteúdo que conecta', 'Acessar Dashboard', frontend_url)}
                        </td>
                    </tr>

                    {generate_unified_footer('📬 Toda <strong>quarta-feira</strong> você recebe inteligência de mercado. Na <strong>segunda</strong>, oportunidades de conteúdo.')}

                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''


# Mock data
MOCK_TENDENCIES = {
    'polemica': {
        'titulo': 'Polêmicas e Debates',
        'items': [
            {
                'titulo_ideia': 'IA substituindo designers: realidade ou exagero?',
                'descricao': 'O debate sobre ferramentas de IA está aquecido. Designers questionam se a tecnologia vai substituir profissionais.',
                'score': 92,
                'url_fonte': 'https://forbes.com.br/tecnologia/ia-design',
                'enriched_sources': [
                    {'url': 'https://medium.com/design-ai', 'title': 'The Future of Design with AI'},
                    {'url': 'https://uxdesign.cc/ai-tools', 'title': 'AI Tools for Designers'},
                ],
                'enriched_analysis': '''Contexto: O debate ganhou força após grandes agências anunciarem redução de equipes. Designers que dominam IA têm salários 40% maiores.

Ângulos sugeridos:
1. Cases de designers que aumentaram produtividade
2. Limites éticos do uso de IA em trabalhos criativos
3. Tutorial de integração de IA no workflow'''
            },
        ]
    },
    'educativo': {
        'titulo': 'Conteúdo Educativo',
        'items': [
            {
                'titulo_ideia': 'Como usar ChatGPT para criar conteúdo único',
                'descricao': 'Técnicas avançadas de prompt engineering para criar conteúdo personalizado.',
                'score': 95,
                'url_fonte': 'https://rockcontent.com/chatgpt',
                'enriched_sources': [
                    {'url': 'https://openai.com/prompt-guide', 'title': 'Prompt Engineering Guide'},
                ],
                'enriched_analysis': '''78% dos profissionais usam IA, mas apenas 23% estão satisfeitos. A diferença está nos prompts.

Sugestões:
1. Templates de prompts para diferentes conteúdos
2. Antes/depois com prompts básicos vs avançados'''
            },
        ]
    },
}

MOCK_CONTEXT = {
    'market_panorama': 'O mercado de marketing digital brasileiro está em expansão, com investimentos de R$ 35 bilhões previstos para 2026. PMEs aumentam orçamentos em redes sociais em 45%.',
    'market_tendencies': ['Vídeo curto dominando', 'IA generativa em marketing', 'Busca por autenticidade', 'Social commerce em alta'],
    'market_challenges': ['Saturação de conteúdo', 'Mudanças em algoritmos', 'Custo de mídia paga', 'Medir ROI orgânico'],
    'competition_main': ['Concorrente A', 'Concorrente B', 'Concorrente C'],
    'competition_strategies': 'Investimento em vídeo marketing e parcerias com micro-influenciadores. Tendência de humanização através de conteúdo behind-the-scenes.',
    'competition_opportunities': 'Lacuna no mercado para conteúdo educativo aprofundado. Espaço para se posicionar como autoridade.',
    'target_audience_profile': 'Empreendedores e profissionais de marketing, 25-45 anos, capitais brasileiras.',
    'target_audience_behaviors': 'Consumo via mobile, horários de deslocamento. Preferência por conteúdo prático.',
    'target_audience_interests': ['Produtividade', 'Marketing Digital', 'Empreendedorismo', 'Tecnologia'],
    'tendencies_popular_themes': ['IA no Marketing', 'Automação', 'Personal Branding', 'Vídeo Marketing'],
    'tendencies_hashtags': ['#MarketingDigital', '#Empreendedorismo', '#IAnoMarketing', '#ContentCreator'],
    'seasonal_relevant_dates': ['08/05 - Dia do Profissional de Marketing', '11/05 - Dia das Mães'],
    'seasonal_local_events': ['RD Summit (Outubro)', 'Social Media Week SP (Junho)'],
}

MOCK_USER = {
    'business_name': 'PostNow Marketing',
    'user_name': 'Maria',
}


def main():
    os.environ.setdefault('FRONTEND_URL', 'https://app.postnow.com.br')

    output_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Generate unified Monday email
    monday_html = generate_monday_email(MOCK_TENDENCIES, MOCK_USER)
    monday_path = os.path.join(output_dir, 'mockup_unified_monday.html')
    with open(monday_path, 'w', encoding='utf-8') as f:
        f.write(monday_html)
    print(f"✅ Segunda (Proposta Unificada): {monday_path}")

    # Generate unified Wednesday email
    wednesday_html = generate_wednesday_email(MOCK_CONTEXT, MOCK_USER)
    wednesday_path = os.path.join(output_dir, 'mockup_unified_wednesday.html')
    with open(wednesday_path, 'w', encoding='utf-8') as f:
        f.write(wednesday_html)
    print(f"✅ Quarta (Proposta Unificada): {wednesday_path}")

    print(f"\n🎨 Mockups unificados gerados!")
    print(f"\nPara visualizar:")
    print(f"  open {monday_path}")
    print(f"  open {wednesday_path}")


if __name__ == '__main__':
    main()
