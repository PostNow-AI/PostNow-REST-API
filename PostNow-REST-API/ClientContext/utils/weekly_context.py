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
