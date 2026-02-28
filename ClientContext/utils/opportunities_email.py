"""
Template do e-mail de Oportunidades de Conteúdo (Segunda-feira).
Contém apenas as oportunidades enriquecidas da Fase 2.
Estilo visual unificado com o e-mail de Inteligência de Mercado.
"""
import html
import os


def _escape(text) -> str:
    """Sanitiza texto para prevenir XSS."""
    if text is None:
        return ''
    return html.escape(str(text))

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

CATEGORY_COLORS = {
    'polemica': {'bg': '#fef2f2', 'border': '#ef4444', 'text': '#dc2626', 'emoji': '🔥'},
    'educativo': {'bg': '#f0fdf4', 'border': '#22c55e', 'text': '#16a34a', 'emoji': '🧠'},
    'newsjacking': {'bg': '#fefce8', 'border': '#eab308', 'text': '#ca8a04', 'emoji': '📰'},
    'entretenimento': {'bg': '#fdf4ff', 'border': '#d946ef', 'text': '#c026d3', 'emoji': '😂'},
    'estudo_caso': {'bg': '#eff6ff', 'border': '#3b82f6', 'text': '#2563eb', 'emoji': '💼'},
    'futuro': {'bg': '#f5f3ff', 'border': '#8b5cf6', 'text': '#7c3aed', 'emoji': '🔮'},
    'outros': {'bg': '#f8fafc', 'border': '#64748b', 'text': '#475569', 'emoji': '⚡'},
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
                📬 Toda <strong>segunda-feira</strong> você recebe oportunidades. Na <strong>quarta</strong>, inteligência de mercado.
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
                    Pronto para transformar essas ideias em posts?
                </p>
                <a href="{url}" style="display: inline-block; background-color: #ffffff; color: {STYLES['primary_color']}; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px;">
                    Criar Conteúdo
                </a>
            </td>
        </tr>
    </table>
    '''


def _generate_opportunity_item(item: dict, colors: dict, index: int) -> str:
    """Item de oportunidade formatado."""
    # Sanitizar todos os campos de texto para prevenir XSS
    titulo = _escape(item.get('titulo_ideia', ''))
    descricao = _escape(item.get('descricao', ''))
    score = item.get('score', 0)
    url_fonte = item.get('url_fonte', '')
    enriched_sources = item.get('enriched_sources', [])
    # Sanitizar e limpar quebras de linha excessivas no analysis
    enriched_analysis = _escape(item.get('enriched_analysis', '')).replace('\n\n\n', '\n\n')

    separator = 'border-top: 1px solid #e5e7eb; padding-top: 16px; margin-top: 16px;' if index > 0 else ''

    # Sources
    sources_html = ''
    if url_fonte:
        sources_html += f'<a href="{url_fonte}" target="_blank" style="display: inline-block; background-color: {STYLES["light_bg"]}; color: #3b82f6; padding: 4px 10px; border-radius: 4px; font-size: 11px; text-decoration: none; margin-right: 6px; margin-bottom: 6px;">Fonte principal</a>'

    for j, source in enumerate(enriched_sources[:3]):
        source_url = source.get('url', '')
        source_title = source.get('title', f'Fonte {j + 2}')
        if len(source_title) > 25:
            source_title = source_title[:22] + '...'
        if source_url:
            sources_html += f'<a href="{source_url}" target="_blank" style="display: inline-block; background-color: {STYLES["light_bg"]}; color: #3b82f6; padding: 4px 10px; border-radius: 4px; font-size: 11px; text-decoration: none; margin-right: 6px; margin-bottom: 6px;">{source_title}</a>'

    # Analysis
    analysis_html = ''
    if enriched_analysis:
        analysis_html = f'''
        <div style="background-color: {STYLES['light_bg']}; border-left: 3px solid {colors['border']}; padding: 12px; margin: 12px 0; border-radius: 0 6px 6px 0;">
            <p style="margin: 0 0 4px 0; color: {colors['text']}; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">💡 Análise</p>
            <p style="margin: 0; color: {STYLES['text_secondary']}; font-size: 13px; line-height: 1.5; white-space: pre-line;">{enriched_analysis}</p>
        </div>
        '''

    return f'''
    <div style="{separator}">
        <table role="presentation" style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="vertical-align: top;">
                    <h4 style="margin: 0; color: {STYLES['text_primary']}; font-size: 15px; font-weight: 600; line-height: 1.4;">{titulo}</h4>
                </td>
                <td style="vertical-align: top; text-align: right; width: 70px;">
                    <span style="background-color: {colors['border']}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; white-space: nowrap;">{score}/100</span>
                </td>
            </tr>
        </table>
        <p style="margin: 8px 0 12px 0; color: {STYLES['text_secondary']}; font-size: 14px; line-height: 1.5;">{descricao}</p>
        {analysis_html}
        <div style="margin-top: 10px;">
            {sources_html}
        </div>
    </div>
    '''


def _generate_opportunities_html(tendencies_data: dict) -> str:
    """Generate HTML for opportunities section."""
    if not tendencies_data:
        return ''

    html_parts = []

    for category_key, category_data in tendencies_data.items():
        if not isinstance(category_data, dict):
            continue
        titulo = category_data.get('titulo', '')
        items = category_data.get('items', [])
        if not items:
            continue

        colors = CATEGORY_COLORS.get(category_key, CATEGORY_COLORS['outros'])

        items_html = ''
        for i, item in enumerate(items[:3]):
            items_html += _generate_opportunity_item(item, colors, i)

        html_parts.append(f'''
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
        ''')

    return ''.join(html_parts)


def generate_opportunities_email_template(tendencies_data: dict, user_data: dict) -> str:
    """
    Generate HTML email template for weekly opportunities report.
    Sent on Mondays with enriched content opportunities.
    """
    # Sanitizar dados do usuário para prevenir XSS
    business_name = _escape(user_data.get('business_name', 'Sua Empresa'))
    user_name = _escape(user_data.get('user_name', user_data.get('user__first_name', 'Usuário')))
    frontend_url = os.getenv('FRONTEND_URL', 'https://app.postnow.com.br')

    opportunities_html = _generate_opportunities_html(tendencies_data)

    if not opportunities_html:
        opportunities_html = f'''
        <div style="text-align: center; padding: 40px; color: {STYLES['text_muted']};">
            <p style="font-size: 16px;">Nenhuma oportunidade de conteúdo identificada esta semana.</p>
            <p style="font-size: 14px;">Continue acompanhando - novas tendências surgem a todo momento!</p>
        </div>
        '''

    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PostNow - Oportunidades de Conteúdo</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: {STYLES['light_bg']};">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 20px;">
                <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: {STYLES['card_bg']}; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">

                    {_generate_header('Oportunidades de Conteúdo', f'Ideias ranqueadas para {business_name}', '🎯')}

                    <tr>
                        <td style="padding: 24px;">
                            <p style="margin: 0 0 20px 0; color: {STYLES['text_secondary']}; font-size: 15px; line-height: 1.6;">
                                Olá, <strong>{user_name}</strong>! Preparamos as <strong>melhores oportunidades</strong> da semana,
                                cada uma com análise aprofundada e fontes extras.
                            </p>

                            {opportunities_html}

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


def generate_opportunities_plain_text(tendencies_data: dict, user_data: dict) -> str:
    """Generate plain text version of the opportunities email."""
    business_name = user_data.get('business_name', 'Sua Empresa')
    user_name = user_data.get('user_name', user_data.get('user__first_name', 'Usuário'))

    lines = [
        "POSTNOW - OPORTUNIDADES DE CONTEÚDO",
        "=" * 40,
        "",
        f"Olá, {user_name}!",
        "",
        f"Preparamos as melhores oportunidades de conteúdo da semana para {business_name}.",
        "",
    ]

    if not tendencies_data:
        lines.append("Nenhuma oportunidade identificada esta semana.")
    else:
        for category_key, category_data in tendencies_data.items():
            if not isinstance(category_data, dict):
                continue
            titulo = category_data.get('titulo', '')
            items = category_data.get('items', [])
            if not items:
                continue

            lines.append(f"\n{titulo.upper()}")
            lines.append("-" * 30)

            for i, item in enumerate(items[:3], 1):
                titulo_ideia = item.get('titulo_ideia', '')
                score = item.get('score', 0)
                descricao = item.get('descricao', '')
                enriched_analysis = item.get('enriched_analysis', '')

                lines.append(f"\n{i}. {titulo_ideia} ({score}/100)")
                lines.append(f"   {descricao}")

                if enriched_analysis:
                    lines.append(f"\n   Análise: {enriched_analysis[:200]}...")

    lines.extend([
        "",
        "=" * 40,
        "Acesse o dashboard para criar seus posts:",
        os.getenv('FRONTEND_URL', 'https://app.postnow.com.br'),
        "",
        "© 2025 PostNow",
    ])

    return "\n".join(lines)
