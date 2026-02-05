import json
from datetime import datetime, timedelta
import os

def generate_deep_link(title, description, platform="instagram"):
    """
    Gera um deep link para o app PostNow com o contexto preenchido.
    """
    import urllib.parse
    
    base_url = "https://app.postnow.com.br/create"
    params = {
        "title": title,
        "context": description,
        "platform": platform
    }
    query_string = urllib.parse.urlencode(params)
    return f"{base_url}?{query_string}"

def _generate_ranked_opportunities_html(ranked_data):
    """
    Gera o HTML para as oportunidades rankeadas e agrupadas por tipo.
    """
    if not ranked_data or not isinstance(ranked_data, dict):
        return ""

    html_parts = []
    
    # Ordem de prioridade para exibição
    priority_order = ['polemica', 'educativo', 'newsjacking', 'futuro', 'estudo_caso', 'entretenimento', 'outros']
    
    for key in priority_order:
        if key not in ranked_data:
            continue
            
        group = ranked_data[key]
        items = group.get('items', [])
        
        if not items:
            continue
            
        # Título da Seção (Ex: 🔥 Polêmica & Debate)
        section_title = group.get('titulo', key.title())
        
        # Cor da borda baseada no tipo
        border_color = "#3b82f6" # Blue default
        bg_color = "#eff6ff"
        if 'polemica' in key:
            border_color = "#ef4444" # Red
            bg_color = "#fef2f2"
        elif 'educativo' in key:
            border_color = "#10b981" # Green
            bg_color = "#ecfdf5"
        elif 'newsjacking' in key:
            border_color = "#f59e0b" # Orange
            bg_color = "#fffbeb"
        elif 'futuro' in key:
            border_color = "#8b5cf6" # Purple
            bg_color = "#f5f3ff"

        items_html = ""
        for item in items:
            title = item.get('titulo_ideia', 'Ideia sem título')
            score = item.get('score', 0)
            reason = item.get('explicacao_score', '')
            trigger = item.get('gatilho_criativo', '')
            source_url = item.get('url_fonte', '#')
            
            deep_link = generate_deep_link(title, f"{trigger} Baseado em: {item.get('texto_base_analisado', '')}")
            
            items_html += f"""
            <div style="background-color: #ffffff; border-radius: 8px; padding: 16px; margin-bottom: 12px; border-left: 4px solid {border_color}; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                    <h3 style="margin: 0; font-size: 16px; color: #1f2937; font-weight: 600; flex: 1;">
                        <a href="{source_url}" target="_blank" style="text-decoration: none; color: #1f2937; border-bottom: 1px dotted #9ca3af;">{title}</a>
                    </h3>
                    <span style="background-color: {border_color}; color: #ffffff; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 700; margin-left: 8px;">
                        {score}
                    </span>
                </div>
                
                <p style="margin: 0 0 8px 0; font-size: 13px; color: #6b7280; line-height: 1.4;">
                    <strong>Por que viraliza:</strong> {reason}
                </p>
                
                <div style="background-color: {bg_color}; padding: 10px; border-radius: 6px; margin-top: 8px;">
                    <p style="margin: 0; font-size: 13px; color: #374151; font-style: italic;">
                        💡 <strong>Sugestão:</strong> {trigger}
                    </p>
                </div>
                
                <div style="margin-top: 12px; text-align: right;">
                    <a href="{deep_link}" style="display: inline-flex; align-items: center; text-decoration: none; background-color: #1f2937; color: #ffffff; padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 500;">
                        ⚡ Criar este Post
                    </a>
                </div>
            </div>
            """
            
        html_parts.append(f"""
        <div style="margin-bottom: 32px;">
            <h2 style="margin: 0 0 16px 0; font-size: 18px; color: #111827; border-bottom: 2px solid {border_color}; padding-bottom: 8px; display: inline-block;">
                {section_title}
            </h2>
            {items_html}
        </div>
        """)
        
    return "\n".join(html_parts)

def generate_weekly_context_email_template(context_data, user_data):
    """
    Generate the HTML email template for the weekly context report using new ranked opportunities.
    """
    business_name = user_data.get('business_name', 'Sua Empresa')
    user_name = user_data.get('user_name', user_data.get('user__first_name', 'Usuário'))
    
    # Recuperar dados rankeados (NOVO MOTOR)
    ranked_opportunities = context_data.get('ranked_opportunities') or context_data.get('tendencies_data', {})
    
    # Se não tiver dados rankeados, tentar fallback para estrutura antiga (retrocompatibilidade)
    # Mas como o novo motor é o foco, vamos priorizar a renderização das oportunidades
    
    opportunities_html = _generate_ranked_opportunities_html(ranked_opportunities)
    
    # Dados Sazonais - Correção de acesso ao dicionário aninhado
    sazonalidade_raw = context_data.get('sazonalidade', {})
    if not sazonalidade_raw:
         # Fallback para chave 'sazonal' se existir
         sazonalidade_raw = context_data.get('sazonal', {})

    seasonal_data = {
        'datas_relevantes': sazonalidade_raw.get('datas_relevantes', []),
        'eventos_locais': sazonalidade_raw.get('eventos_locais', [])
    }
    
    # Data da geração (Semana)
    today = datetime.now()
    next_week = today + timedelta(days=7)
    week_range = f"{today.day}/{today.month} a {next_week.day}/{next_week.month}"

    # Build Calendar HTML with Deep Links
    calendar_items_html = ""
    datas_relevantes = seasonal_data.get('datas_relevantes', [])
    
    if datas_relevantes:
        for date_str in datas_relevantes[:3]:
            # date_str ex: "25/12 - Natal - Descrição..."
            # Tentar extrair data e título para o deep link
            parts = date_str.split('-', 1)
            date_display = parts[0].strip()
            title_display = parts[1].strip() if len(parts) > 1 else "Data Comemorativa"
            
            deep_link = generate_deep_link(
                f"Post sobre {title_display}", 
                f"Crie um post engajador sobre {title_display} ({date_display}) alinhado com a marca {business_name}."
            )
            
            calendar_items_html += f'''
            <div style="background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; flex: 1;">
                    <div style="background-color: #fee2e2; color: #991b1b; font-weight: 700; font-size: 12px; padding: 4px 8px; border-radius: 4px; margin-right: 12px; min-width: 40px; text-align: center;">
                        {date_display.split(' ')[0]}
                    </div>
                    <div style="font-size: 14px; color: #374151;">{title_display}</div>
                </div>
                <a href="{deep_link}" style="display: inline-flex; align-items: center; text-decoration: none; background-color: #be185d; color: #ffffff; padding: 6px 10px; border-radius: 6px; font-size: 11px; font-weight: 500; margin-left: 8px; white-space: nowrap;">
                    ⚡ Criar Post
                </a>
            </div>
            '''
    else:
        calendar_items_html = '<p style="font-size: 13px; color: #6b7280; font-style: italic;">Sem datas críticas nesta semana.</p>'

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PostNow - Radar de Oportunidades</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6; color: #1f2937;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <!-- Header -->
        <div style="background-color: #111827; padding: 32px 24px; text-align: center;">
            <img src="https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/postnow_logo_white.png" alt="PostNow" style="height: 32px; margin-bottom: 16px;">
            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 700;">Radar Semanal de Conteúdo</h1>
            <p style="margin: 8px 0 0 0; color: #9ca3af; font-size: 14px;">Semana de {week_range}</p>
        </div>

        <!-- Intro -->
        <div style="padding: 24px;">
            <p style="margin: 0; font-size: 16px; line-height: 1.6;">
                Olá, <strong>{user_name}</strong>! 👋
            </p>
            <p style="margin: 12px 0 0 0; font-size: 15px; line-height: 1.6; color: #4b5563;">
                Analisamos o mercado para a <strong>{business_name}</strong> e separamos as melhores oportunidades de conteúdo para você viralizar e vender mais esta semana.
            </p>
        </div>

        <!-- Oportunidades (NOVO MOTOR) -->
        <div style="padding: 0 24px 24px 24px;">
            {opportunities_html if opportunities_html else '<p style="text-align:center; color:#6b7280;">Nenhuma oportunidade de alta relevância encontrada esta semana.</p>'}
        </div>

        <!-- Seção Sazonalidade (Calendário) -->
        <div style="background-color: #f9fafb; padding: 24px; border-top: 1px solid #e5e7eb;">
            <h2 style="margin: 0 0 16px 0; font-size: 18px; color: #111827; display: flex; align-items: center;">
                📅 Calendário Estratégico
            </h2>
            {calendar_items_html}
        </div>

        <!-- Footer -->
        <div style="background-color: #111827; padding: 32px 24px; text-align: center;">
            <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                Gerado por Inteligência Artificial PostNow ⚡<br>
                <a href="https://app.postnow.com.br" style="color: #ffffff; text-decoration: underline;">Acessar Plataforma</a>
            </p>
        </div>
    </div>
</body>
</html>
    """
    return html


def generate_opportunities_email_template(context_data, user_data):
    """
    Generate the HTML email template for the weekly opportunities email (Monday).
    Focuses on ranked opportunities + CTA.
    """
    business_name = user_data.get('business_name', 'Sua Empresa')
    user_name = user_data.get('user_name', user_data.get('user__first_name', 'Usuário'))

    ranked_opportunities = context_data.get('ranked_opportunities') or context_data.get('tendencies_data', {})
    opportunities_html = _generate_ranked_opportunities_html(ranked_opportunities)

    today = datetime.now()
    next_week = today + timedelta(days=7)
    week_range = f"{today.day}/{today.month} a {next_week.day}/{next_week.month}"

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PostNow - Oportunidades de Conteúdo</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6; color: #1f2937;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <!-- Header -->
        <div style="background-color: #111827; padding: 32px 24px; text-align: center;">
            <img src="https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/postnow_logo_white.png" alt="PostNow" style="height: 32px; margin-bottom: 16px;">
            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 700;">Oportunidades de Conteúdo da Semana</h1>
            <p style="margin: 8px 0 0 0; color: #9ca3af; font-size: 14px;">Semana de {week_range}</p>
        </div>

        <!-- Intro -->
        <div style="padding: 24px;">
            <p style="margin: 0; font-size: 16px; line-height: 1.6;">
                Olá, <strong>{user_name}</strong>! 👋
            </p>
            <p style="margin: 12px 0 0 0; font-size: 15px; line-height: 1.6; color: #4b5563;">
                Confira as melhores oportunidades de conteúdo para a <strong>{business_name}</strong> esta semana. Cada ideia foi rankeada por potencial de engajamento e relevância para o seu mercado.
            </p>
        </div>

        <!-- Oportunidades Rankeadas -->
        <div style="padding: 0 24px 24px 24px;">
            {opportunities_html if opportunities_html else '<p style="text-align:center; color:#6b7280;">Nenhuma oportunidade de alta relevância encontrada esta semana.</p>'}
        </div>

        <!-- CTA -->
        <div style="padding: 0 24px 32px 24px; text-align: center;">
            <a href="https://app.postnow.com.br/radar" style="display: inline-block; background-color: #111827; color: #ffffff; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-size: 16px; font-weight: 600;">
                Abrir Radar de Oportunidades
            </a>
        </div>

        <!-- Footer -->
        <div style="background-color: #111827; padding: 32px 24px; text-align: center;">
            <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                Gerado por Inteligência Artificial PostNow ⚡<br>
                <a href="https://app.postnow.com.br" style="color: #ffffff; text-decoration: underline;">Acessar Plataforma</a>
            </p>
        </div>
    </div>
</body>
</html>
    """
    return html


def _render_sources_list(sources, label):
    """Render a list of sources as HTML."""
    if not sources:
        return ""
    items_html = ""
    for src in sources[:5]:
        if isinstance(src, dict):
            url = src.get('url', '#')
            title = src.get('title', src.get('titulo', url))
        elif isinstance(src, str):
            url = src
            title = src
        else:
            continue
        items_html += f'<li style="margin-bottom: 4px;"><a href="{url}" target="_blank" style="color: #3b82f6; text-decoration: none; font-size: 13px;">{title}</a></li>'
    if not items_html:
        return ""
    return f"""
    <div style="margin-top: 8px;">
        <p style="margin: 0 0 4px 0; font-size: 12px; color: #9ca3af; font-weight: 600;">{label}</p>
        <ul style="margin: 0; padding-left: 16px; list-style-type: disc;">{items_html}</ul>
    </div>
    """


def _render_json_as_bullets(data, fallback="Dados indisponíveis."):
    """Render a JSON list or string as bullet-point HTML."""
    if not data:
        return f'<p style="font-size: 14px; color: #6b7280; font-style: italic;">{fallback}</p>'
    if isinstance(data, str):
        return f'<p style="font-size: 14px; color: #374151; line-height: 1.6;">{data}</p>'
    if isinstance(data, list):
        items = ""
        for item in data[:8]:
            if isinstance(item, dict):
                text = item.get('titulo', item.get('name', item.get('nome', str(item))))
            else:
                text = str(item)
            items += f'<li style="margin-bottom: 6px; font-size: 14px; color: #374151; line-height: 1.5;">{text}</li>'
        return f'<ul style="margin: 0; padding-left: 20px;">{items}</ul>'
    return f'<p style="font-size: 14px; color: #374151;">{str(data)}</p>'


def generate_market_intelligence_email_template(context_data, user_data):
    """
    Generate the HTML email template for the market intelligence email (Wednesday).
    Includes: Panorama, Competition, Audience, Trends, Brand, Calendar.
    """
    business_name = user_data.get('business_name', 'Sua Empresa')
    user_name = user_data.get('user_name', user_data.get('user__first_name', 'Usuário'))

    today = datetime.now()
    next_week = today + timedelta(days=7)
    week_range = f"{today.day}/{today.month} a {next_week.day}/{next_week.month}"

    # --- Market Panorama ---
    market_panorama = context_data.get('market_panorama', '')
    market_tendencies = context_data.get('market_tendencies', [])
    market_challenges = context_data.get('market_challenges', [])
    market_opportunities = context_data.get('market_opportunities', [])
    market_sources = context_data.get('market_sources', [])

    # --- Competition ---
    competition_main = context_data.get('competition_main', [])
    competition_strategies = context_data.get('competition_strategies', '')
    competition_opportunities = context_data.get('competition_opportunities', '')
    competition_benchmark = context_data.get('competition_benchmark', [])
    competition_sources = context_data.get('competition_sources', [])

    # --- Target Audience ---
    audience_profile = context_data.get('target_audience_profile', '')
    audience_behaviors = context_data.get('target_audience_behaviors', '')
    audience_interests = context_data.get('target_audience_interests', [])
    audience_sources = context_data.get('target_audience_sources', [])

    # --- Trends ---
    tendencies_themes = context_data.get('tendencies_popular_themes', [])
    tendencies_hashtags = context_data.get('tendencies_hashtags', [])
    tendencies_keywords = context_data.get('tendencies_keywords', [])
    tendencies_sources = context_data.get('tendencies_sources', [])

    # --- Brand ---
    brand_presence = context_data.get('brand_online_presence', '')
    brand_reputation = context_data.get('brand_reputation', '')
    brand_style = context_data.get('brand_communication_style', '')
    brand_sources = context_data.get('brand_sources', [])

    # --- Calendar ---
    seasonal_dates = context_data.get('seasonal_relevant_dates', [])
    seasonal_events = context_data.get('seasonal_local_events', [])
    seasonal_sources = context_data.get('seasonal_sources', [])

    # Build calendar HTML
    calendar_html = ""
    if seasonal_dates:
        for date_str in seasonal_dates[:5]:
            if isinstance(date_str, str):
                calendar_html += f'<li style="margin-bottom: 6px; font-size: 14px; color: #374151;">{date_str}</li>'
            elif isinstance(date_str, dict):
                calendar_html += f'<li style="margin-bottom: 6px; font-size: 14px; color: #374151;">{date_str.get("data", "")} - {date_str.get("titulo", "")}</li>'
        calendar_html = f'<ul style="margin: 0; padding-left: 20px;">{calendar_html}</ul>'
    else:
        calendar_html = '<p style="font-size: 14px; color: #6b7280; font-style: italic;">Sem datas relevantes identificadas.</p>'

    events_html = ""
    if seasonal_events:
        for evt in seasonal_events[:5]:
            if isinstance(evt, str):
                events_html += f'<li style="margin-bottom: 6px; font-size: 14px; color: #374151;">{evt}</li>'
            elif isinstance(evt, dict):
                events_html += f'<li style="margin-bottom: 6px; font-size: 14px; color: #374151;">{evt.get("nome", evt.get("name", str(evt)))}</li>'
        events_html = f'<ul style="margin: 0; padding-left: 20px;">{events_html}</ul>'

    # Build hashtags display
    hashtags_html = ""
    if tendencies_hashtags:
        tags = tendencies_hashtags if isinstance(tendencies_hashtags, list) else []
        for tag in tags[:10]:
            tag_text = tag if isinstance(tag, str) else str(tag)
            hashtags_html += f'<span style="display: inline-block; background-color: #eff6ff; color: #1d4ed8; padding: 4px 10px; border-radius: 12px; font-size: 12px; margin: 2px 4px 2px 0;">{tag_text}</span>'

    # Collect all sources
    all_sources = []
    for src_list, label in [
        (market_sources, "Mercado"),
        (competition_sources, "Concorrência"),
        (audience_sources, "Público"),
        (tendencies_sources, "Tendências"),
        (brand_sources, "Marca"),
        (seasonal_sources, "Calendário"),
    ]:
        if src_list:
            all_sources.append((src_list, label))

    sources_section = ""
    if all_sources:
        sources_items = ""
        for src_list, label in all_sources:
            rendered = _render_sources_list(src_list, label)
            if rendered:
                sources_items += rendered
        if sources_items:
            sources_section = f"""
            <div style="background-color: #f9fafb; padding: 20px 24px; border-top: 1px solid #e5e7eb;">
                <h2 style="margin: 0 0 12px 0; font-size: 16px; color: #6b7280;">📎 Fontes Consultadas</h2>
                {sources_items}
            </div>
            """

    section_style = "padding: 20px 24px; border-top: 1px solid #e5e7eb;"
    section_title_style = "margin: 0 0 12px 0; font-size: 18px; color: #111827;"

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PostNow - Inteligência de Mercado</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6; color: #1f2937;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <!-- Header -->
        <div style="background-color: #111827; padding: 32px 24px; text-align: center;">
            <img src="https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/postnow_logo_white.png" alt="PostNow" style="height: 32px; margin-bottom: 16px;">
            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 700;">Inteligência de Mercado Semanal</h1>
            <p style="margin: 8px 0 0 0; color: #9ca3af; font-size: 14px;">Semana de {week_range}</p>
        </div>

        <!-- Intro -->
        <div style="padding: 24px;">
            <p style="margin: 0; font-size: 16px; line-height: 1.6;">
                Olá, <strong>{user_name}</strong>! 👋
            </p>
            <p style="margin: 12px 0 0 0; font-size: 15px; line-height: 1.6; color: #4b5563;">
                Aqui está sua análise completa de mercado para a <strong>{business_name}</strong>. Use esses insights para tomar decisões mais estratégicas sobre seu conteúdo.
            </p>
        </div>

        <!-- Panorama do Mercado -->
        <div style="{section_style}">
            <h2 style="{section_title_style}">📊 Panorama do Mercado</h2>
            <p style="font-size: 14px; color: #374151; line-height: 1.6;">{market_panorama or 'Análise de mercado indisponível.'}</p>
            {'<h3 style="font-size: 14px; color: #6b7280; margin: 12px 0 6px 0;">Tendências</h3>' + _render_json_as_bullets(market_tendencies) if market_tendencies else ''}
            {'<h3 style="font-size: 14px; color: #6b7280; margin: 12px 0 6px 0;">Desafios</h3>' + _render_json_as_bullets(market_challenges) if market_challenges else ''}
            {'<h3 style="font-size: 14px; color: #6b7280; margin: 12px 0 6px 0;">Oportunidades</h3>' + _render_json_as_bullets(market_opportunities) if market_opportunities else ''}
        </div>

        <!-- Concorrência -->
        <div style="{section_style}">
            <h2 style="{section_title_style}">🏆 Concorrência</h2>
            {'<h3 style="font-size: 14px; color: #6b7280; margin: 0 0 6px 0;">Principais Concorrentes</h3>' + _render_json_as_bullets(competition_main) if competition_main else ''}
            {'<h3 style="font-size: 14px; color: #6b7280; margin: 12px 0 6px 0;">Estratégias</h3><p style="font-size: 14px; color: #374151; line-height: 1.6;">' + competition_strategies + '</p>' if competition_strategies else ''}
            {'<h3 style="font-size: 14px; color: #6b7280; margin: 12px 0 6px 0;">Oportunidades</h3><p style="font-size: 14px; color: #374151; line-height: 1.6;">' + competition_opportunities + '</p>' if competition_opportunities else ''}
            {'<h3 style="font-size: 14px; color: #6b7280; margin: 12px 0 6px 0;">Benchmark</h3>' + _render_json_as_bullets(competition_benchmark) if competition_benchmark else ''}
        </div>

        <!-- Público-Alvo -->
        <div style="{section_style}">
            <h2 style="{section_title_style}">👥 Público-Alvo</h2>
            {'<h3 style="font-size: 14px; color: #6b7280; margin: 0 0 6px 0;">Perfil</h3><p style="font-size: 14px; color: #374151; line-height: 1.6;">' + audience_profile + '</p>' if audience_profile else ''}
            {'<h3 style="font-size: 14px; color: #6b7280; margin: 12px 0 6px 0;">Comportamentos</h3><p style="font-size: 14px; color: #374151; line-height: 1.6;">' + audience_behaviors + '</p>' if audience_behaviors else ''}
            {'<h3 style="font-size: 14px; color: #6b7280; margin: 12px 0 6px 0;">Interesses</h3>' + _render_json_as_bullets(audience_interests) if audience_interests else ''}
        </div>

        <!-- Tendências -->
        <div style="{section_style}">
            <h2 style="{section_title_style}">🔥 Tendências</h2>
            {'<h3 style="font-size: 14px; color: #6b7280; margin: 0 0 6px 0;">Temas Populares</h3>' + _render_json_as_bullets(tendencies_themes) if tendencies_themes else ''}
            {'<h3 style="font-size: 14px; color: #6b7280; margin: 12px 0 6px 0;">Hashtags em Alta</h3><div style="margin-top: 4px;">' + hashtags_html + '</div>' if hashtags_html else ''}
            {'<h3 style="font-size: 14px; color: #6b7280; margin: 12px 0 6px 0;">Palavras-chave</h3>' + _render_json_as_bullets(tendencies_keywords) if tendencies_keywords else ''}
        </div>

        <!-- Marca -->
        <div style="{section_style}">
            <h2 style="{section_title_style}">💼 Sua Marca</h2>
            {'<h3 style="font-size: 14px; color: #6b7280; margin: 0 0 6px 0;">Presença Online</h3><p style="font-size: 14px; color: #374151; line-height: 1.6;">' + brand_presence + '</p>' if brand_presence else ''}
            {'<h3 style="font-size: 14px; color: #6b7280; margin: 12px 0 6px 0;">Reputação</h3><p style="font-size: 14px; color: #374151; line-height: 1.6;">' + brand_reputation + '</p>' if brand_reputation else ''}
            {'<h3 style="font-size: 14px; color: #6b7280; margin: 12px 0 6px 0;">Estilo de Comunicação</h3><p style="font-size: 14px; color: #374151; line-height: 1.6;">' + brand_style + '</p>' if brand_style else ''}
        </div>

        <!-- Calendário -->
        <div style="{section_style}">
            <h2 style="{section_title_style}">📅 Calendário Estratégico</h2>
            <h3 style="font-size: 14px; color: #6b7280; margin: 0 0 6px 0;">Datas Relevantes</h3>
            {calendar_html}
            {'<h3 style="font-size: 14px; color: #6b7280; margin: 12px 0 6px 0;">Eventos Locais</h3>' + events_html if events_html else ''}
        </div>

        <!-- Fontes -->
        {sources_section}

        <!-- CTA -->
        <div style="padding: 24px 24px 32px 24px; text-align: center;">
            <a href="https://app.postnow.com.br/insights" style="display: inline-block; background-color: #111827; color: #ffffff; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-size: 16px; font-weight: 600;">
                Explorar Insights no App
            </a>
        </div>

        <!-- Footer -->
        <div style="background-color: #111827; padding: 32px 24px; text-align: center;">
            <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                Gerado por Inteligência Artificial PostNow ⚡<br>
                <a href="https://app.postnow.com.br" style="color: #ffffff; text-decoration: underline;">Acessar Plataforma</a>
            </p>
        </div>
    </div>
</body>
</html>
    """
    return html
