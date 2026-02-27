"""
Template do e-mail de Inteligência de Mercado (Quarta-feira).
Contém análise de mercado, concorrência, público, tendências e calendário.
Estilo visual unificado com o e-mail de Oportunidades.
"""
import os

# Estilo unificado PostNow
STYLES = {
    'primary_color': '#8b5cf6',
    'secondary_color': '#6366f1',
    'dark_bg': '#0f172a',
    'light_bg': '#f8fafc',
    'card_bg': '#ffffff',
    'text_primary': '#1e293b',
    'text_secondary': '#475569',
    'text_muted': '#64748b',
    'border_color': '#e2e8f0',
}

SECTION_COLORS = {
    'market': '#8b5cf6',
    'competition': '#059669',
    'audience': '#ea580c',
    'trends': '#7c3aed',
    'calendar': '#be185d',
}


def _generate_header(title: str, subtitle: str, emoji: str) -> str:
    """Header unificado."""
    return f'''
    <tr>
        <td style="background: linear-gradient(135deg, {STYLES['dark_bg']} 0%, #1e293b 100%); padding: 32px; text-align: center;">
            <img src="https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/postnow_logo_white.png" alt="PostNow Logo" style="width: 114px; height: 32px; margin-bottom: 16px;">
            <h1 style="margin: 0; color: {STYLES['primary_color']}; font-size: 22px; font-weight: 700;">
                {emoji} {title}
            </h1>
            <p style="margin: 8px 0 0 0; color: #94a3b8; font-size: 14px;">
                {subtitle}
            </p>
        </td>
    </tr>
    '''


def _generate_footer() -> str:
    """Footer unificado."""
    return f'''
    <tr>
        <td style="padding: 24px; background-color: {STYLES['light_bg']}; border-top: 1px solid {STYLES['border_color']}; text-align: center;">
            <p style="margin: 0 0 8px 0; color: {STYLES['text_muted']}; font-size: 12px;">
                📬 Toda <strong>quarta-feira</strong> você recebe inteligência de mercado. Na <strong>segunda</strong>, oportunidades de conteúdo.
            </p>
            <p style="margin: 0; color: #94a3b8; font-size: 11px;">
                © 2025 PostNow. Transformando dados em conteúdo.
            </p>
        </td>
    </tr>
    '''


def _generate_cta(url: str) -> str:
    """CTA unificado."""
    return f'''
    <table role="presentation" style="width: 100%; background: linear-gradient(135deg, {STYLES['secondary_color']} 0%, {STYLES['primary_color']} 100%); border-radius: 12px; margin-top: 24px;">
        <tr>
            <td style="padding: 24px; text-align: center;">
                <p style="margin: 0 0 12px 0; color: rgba(255,255,255,0.9); font-size: 15px;">
                    Use esses insights para criar conteúdo que conecta
                </p>
                <a href="{url}" style="display: inline-block; background-color: #ffffff; color: {STYLES['primary_color']}; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px;">
                    Acessar Dashboard
                </a>
            </td>
        </tr>
    </table>
    '''


def _generate_section_card(title: str, emoji: str, color: str, content: str) -> str:
    """Card de seção unificado."""
    return f'''
    <table role="presentation" style="width: 100%; margin-bottom: 20px; border: 1px solid {STYLES['border_color']}; border-radius: 12px; overflow: hidden;">
        <tr>
            <td style="background-color: {color}; padding: 14px 20px;">
                <h3 style="margin: 0; color: white; font-size: 16px; font-weight: 600;">{emoji} {title}</h3>
            </td>
        </tr>
        <tr>
            <td style="padding: 20px; background-color: {STYLES['card_bg']};">
                {content}
            </td>
        </tr>
    </table>
    '''


def _generate_tag(text: str, bg_color: str, text_color: str) -> str:
    """Tag/badge formatado."""
    return f'<span style="display: inline-block; background-color: {bg_color}; color: {text_color}; padding: 4px 12px; border-radius: 16px; font-size: 12px; margin-right: 6px; margin-bottom: 6px;">{text}</span>'


def generate_weekly_context_email_template(context_data: dict, user_data: dict) -> str:
    """
    Generate HTML email template for weekly market intelligence report.
    Sent on Wednesdays.
    """
    business_name = user_data.get('business_name', 'Sua Empresa')
    user_name = user_data.get('user_name', user_data.get('user__first_name', 'Usuário'))
    frontend_url = os.getenv('FRONTEND_URL', 'https://app.postnow.com.br')

    # Market section
    market_content = f'''
    <p style="margin: 0 0 16px 0; color: {STYLES['text_secondary']}; font-size: 14px; line-height: 1.6;">
        {context_data.get('market_panorama', 'Dados do mercado não disponíveis nesta semana.')}
    </p>
    '''

    tendencias = context_data.get('market_tendencies', [])
    if tendencias:
        market_content += f'<p style="margin: 0 0 8px 0; color: {STYLES["text_primary"]}; font-size: 13px; font-weight: 600;">📈 Tendências:</p><ul style="margin: 0 0 16px 0; padding-left: 20px; color: {STYLES["text_secondary"]}; font-size: 13px; line-height: 1.6;">'
        for t in tendencias:
            market_content += f'<li style="margin-bottom: 4px;">{t}</li>'
        market_content += '</ul>'

    desafios = context_data.get('market_challenges', [])
    if desafios:
        market_content += f'<p style="margin: 0 0 8px 0; color: {STYLES["text_primary"]}; font-size: 13px; font-weight: 600;">⚠️ Desafios:</p><ul style="margin: 0; padding-left: 20px; color: {STYLES["text_secondary"]}; font-size: 13px; line-height: 1.6;">'
        for d in desafios:
            market_content += f'<li style="margin-bottom: 4px;">{d}</li>'
        market_content += '</ul>'

    # Competition section
    competition_content = ''
    principais = context_data.get('competition_main', [])
    if principais:
        competition_content += '<div style="margin-bottom: 12px;">'
        for p in principais:
            competition_content += _generate_tag(p, STYLES['light_bg'], STYLES['text_secondary'])
        competition_content += '</div>'

    competition_content += f'''
    <p style="margin: 0 0 12px 0; color: {STYLES['text_secondary']}; font-size: 14px; line-height: 1.6;">
        <strong>Estratégias:</strong> {context_data.get('competition_strategies', 'Análise não disponível.')}
    </p>
    '''

    oportunidades = context_data.get('competition_opportunities', '')
    if oportunidades:
        competition_content += f'''
        <div style="background-color: #f0fdf4; border-left: 3px solid #22c55e; padding: 12px; border-radius: 0 6px 6px 0;">
            <p style="margin: 0; color: #166534; font-size: 13px; line-height: 1.5;">
                <strong>💡 Oportunidade:</strong> {oportunidades}
            </p>
        </div>
        '''

    # Audience section
    audience_content = f'''
    <p style="margin: 0 0 12px 0; color: {STYLES['text_secondary']}; font-size: 14px; line-height: 1.6;">
        <strong>Perfil:</strong> {context_data.get('target_audience_profile', 'Não disponível.')}
    </p>
    <p style="margin: 0 0 12px 0; color: {STYLES['text_secondary']}; font-size: 14px; line-height: 1.6;">
        <strong>Comportamento:</strong> {context_data.get('target_audience_behaviors', 'Não disponível.')}
    </p>
    '''
    interesses = context_data.get('target_audience_interests', [])
    if interesses:
        audience_content += '<div>'
        for i in interesses:
            audience_content += _generate_tag(i, '#fff7ed', '#c2410c')
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
        trends_content += f'<p style="margin: 12px 0 8px 0; color: {STYLES["text_primary"]}; font-size: 13px; font-weight: 600;"># Hashtags em Alta:</p><div>'
        for h in hashtags:
            trends_content += f'<span style="display: inline-block; background-color: #dbeafe; color: #1e40af; padding: 4px 10px; border-radius: 16px; font-size: 12px; font-family: monospace; margin-right: 6px; margin-bottom: 6px;">{h}</span>'
        trends_content += '</div>'

    keywords = context_data.get('tendencies_keywords', [])
    if keywords:
        trends_content += f'<p style="margin: 12px 0 8px 0; color: {STYLES["text_primary"]}; font-size: 13px; font-weight: 600;">🔍 Palavras-chave:</p><div>'
        for k in keywords:
            trends_content += _generate_tag(k, '#ecfdf5', '#047857')
        trends_content += '</div>'

    if not trends_content:
        trends_content = f'<p style="margin: 0; color: {STYLES["text_muted"]}; font-size: 14px;">Nenhuma tendência identificada esta semana.</p>'

    # Calendar section
    calendar_content = ''
    datas = context_data.get('seasonal_relevant_dates', [])
    if datas:
        calendar_content += f'<p style="margin: 0 0 8px 0; color: {STYLES["text_primary"]}; font-size: 13px; font-weight: 600;">📆 Datas Importantes:</p><ul style="margin: 0 0 12px 0; padding-left: 20px; color: {STYLES["text_secondary"]}; font-size: 13px; line-height: 1.6;">'
        for d in datas:
            calendar_content += f'<li style="margin-bottom: 4px;">{d}</li>'
        calendar_content += '</ul>'

    eventos = context_data.get('seasonal_local_events', [])
    if eventos:
        calendar_content += f'<p style="margin: 0 0 8px 0; color: {STYLES["text_primary"]}; font-size: 13px; font-weight: 600;">🎪 Eventos:</p><ul style="margin: 0; padding-left: 20px; color: {STYLES["text_secondary"]}; font-size: 13px; line-height: 1.6;">'
        for e in eventos:
            calendar_content += f'<li style="margin-bottom: 4px;">{e}</li>'
        calendar_content += '</ul>'

    if not calendar_content:
        calendar_content = f'<p style="margin: 0; color: {STYLES["text_muted"]}; font-size: 14px;">Nenhum evento relevante identificado esta semana.</p>'

    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PostNow - Inteligência de Mercado</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: {STYLES['light_bg']};">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 20px;">
                <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: {STYLES['card_bg']}; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">

                    {_generate_header('Inteligência de Mercado', f'Insights semanais para {business_name}', '📊')}

                    <tr>
                        <td style="padding: 24px;">
                            <p style="margin: 0 0 20px 0; color: {STYLES['text_secondary']}; font-size: 15px; line-height: 1.6;">
                                Olá, <strong>{user_name}</strong>! Aqui está seu resumo semanal com as principais tendências
                                e insights do mercado.
                            </p>

                            {_generate_section_card('Panorama do Mercado', '🏢', SECTION_COLORS['market'], market_content)}

                            {_generate_section_card('Análise da Concorrência', '🎯', SECTION_COLORS['competition'], competition_content)}

                            {_generate_section_card('Insights do Público', '👥', SECTION_COLORS['audience'], audience_content)}

                            {_generate_section_card('Tendências da Semana', '🔥', SECTION_COLORS['trends'], trends_content)}

                            {_generate_section_card('Calendário Estratégico', '📅', SECTION_COLORS['calendar'], calendar_content)}

                            {_generate_cta(frontend_url)}
                        </td>
                    </tr>

                    {_generate_footer()}

                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''


def generate_weekly_context_plain_text(context_data: dict, user_data: dict) -> str:
    """Generate plain text version for email clients that don't support HTML."""
    business_name = user_data.get('business_name', 'Sua Empresa')
    user_name = user_data.get('user_name', user_data.get('user__first_name', 'Usuário'))

    lines = [
        "POSTNOW - INTELIGÊNCIA DE MERCADO",
        "=" * 40,
        "",
        f"Olá, {user_name}!",
        "",
        f"Aqui está seu resumo semanal de mercado para {business_name}.",
        "",
        "PANORAMA DO MERCADO",
        "-" * 30,
        context_data.get('market_panorama', 'Não disponível.'),
        "",
    ]

    tendencias = context_data.get('market_tendencies', [])
    if tendencias:
        lines.append("Tendências:")
        for t in tendencias:
            lines.append(f"  • {t}")
        lines.append("")

    desafios = context_data.get('market_challenges', [])
    if desafios:
        lines.append("Desafios:")
        for d in desafios:
            lines.append(f"  • {d}")
        lines.append("")

    lines.extend([
        "ANÁLISE DA CONCORRÊNCIA",
        "-" * 30,
        f"Principais: {', '.join(context_data.get('competition_main', ['Não disponível']))}",
        f"Estratégias: {context_data.get('competition_strategies', 'Não disponível.')}",
        f"Oportunidades: {context_data.get('competition_opportunities', 'Não disponível.')}",
        "",
        "INSIGHTS DO PÚBLICO",
        "-" * 30,
        f"Perfil: {context_data.get('target_audience_profile', 'Não disponível.')}",
        f"Comportamento: {context_data.get('target_audience_behaviors', 'Não disponível.')}",
        f"Interesses: {', '.join(context_data.get('target_audience_interests', ['Não disponível']))}",
        "",
        "TENDÊNCIAS",
        "-" * 30,
        f"Temas: {', '.join(context_data.get('tendencies_popular_themes', ['Não disponível']))}",
        f"Hashtags: {', '.join(context_data.get('tendencies_hashtags', ['Não disponível']))}",
        "",
        "CALENDÁRIO",
        "-" * 30,
    ])

    datas = context_data.get('seasonal_relevant_dates', [])
    if datas:
        for d in datas:
            lines.append(f"  • {d}")
    else:
        lines.append("  Nenhuma data relevante.")

    lines.extend([
        "",
        "=" * 40,
        "Acesse o dashboard:",
        os.getenv('FRONTEND_URL', 'https://app.postnow.com.br'),
        "",
        "© 2025 PostNow",
    ])

    return "\n".join(lines)
