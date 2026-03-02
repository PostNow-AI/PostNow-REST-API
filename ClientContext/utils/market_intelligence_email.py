"""
Template de e-mail para Inteligência de Mercado (Quarta-feira).

Este é um template SEPARADO do weekly_context.py.
"""
import html
import os


def _escape(text) -> str:
    """Sanitiza texto para prevenir XSS."""
    if text is None:
        return ''
    return html.escape(str(text))


def generate_market_intelligence_email(context_data: dict, user_data: dict) -> str:
    """
    Gera o HTML do e-mail de Inteligência de Mercado.

    Args:
        context_data: Dados do contexto (mercado, concorrência, público, etc.)
        user_data: Dados do usuário (nome, business_name, etc.)

    Returns:
        HTML do e-mail
    """
    # Sanitizar dados do usuário para prevenir XSS
    user_name = _escape(user_data.get('user_name', user_data.get('user__first_name', 'Usuário')))
    business_name = _escape(user_data.get('business_name', 'Sua Empresa'))
    frontend_url = os.getenv('FRONTEND_URL', 'https://app.postnow.com.br')

    # Extrair e sanitizar dados para prevenir XSS
    market_panorama = _escape(context_data.get('market_panorama', ''))
    market_tendencies = [_escape(t) for t in (context_data.get('market_tendencies') or [])]
    market_challenges = [_escape(c) for c in (context_data.get('market_challenges') or [])]

    competition_main = context_data.get('competition_main', [])  # Sanitizado em _format_competitor
    competition_strategies = _escape(context_data.get('competition_strategies', ''))
    competition_opportunities = _escape(context_data.get('competition_opportunities', ''))

    audience_profile = _escape(context_data.get('target_audience_profile', ''))
    audience_behaviors = _escape(context_data.get('target_audience_behaviors', ''))
    audience_interests = [_escape(i) for i in (context_data.get('target_audience_interests') or [])]

    popular_themes = [_escape(t) for t in (context_data.get('tendencies_popular_themes') or [])]
    hashtags = [_escape(h) for h in (context_data.get('tendencies_hashtags') or [])]
    keywords = [_escape(k) for k in (context_data.get('tendencies_keywords') or [])]

    relevant_dates = context_data.get('seasonal_relevant_dates', [])  # Sanitizado em _format_date
    local_events = context_data.get('seasonal_local_events', [])  # Sanitizado em _format_date

    brand_presence = _escape(context_data.get('brand_online_presence', ''))
    brand_reputation = _escape(context_data.get('brand_reputation', ''))
    brand_style = _escape(context_data.get('brand_communication_style', ''))

    # Extrair fontes enriquecidas
    market_sources = context_data.get('market_sources', [])
    competition_sources = context_data.get('competition_sources', [])
    audience_sources = context_data.get('target_audience_sources', [])
    trends_sources = context_data.get('tendencies_sources', [])
    seasonal_sources = context_data.get('seasonal_sources', [])
    brand_sources = context_data.get('brand_sources', [])

    # Gerar seções com fontes
    market_section = _generate_market_section(market_panorama, market_tendencies, market_challenges, market_sources)
    competition_section = _generate_competition_section(competition_main, competition_strategies, competition_opportunities, competition_sources)
    audience_section = _generate_audience_section(audience_profile, audience_behaviors, audience_interests, audience_sources)
    trends_section = _generate_trends_section(popular_themes, hashtags, keywords, trends_sources)
    calendar_section = _generate_calendar_section(relevant_dates, local_events, seasonal_sources)
    brand_section = _generate_brand_section(brand_presence, brand_reputation, brand_style, brand_sources)

    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PostNow - Inteligência de Mercado</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f8fafc;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 20px;">
                <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">

                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 32px; text-align: center;">
                            <img src="https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/postnow_logo_white.png" alt="PostNow Logo" style="width: 114px; height: 32px; margin-bottom: 16px;">
                            <h1 style="margin: 0; color: #8b5cf6; font-size: 22px; font-weight: 700;">
                                Inteligência de Mercado
                            </h1>
                            <p style="margin: 8px 0 0 0; color: #94a3b8; font-size: 14px;">
                                Insights semanais para {business_name}
                            </p>
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td style="padding: 24px;">
                            <p style="margin: 0 0 20px 0; color: #475569; font-size: 15px; line-height: 1.6;">
                                Olá, <strong>{user_name}</strong>! Aqui está seu resumo semanal com as principais tendências
                                e insights do mercado.
                            </p>

                            {market_section}
                            {competition_section}
                            {audience_section}
                            {trends_section}
                            {calendar_section}
                            {brand_section}

                            <!-- CTA -->
                            <table role="presentation" style="width: 100%; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); border-radius: 12px; margin-top: 24px;">
                                <tr>
                                    <td style="padding: 24px; text-align: center;">
                                        <p style="margin: 0 0 12px 0; color: rgba(255,255,255,0.9); font-size: 15px;">
                                            Use esses insights para criar conteúdo que conecta
                                        </p>
                                        <a href="{frontend_url}" style="display: inline-block; background-color: #ffffff; color: #8b5cf6; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px;">
                                            Acessar Dashboard
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px; background-color: #f8fafc; border-top: 1px solid #e2e8f0; text-align: center;">
                            <p style="margin: 0 0 8px 0; color: #64748b; font-size: 12px;">
                                Toda <strong>quarta-feira</strong> você recebe inteligência de mercado. Na <strong>segunda</strong>, oportunidades de conteúdo.
                            </p>
                            <p style="margin: 0; color: #94a3b8; font-size: 11px;">
                                © 2025 PostNow. Transformando dados em conteúdo.
                            </p>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''

    return html


def _generate_sources_html(sources: list, max_sources: int = 3) -> str:
    """Gera HTML compacto para lista de fontes."""
    if not sources:
        return ''

    # Limitar número de fontes e extrair URLs
    urls = []
    for source in sources[:max_sources]:
        if isinstance(source, str):
            urls.append(source)
        elif isinstance(source, dict):
            urls.append(source.get('url', ''))

    if not urls:
        return ''

    links = ' • '.join([
        f'<a href="{url}" style="color: #6366f1; text-decoration: none; font-size: 11px;">{_extract_domain(url)}</a>'
        for url in urls if url
    ])

    return f'''
        <div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid #e2e8f0;">
            <span style="color: #94a3b8; font-size: 11px;">Fontes: </span>{links}
        </div>'''


def _extract_domain(url: str) -> str:
    """Extrai o domínio de uma URL para exibição."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        return domain[:25] + '...' if len(domain) > 25 else domain
    except Exception:
        return url[:25] + '...' if len(url) > 25 else url


def _generate_market_section(panorama: str, tendencies: list, challenges: list, sources: list = None) -> str:
    """Gera a seção Panorama do Mercado."""
    if not panorama and not tendencies and not challenges:
        return ''

    tendencies_html = ''
    if tendencies:
        items = ''.join([f'<li style="margin-bottom: 4px;">{t}</li>' for t in tendencies])
        tendencies_html = f'''
            <p style="margin: 0 0 8px 0; color: #1e293b; font-size: 13px; font-weight: 600;">Tendências:</p>
            <ul style="margin: 0 0 16px 0; padding-left: 20px; color: #475569; font-size: 13px; line-height: 1.6;">
                {items}
            </ul>'''

    challenges_html = ''
    if challenges:
        items = ''.join([f'<li style="margin-bottom: 4px;">{c}</li>' for c in challenges])
        challenges_html = f'''
            <p style="margin: 0 0 8px 0; color: #1e293b; font-size: 13px; font-weight: 600;">Desafios:</p>
            <ul style="margin: 0; padding-left: 20px; color: #475569; font-size: 13px; line-height: 1.6;">
                {items}
            </ul>'''

    sources_html = _generate_sources_html(sources or [])

    return f'''
    <table role="presentation" style="width: 100%; margin-bottom: 20px; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
        <tr>
            <td style="background-color: #8b5cf6; padding: 14px 20px;">
                <h3 style="margin: 0; color: white; font-size: 16px; font-weight: 600;">Panorama do Mercado</h3>
            </td>
        </tr>
        <tr>
            <td style="padding: 20px; background-color: #ffffff;">
                <p style="margin: 0 0 16px 0; color: #475569; font-size: 14px; line-height: 1.6;">
                    {panorama}
                </p>
                {tendencies_html}
                {challenges_html}
                {sources_html}
            </td>
        </tr>
    </table>'''


def _generate_competition_section(competitors: list, strategies: str, opportunities: str, sources: list = None) -> str:
    """Gera a seção Análise da Concorrência."""
    if not competitors and not strategies and not opportunities:
        return ''

    competitors_html = ''
    if competitors:
        tags = ''.join([
            f'<span style="display: inline-block; background-color: #f8fafc; color: #475569; padding: 4px 12px; border-radius: 16px; font-size: 12px; margin-right: 6px; margin-bottom: 6px;">{_format_competitor(c)}</span>'
            for c in competitors
        ])
        competitors_html = f'<div style="margin-bottom: 12px;">{tags}</div>'

    strategies_html = ''
    if strategies:
        strategies_html = f'''
            <p style="margin: 0 0 12px 0; color: #475569; font-size: 14px; line-height: 1.6;">
                <strong>Estratégias:</strong> {strategies}
            </p>'''

    opportunities_html = ''
    if opportunities:
        opportunities_html = f'''
            <div style="background-color: #f0fdf4; border-left: 3px solid #22c55e; padding: 12px; border-radius: 0 6px 6px 0;">
                <p style="margin: 0; color: #166534; font-size: 13px; line-height: 1.5;">
                    <strong>Oportunidade:</strong> {opportunities}
                </p>
            </div>'''

    sources_html = _generate_sources_html(sources or [])

    return f'''
    <table role="presentation" style="width: 100%; margin-bottom: 20px; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
        <tr>
            <td style="background-color: #059669; padding: 14px 20px;">
                <h3 style="margin: 0; color: white; font-size: 16px; font-weight: 600;">Análise da Concorrência</h3>
            </td>
        </tr>
        <tr>
            <td style="padding: 20px; background-color: #ffffff;">
                {competitors_html}
                {strategies_html}
                {opportunities_html}
                {sources_html}
            </td>
        </tr>
    </table>'''


def _generate_audience_section(profile: str, behaviors: str, interests: list, sources: list = None) -> str:
    """Gera a seção Insights do Público."""
    if not profile and not behaviors and not interests:
        return ''

    profile_html = ''
    if profile:
        profile_html = f'''
            <p style="margin: 0 0 12px 0; color: #475569; font-size: 14px; line-height: 1.6;">
                <strong>Perfil:</strong> {profile}
            </p>'''

    behaviors_html = ''
    if behaviors:
        behaviors_html = f'''
            <p style="margin: 0 0 12px 0; color: #475569; font-size: 14px; line-height: 1.6;">
                <strong>Comportamento:</strong> {behaviors}
            </p>'''

    interests_html = ''
    if interests:
        tags = ''.join([
            f'<span style="display: inline-block; background-color: #fff7ed; color: #c2410c; padding: 4px 12px; border-radius: 16px; font-size: 12px; margin-right: 6px; margin-bottom: 6px;">{i}</span>'
            for i in interests
        ])
        interests_html = f'<div>{tags}</div>'

    sources_html = _generate_sources_html(sources or [])

    return f'''
    <table role="presentation" style="width: 100%; margin-bottom: 20px; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
        <tr>
            <td style="background-color: #ea580c; padding: 14px 20px;">
                <h3 style="margin: 0; color: white; font-size: 16px; font-weight: 600;">Insights do Público</h3>
            </td>
        </tr>
        <tr>
            <td style="padding: 20px; background-color: #ffffff;">
                {profile_html}
                {behaviors_html}
                {interests_html}
                {sources_html}
            </td>
        </tr>
    </table>'''


def _generate_trends_section(themes: list, hashtags: list, keywords: list, sources: list = None) -> str:
    """Gera a seção Tendências da Semana."""
    if not themes and not hashtags and not keywords:
        return ''

    themes_html = ''
    if themes:
        tags = ''.join([
            f'<span style="display: inline-block; background-color: #f3e8ff; color: #7c3aed; padding: 6px 14px; border-radius: 16px; font-size: 13px; font-weight: 500; margin-right: 6px; margin-bottom: 6px;">{t}</span>'
            for t in themes
        ])
        themes_html = f'<div style="margin-bottom: 12px;">{tags}</div>'

    hashtags_html = ''
    if hashtags:
        tags = ''.join([
            f'<span style="display: inline-block; background-color: #dbeafe; color: #1e40af; padding: 4px 10px; border-radius: 16px; font-size: 12px; font-family: monospace; margin-right: 6px; margin-bottom: 6px;">{h}</span>'
            for h in hashtags
        ])
        hashtags_html = f'''
            <p style="margin: 12px 0 8px 0; color: #1e293b; font-size: 13px; font-weight: 600;"># Hashtags em Alta:</p>
            <div>{tags}</div>'''

    keywords_html = ''
    if keywords:
        tags = ''.join([
            f'<span style="display: inline-block; background-color: #ecfdf5; color: #047857; padding: 4px 12px; border-radius: 16px; font-size: 12px; margin-right: 6px; margin-bottom: 6px;">{k}</span>'
            for k in keywords
        ])
        keywords_html = f'''
            <p style="margin: 12px 0 8px 0; color: #1e293b; font-size: 13px; font-weight: 600;">Palavras-chave:</p>
            <div>{tags}</div>'''

    sources_html = _generate_sources_html(sources or [])

    return f'''
    <table role="presentation" style="width: 100%; margin-bottom: 20px; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
        <tr>
            <td style="background-color: #7c3aed; padding: 14px 20px;">
                <h3 style="margin: 0; color: white; font-size: 16px; font-weight: 600;">Tendências da Semana</h3>
            </td>
        </tr>
        <tr>
            <td style="padding: 20px; background-color: #ffffff;">
                {themes_html}
                {hashtags_html}
                {keywords_html}
                {sources_html}
            </td>
        </tr>
    </table>'''


def _generate_calendar_section(dates: list, events: list, sources: list = None) -> str:
    """Gera a seção Calendário Estratégico."""
    if not dates and not events:
        return ''

    dates_html = ''
    if dates:
        items = ''.join([f'<li style="margin-bottom: 4px;">{_format_date(d)}</li>' for d in dates])
        dates_html = f'''
            <p style="margin: 0 0 8px 0; color: #1e293b; font-size: 13px; font-weight: 600;">Datas Importantes:</p>
            <ul style="margin: 0 0 12px 0; padding-left: 20px; color: #475569; font-size: 13px; line-height: 1.6;">
                {items}
            </ul>'''

    events_html = ''
    if events:
        items = ''.join([f'<li style="margin-bottom: 4px;">{_format_date(e)}</li>' for e in events])
        events_html = f'''
            <p style="margin: 0 0 8px 0; color: #1e293b; font-size: 13px; font-weight: 600;">Eventos:</p>
            <ul style="margin: 0; padding-left: 20px; color: #475569; font-size: 13px; line-height: 1.6;">
                {items}
            </ul>'''

    sources_html = _generate_sources_html(sources or [])

    return f'''
    <table role="presentation" style="width: 100%; margin-bottom: 20px; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
        <tr>
            <td style="background-color: #be185d; padding: 14px 20px;">
                <h3 style="margin: 0; color: white; font-size: 16px; font-weight: 600;">Calendário Estratégico</h3>
            </td>
        </tr>
        <tr>
            <td style="padding: 20px; background-color: #ffffff;">
                {dates_html}
                {events_html}
                {sources_html}
            </td>
        </tr>
    </table>'''


def _format_competitor(c) -> str:
    """Formata um competidor (string ou dict) com sanitização XSS."""
    if isinstance(c, dict):
        name = _escape(c.get('name', str(c)))
        followers = _escape(c.get('followers', ''))
        if followers:
            return f"{name} ({followers})"
        return name
    return _escape(str(c))


def _format_date(d) -> str:
    """Formata uma data/evento (string ou dict) com sanitização XSS."""
    if isinstance(d, dict):
        date = _escape(d.get('date', ''))
        event = _escape(d.get('event', ''))
        if date and event:
            return f"{date} - {event}"
        return event or date or _escape(str(d))
    return _escape(str(d))


def _generate_brand_section(presence: str, reputation: str, style: str, sources: list = None) -> str:
    """Gera a seção Análise da Marca."""
    if not presence and not reputation and not style:
        return ''

    presence_html = ''
    if presence:
        presence_html = f'''
            <p style="margin: 0 0 12px 0; color: #475569; font-size: 14px; line-height: 1.6;">
                <strong>Presença Online:</strong> {presence}
            </p>'''

    reputation_html = ''
    if reputation:
        reputation_html = f'''
            <p style="margin: 0 0 12px 0; color: #475569; font-size: 14px; line-height: 1.6;">
                <strong>Reputação:</strong> {reputation}
            </p>'''

    style_html = ''
    if style:
        style_html = f'''
            <div style="background-color: #fef3c7; border-left: 3px solid #f59e0b; padding: 12px; border-radius: 0 6px 6px 0;">
                <p style="margin: 0; color: #92400e; font-size: 13px; line-height: 1.5;">
                    <strong>Estilo de Comunicação:</strong> {style}
                </p>
            </div>'''

    sources_html = _generate_sources_html(sources or [])

    return f'''
    <table role="presentation" style="width: 100%; margin-bottom: 20px; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
        <tr>
            <td style="background-color: #0891b2; padding: 14px 20px;">
                <h3 style="margin: 0; color: white; font-size: 16px; font-weight: 600;">Análise da Marca</h3>
            </td>
        </tr>
        <tr>
            <td style="padding: 20px; background-color: #ffffff;">
                {presence_html}
                {reputation_html}
                {style_html}
                {sources_html}
            </td>
        </tr>
    </table>'''
