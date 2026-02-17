import os


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
                # Tentar extrair texto de varias chaves possiveis
                text = (
                    item.get('titulo') or
                    item.get('titulo_original') or
                    item.get('titulo_ideia') or
                    item.get('name') or
                    item.get('nome') or
                    item.get('title') or
                    item.get('texto') or
                    item.get('descricao') or
                    item.get('description') or
                    item.get('text') or
                    None
                )
                # Se nao encontrou texto valido, pular este item
                if not text:
                    continue
            else:
                text = str(item)
            items += f'<li style="margin-bottom: 6px; font-size: 14px; color: #374151; line-height: 1.5;">{text}</li>'
        if not items:
            return f'<p style="font-size: 14px; color: #6b7280; font-style: italic;">{fallback}</p>'
        return f'<ul style="margin: 0; padding-left: 20px;">{items}</ul>'
    return f'<p style="font-size: 14px; color: #6b7280; font-style: italic;">{fallback}</p>'


def _format_text_data(data, fallback="Dados não disponíveis."):
    """Format data that may be string, dict, or list into readable text."""
    if not data:
        return fallback
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        # Tentar extrair texto de varias chaves possiveis
        text = (
            data.get('titulo') or
            data.get('titulo_original') or
            data.get('titulo_ideia') or
            data.get('name') or
            data.get('nome') or
            data.get('title') or
            data.get('texto') or
            data.get('descricao') or
            data.get('description') or
            data.get('text') or
            None
        )
        if text:
            return text
        # Se tem lista de oportunidades aninhada, extrair os itens
        if 'oportunidades' in data and isinstance(data['oportunidades'], list):
            items = []
            for item in data['oportunidades'][:5]:
                if isinstance(item, str):
                    items.append(item)
                elif isinstance(item, dict):
                    item_text = (
                        item.get('titulo') or
                        item.get('titulo_original') or
                        item.get('name') or
                        item.get('texto') or
                        item.get('descricao') or
                        None
                    )
                    if item_text:
                        items.append(item_text)
            if items:
                return "; ".join(items)
        return fallback
    if isinstance(data, list):
        items = []
        for item in data[:5]:
            if isinstance(item, str):
                items.append(item)
            elif isinstance(item, dict):
                item_text = (
                    item.get('titulo') or
                    item.get('titulo_original') or
                    item.get('name') or
                    item.get('texto') or
                    item.get('descricao') or
                    None
                )
                if item_text:
                    items.append(item_text)
        if items:
            return "; ".join(items)
        return fallback
    return fallback


def generate_weekly_context_email_template(context_data, user_data):
    """Generate HTML email template for weekly context report"""

    # Extract relevant data
    business_name = user_data.get('business_name', 'Sua Empresa')
    user_name = user_data.get(
        'user_name', user_data.get('user__first_name', 'Usuário'))

    # Map flat context_data structure to nested structure for compatibility
    market_data = {
        'panorama': context_data.get('market_panorama', ''),
        'tendencias': context_data.get('market_tendencies', []),
        'desafios': context_data.get('market_challenges', []),
        'fontes': context_data.get('market_sources', [])
    }

    competition_data = {
        'principais': context_data.get('competition_main', []),
        'estrategias': context_data.get('competition_strategies', ''),
        'oportunidades': context_data.get('competition_opportunities', ''),
        'fontes': context_data.get('competition_sources', [])
    }

    audience_data = {
        'perfil': context_data.get('target_audience_profile', ''),
        'comportamento_online': context_data.get('target_audience_behaviors', ''),
        'interesses': context_data.get('target_audience_interests', []),
        'fontes': context_data.get('target_audience_sources', [])
    }

    trends_data = {
        'temas_populares': context_data.get('tendencies_popular_themes', []),
        'hashtags': context_data.get('tendencies_hashtags', []),
        'palavras_chave': context_data.get('tendencies_keywords', []),
        'fontes': context_data.get('tendencies_sources', [])
    }

    # Brand and seasonal data
    brand_data = {
        'presenca_online': context_data.get('brand_online_presence', ''),
        'reputacao': context_data.get('brand_reputation', ''),
        'estilo_comunicacao': context_data.get('brand_communication_style', ''),
        'fontes': context_data.get('brand_sources', [])
    }

    seasonal_data = {
        'datas_relevantes': context_data.get('seasonal_relevant_dates', []),
        'eventos_locais': context_data.get('seasonal_local_events', []),
        'fontes': context_data.get('seasonal_sources', [])
    }

    # Ranked opportunities data
    ranked_opportunities = context_data.get('tendencies_data', {})
    if not isinstance(ranked_opportunities, dict):
        ranked_opportunities = {}

    SECTION_STYLES = {
        'polemica': {'emoji': '🔥', 'titulo': 'Polêmica & Debate', 'border': '#ef4444', 'bg': '#fef2f2'},
        'educativo': {'emoji': '📚', 'titulo': 'Educativo & Utilidade', 'border': '#10b981', 'bg': '#ecfdf5'},
        'newsjacking': {'emoji': '📰', 'titulo': 'Newsjacking (Urgente)', 'border': '#f59e0b', 'bg': '#fffbeb'},
        'futuro': {'emoji': '🔮', 'titulo': 'Futuro & Tendências', 'border': '#8b5cf6', 'bg': '#f5f3ff'},
        'estudo_caso': {'emoji': '📊', 'titulo': 'Estudo de Caso', 'border': '#06b6d4', 'bg': '#ecfeff'},
        'entretenimento': {'emoji': '🎭', 'titulo': 'Entretenimento', 'border': '#ec4899', 'bg': '#fdf2f8'},
        'outros': {'emoji': '💡', 'titulo': 'Outras Oportunidades', 'border': '#3b82f6', 'bg': '#eff6ff'},
    }

    frontend_url = os.getenv('FRONTEND_URL', 'https://app.postnow.com.br')

    # Build ranked opportunities HTML
    opportunities_html = ''
    for section_key in ['polemica', 'newsjacking', 'educativo', 'futuro', 'estudo_caso', 'entretenimento', 'outros']:
        section = ranked_opportunities.get(section_key, {})
        if not section or not isinstance(section, dict):
            continue
        items = section.get('items', [])
        if not items:
            continue

        style = SECTION_STYLES.get(section_key, SECTION_STYLES['outros'])
        titulo = section.get('titulo', f"{style['emoji']} {style['titulo']}")

        cards_html = ''
        for item in items[:3]:  # Max 3 per section in email
            score = item.get('score', 0)
            titulo_ideia = item.get('titulo_ideia', '')
            explicacao = item.get('explicacao_score', '')
            gatilho = item.get('gatilho_criativo', '')
            url_fonte = item.get('url_fonte', '')

            cards_html += f"""
                <div style="background-color: #ffffff; border-left: 4px solid {style['border']}; border-radius: 8px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
                    <div style="margin-bottom: 8px;">
                        <span style="font-size: 16px; font-weight: 600; color: #1e293b;">{titulo_ideia}</span>
                        <span style="display: inline-block; background-color: {style['border']}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 700; margin-left: 8px; vertical-align: middle;">{score}</span>
                    </div>
                    <p style="margin: 0 0 8px 0; color: #64748b; font-size: 13px;">{explicacao}</p>
                    <div style="background-color: {style['bg']}; border-radius: 6px; padding: 12px; margin-bottom: 12px;">
                        <p style="margin: 0; color: #334155; font-size: 13px;">💡 <strong>Sugestão:</strong> {gatilho}</p>
                    </div>
                    <div>
                        <a href="{frontend_url}/weekly-context" style="display: inline-block; background-color: {style['border']}; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: 600;">Criar Post</a>
                        {'<a href="' + url_fonte + '" style="display: inline-block; color: ' + style["border"] + '; padding: 8px 16px; font-size: 13px; text-decoration: none; font-weight: 500;">Ver Fonte →</a>' if url_fonte else ''}
                    </div>
                </div>"""

        opportunities_html += f"""
            <div style="margin-bottom: 24px;">
                <h3 style="margin: 0 0 12px 0; color: {style['border']}; font-size: 18px; font-weight: 600;">{titulo} ({len(items)})</h3>
                {cards_html}
            </div>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PostNow - Contexto Semanal de Mercado</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #ffffff;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 20px 0;">
                <table role="presentation" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">

                    <!-- Header -->
                    <tr>
                        <td style="background-color: #0f172a; padding: 40px; text-align: center;">
                            <img src="https://postnow-image-bucket-prod.s3.sa-east-1.amazonaws.com/postnow_logo_white.png" alt="PostNow Logo" style="width: 114px; height: 32px; margin-bottom: 20px;">
                            <h1 style="margin: 0; color: #8b5cf6; font-size: 24px; font-weight: 600;">
                                Contexto Semanal de Mercado <span style="color: #ffffff;">📈</span>
                            </h1>
                            <p style="margin: 10px 0 0 0; color: #94a3b8; font-size: 16px;">
                                Insights personalizados para {business_name}
                            </p>
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <!-- Greeting Section -->
                            <table role="presentation" style="width: 100%; margin-bottom: 30px;">
                                <tr>
                                    <td>
                                        <h2 style="margin: 0 0 16px 0; color: #1e293b; font-size: 22px; font-weight: 600;">
                                            Olá, {user_name}! 👋
                                        </h2>
                                        <p style="margin: 0; color: #475569; font-size: 16px; line-height: 1.5;">
                                            Aqui está seu resumo semanal personalizado com as principais tendências, 
                                            insights de mercado e oportunidades para impulsionar seu negócio.
                                        </p>
                                    </td>
                                </tr>
                            </table>

                            <!-- Ranked Opportunities Section (Hero) -->
                            {f"""
                            <table role="presentation" style="width: 100%; margin-bottom: 40px; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
                                <tr>
                                    <td style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 20px; color: white;">
                                        <h2 style="margin: 0; font-size: 20px; font-weight: 600;">🎯 Oportunidades de Conteúdo da Semana</h2>
                                        <p style="margin: 6px 0 0 0; color: #94a3b8; font-size: 14px;">Rankeadas por potencial de engajamento</p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 24px; background-color: #f8fafc;">
                                        {opportunities_html}
                                        <div style="text-align: center; margin-top: 16px;">
                                            <a href="{frontend_url}/weekly-context" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 16px;">
                                                🚀 Ver Todas as Oportunidades no App
                                            </a>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                            """ if opportunities_html else ''}

                            <!-- Market Overview Section -->
                            <table role="presentation" style="width: 100%; margin-bottom: 40px; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
                                <tr>
                                    <td style="background-color: #8b5cf6; padding: 20px; color: white;">
                                        <h2 style="margin: 0; font-size: 20px; font-weight: 600;">🏢 Panorama do Mercado</h2>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 24px;">
                                        <p style="margin: 0 0 16px 0; color: #374151; font-size: 16px; line-height: 1.6;">
                                            {_format_text_data(market_data.get('panorama'), 'Dados do mercado não disponíveis nesta semana.')}
                                        </p>
                                        
                                        {'''
                                        <div style="margin-top: 20px;">
                                            <h4 style="margin: 0 0 12px 0; color: #6366f1; font-size: 16px; font-weight: 600;">🔥 Principais Tendências:</h4>
                                            <ul style="margin: 0; padding-left: 20px; color: #4b5563; font-size: 14px; line-height: 1.5;">
                                        ''' if market_data.get('tendencias') else ''}
                                        
                                        {(''.join([f'<li style="margin-bottom: 8px;">{trend}</li>' for trend in market_data.get('tendencias', [])])) if market_data.get('tendencias') else ''}
                                        
                                        {'''
                                            </ul>
                                        </div>
                                        ''' if market_data.get('tendencias') else ''}
                                        
                                        {'''
                                        <div style="margin-top: 20px;">
                                            <h4 style="margin: 0 0 12px 0; color: #dc2626; font-size: 16px; font-weight: 600;">⚠️ Desafios Identificados:</h4>
                                            <ul style="margin: 0; padding-left: 20px; color: #4b5563; font-size: 14px; line-height: 1.5;">
                                        ''' if market_data.get('desafios') else ''}
                                        
                                        {(''.join([f'<li style="margin-bottom: 8px;">{challenge}</li>' for challenge in market_data.get('desafios', [])])) if market_data.get('desafios') else ''}
                                        
                                        {'''
                                            </ul>
                                        </div>
                                        ''' if market_data.get('desafios') else ''}
                                    </td>
                                </tr>
                            </table>

                            <!-- Competition Analysis Section -->
                            <table role="presentation" style="width: 100%; margin-bottom: 40px; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
                                <tr>
                                    <td style="background-color: #059669; padding: 20px; color: white;">
                                        <h2 style="margin: 0; font-size: 20px; font-weight: 600;">🎯 Análise da Concorrência</h2>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 24px;">
                                        {'''
                                        <div style="margin-bottom: 20px;">
                                            <h4 style="margin: 0 0 12px 0; color: #059669; font-size: 16px; font-weight: 600;">🏆 Principais Concorrentes:</h4>
                                            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                                        ''' if competition_data.get('principais') else ''}
                                        
                                        {(''.join([f'<span style="background-color: #ecfdf5; color: #065f46; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 500;">{competitor}</span>' for competitor in competition_data.get('principais', [])])) if competition_data.get('principais') else ''}
                                        
                                        {'''
                                            </div>
                                        </div>
                                        ''' if competition_data.get('principais') else ''}
                                        
                                        <p style="margin: 0 0 16px 0; color: #374151; font-size: 16px; line-height: 1.6;">
                                            <strong>Estratégias Observadas:</strong><br>
                                            {_format_text_data(competition_data.get('estrategias'), 'Análise competitiva não disponível nesta semana.')}
                                        </p>
                                        
                                        <div style="background-color: #f0fdf4; border-left: 4px solid #22c55e; padding: 16px; border-radius: 4px;">
                                            <h4 style="margin: 0 0 8px 0; color: #15803d; font-size: 14px; font-weight: 600;">💡 Oportunidades de Diferenciação:</h4>
                                            <p style="margin: 0; color: #166534; font-size: 14px; line-height: 1.5;">
                                                {_format_text_data(competition_data.get('oportunidades'), 'Análise de oportunidades em desenvolvimento.')}
                                            </p>
                                        </div>
                                    </td>
                                </tr>
                            </table>

                            <!-- Audience Insights Section -->
                            <table role="presentation" style="width: 100%; margin-bottom: 40px; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
                                <tr>
                                    <td style="background-color: #ea580c; padding: 20px; color: white;">
                                        <h2 style="margin: 0; font-size: 20px; font-weight: 600;">👥 Insights do Público</h2>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 24px;">
                                        <p style="margin: 0 0 16px 0; color: #374151; font-size: 16px; line-height: 1.6;">
                                            <strong>Perfil do Público:</strong><br>
                                            {_format_text_data(audience_data.get('perfil'), 'Dados do público-alvo em análise.')}
                                        </p>
                                        
                                        <p style="margin: 0 0 20px 0; color: #374151; font-size: 16px; line-height: 1.6;">
                                            <strong>Comportamento Online:</strong><br>
                                            {_format_text_data(audience_data.get('comportamento_online'), 'Análise comportamental em desenvolvimento.')}
                                        </p>
                                        
                                        {'''
                                        <div>
                                            <h4 style="margin: 0 0 12px 0; color: #ea580c; font-size: 16px; font-weight: 600;">❤️ Principais Interesses:</h4>
                                            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                                        ''' if audience_data.get('interesses') else ''}
                                        
                                        {(''.join([f'<span style="background-color: #fff7ed; color: #c2410c; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 500;">{interest}</span>' for interest in audience_data.get('interesses', [])])) if audience_data.get('interesses') else ''}
                                        
                                        {'''
                                            </div>
                                        </div>
                                        ''' if audience_data.get('interesses') else ''}
                                    </td>
                                </tr>
                            </table>

                            <!-- Trending Topics Section -->
                            <table role="presentation" style="width: 100%; margin-bottom: 40px; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
                                <tr>
                                    <td style="background-color: #7c3aed; padding: 20px; color: white;">
                                        <h2 style="margin: 0; font-size: 20px; font-weight: 600;">🔥 Tendências da Semana</h2>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 24px;">
                                        {'''
                                        <div style="margin-bottom: 24px;">
                                            <h4 style="margin: 0 0 12px 0; color: #7c3aed; font-size: 16px; font-weight: 600;">🌟 Temas Populares:</h4>
                                            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                                        ''' if trends_data.get('temas_populares') else ''}
                                        
                                        {(''.join([f'<span style="background-color: #f3e8ff; color: #6b21a8; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: 500;">{topic}</span>' for topic in trends_data.get('temas_populares', [])])) if trends_data.get('temas_populares') else ''}
                                        
                                        {'''
                                            </div>
                                        </div>
                                        ''' if trends_data.get('temas_populares') else ''}
                                        
                                        {'''
                                        <div style="margin-bottom: 24px;">
                                            <h4 style="margin: 0 0 12px 0; color: #1d4ed8; font-size: 16px; font-weight: 600;"># Hashtags em Alta:</h4>
                                            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                                        ''' if trends_data.get('hashtags') else ''}
                                        
                                        {(''.join([f'<span style="background-color: #dbeafe; color: #1e40af; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 500; font-family: monospace;">{hashtag}</span>' for hashtag in trends_data.get('hashtags', [])])) if trends_data.get('hashtags') else ''}
                                        
                                        {'''
                                            </div>
                                        </div>
                                        ''' if trends_data.get('hashtags') else ''}
                                        
                                        {'''
                                        <div>
                                            <h4 style="margin: 0 0 12px 0; color: #059669; font-size: 16px; font-weight: 600;">🔍 Palavras-chave Estratégicas:</h4>
                                            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                                        ''' if trends_data.get('palavras_chave') else ''}
                                        
                                        {(''.join([f'<span style="background-color: #ecfdf5; color: #047857; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 500;">{keyword}</span>' for keyword in trends_data.get('palavras_chave', [])])) if trends_data.get('palavras_chave') else ''}
                                        
                                        {'''
                                            </div>
                                        </div>
                                        ''' if trends_data.get('palavras_chave') else ''}
                                    </td>
                                </tr>
                            </table>

                            <!-- Brand Analysis Section -->
                            <table role="presentation" style="width: 100%; margin-bottom: 40px; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
                                <tr>
                                    <td style="background-color: #1e40af; padding: 20px; color: white;">
                                        <h2 style="margin: 0; font-size: 20px; font-weight: 600;">🏢 Análise da Marca</h2>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 24px;">
                                        <p style="margin: 0 0 16px 0; color: #374151; font-size: 16px; line-height: 1.6;">
                                            <strong>Presença Online:</strong><br>
                                            {_format_text_data(brand_data.get('presenca_online'), 'Análise de presença online não disponível.')}
                                        </p>

                                        <p style="margin: 0 0 16px 0; color: #374151; font-size: 16px; line-height: 1.6;">
                                            <strong>Reputação:</strong><br>
                                            {_format_text_data(brand_data.get('reputacao'), 'Análise de reputação não disponível.')}
                                        </p>

                                        {f"""
                                        <p style="margin: 0 0 16px 0; color: #374151; font-size: 16px; line-height: 1.6;">
                                            <strong>Estilo de Comunicação:</strong><br>
                                            {_format_text_data(brand_data.get('estilo_comunicacao'), 'Análise de comunicação não disponível.')}
                                        </p>
                                        """ if brand_data.get('estilo_comunicacao') else ''}
                                    </td>
                                </tr>
                            </table>

                            <!-- Seasonal Calendar Section -->
                            <table role="presentation" style="width: 100%; margin-bottom: 40px; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
                                <tr>
                                    <td style="background-color: #be185d; padding: 20px; color: white;">
                                        <h2 style="margin: 0; font-size: 20px; font-weight: 600;">📅 Calendário Estratégico</h2>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 24px;">
                                        {'''
                                        <div style="margin-bottom: 20px;">
                                            <h4 style="margin: 0 0 12px 0; color: #be185d; font-size: 16px; font-weight: 600;">📆 Datas Relevantes:</h4>
                                            <ul style="margin: 0; padding-left: 20px; color: #4b5563; font-size: 14px; line-height: 1.5;">
                                        ''' if seasonal_data.get('datas_relevantes') else ''}
                                        
                                        {(''.join([f'<li style="margin-bottom: 8px;">{date}</li>' for date in seasonal_data.get('datas_relevantes', [])])) if seasonal_data.get('datas_relevantes') else ''}
                                        
                                        {'''
                                            </ul>
                                        </div>
                                        ''' if seasonal_data.get('datas_relevantes') else ''}
                                        
                                        {'''
                                        <div>
                                            <h4 style="margin: 0 0 12px 0; color: #7c2d12; font-size: 16px; font-weight: 600;">🎪 Eventos Locais:</h4>
                                            <ul style="margin: 0; padding-left: 20px; color: #4b5563; font-size: 14px; line-height: 1.5;">
                                        ''' if seasonal_data.get('eventos_locais') else ''}
                                        
                                        {(''.join([f'<li style="margin-bottom: 8px;">{event}</li>' for event in seasonal_data.get('eventos_locais', [])])) if seasonal_data.get('eventos_locais') else ''}
                                        
                                        {'''
                                            </ul>
                                        </div>
                                        ''' if seasonal_data.get('eventos_locais') else ''}
                                        
                                        {'''
                                        <div style="background-color: #fef7ff; border-left: 4px solid #be185d; padding: 16px; border-radius: 4px; margin-top: 16px;">
                                            <p style="margin: 0; color: #92400e; font-size: 14px; line-height: 1.5;">
                                                💡 <strong>Dica:</strong> Use essas datas para planejar campanhas especiais e criar conteúdo relevante para seu público.
                                            </p>
                                        </div>
                                        ''' if seasonal_data.get('datas_relevantes') or seasonal_data.get('eventos_locais') else ''}
                                    </td>
                                </tr>
                            </table>

                            <!-- Sources Section -->
                            <table role="presentation" style="width: 100%; margin-bottom: 40px; background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
                                <tr>
                                    <td style="padding: 24px;">
                                        <h3 style="margin: 0 0 16px 0; color: #374151; font-size: 18px; font-weight: 600;">📚 Fontes Consultadas</h3>
                                        <p style="margin: 0 0 12px 0; color: #6b7280; font-size: 14px;">
                                            Esta análise foi baseada em dados de fontes confiáveis:
                                        </p>
                                        
                                        {'''
                                        <div style="margin-top: 16px;">
                                            <h4 style="margin: 0 0 8px 0; color: #6366f1; font-size: 14px; font-weight: 600;">Mercado:</h4>
                                            <ul style="margin: 0 0 16px 0; padding-left: 20px; color: #6b7280; font-size: 12px;">
                                        ''' if market_data.get('fontes') else ''}
                                        
                                        {(''.join([f'<li style="margin-bottom: 4px;"><a href="{source}" style="color: #3b82f6; text-decoration: none;">{source}</a></li>' for source in market_data.get('fontes', [])])) if market_data.get('fontes') else ''}
                                        
                                        {'''
                                            </ul>
                                        </div>
                                        ''' if market_data.get('fontes') else ''}
                                        
                                        {'''
                                        <div style="margin-top: 16px;">
                                            <h4 style="margin: 0 0 8px 0; color: #059669; font-size: 14px; font-weight: 600;">Concorrência:</h4>
                                            <ul style="margin: 0 0 16px 0; padding-left: 20px; color: #6b7280; font-size: 12px;">
                                        ''' if competition_data.get('fontes') else ''}
                                        
                                        {(''.join([f'<li style="margin-bottom: 4px;"><a href="{source}" style="color: #3b82f6; text-decoration: none;">{source}</a></li>' for source in competition_data.get('fontes', [])])) if competition_data.get('fontes') else ''}
                                        
                                        {'''
                                            </ul>
                                        </div>
                                        ''' if competition_data.get('fontes') else ''}
                                        
                                        {'''
                                        <div style="margin-top: 16px;">
                                            <h4 style="margin: 0 0 8px 0; color: #ea580c; font-size: 14px; font-weight: 600;">Público-Alvo:</h4>
                                            <ul style="margin: 0 0 16px 0; padding-left: 20px; color: #6b7280; font-size: 12px;">
                                        ''' if audience_data.get('fontes') else ''}
                                        
                                        {(''.join([f'<li style="margin-bottom: 4px;"><a href="{source}" style="color: #3b82f6; text-decoration: none;">{source}</a></li>' for source in audience_data.get('fontes', [])])) if audience_data.get('fontes') else ''}
                                        
                                        {'''
                                            </ul>
                                        </div>
                                        ''' if audience_data.get('fontes') else ''}
                                        
                                        {'''
                                        <div style="margin-top: 16px;">
                                            <h4 style="margin: 0 0 8px 0; color: #7c3aed; font-size: 14px; font-weight: 600;">Tendências:</h4>
                                            <ul style="margin: 0 0 16px 0; padding-left: 20px; color: #6b7280; font-size: 12px;">
                                        ''' if trends_data.get('fontes') else ''}
                                        
                                        {(''.join([f'<li style="margin-bottom: 4px;"><a href="{source}" style="color: #3b82f6; text-decoration: none;">{source}</a></li>' for source in trends_data.get('fontes', [])])) if trends_data.get('fontes') else ''}
                                        
                                        {'''
                                            </ul>
                                        </div>
                                        ''' if trends_data.get('fontes') else ''}
                                        
                                        {'''
                                        <div style="margin-top: 16px;">
                                            <h4 style="margin: 0 0 8px 0; color: #1e40af; font-size: 14px; font-weight: 600;">Marca:</h4>
                                            <ul style="margin: 0 0 16px 0; padding-left: 20px; color: #6b7280; font-size: 12px;">
                                        ''' if brand_data.get('fontes') else ''}
                                        
                                        {(''.join([f'<li style="margin-bottom: 4px;"><a href="{source}" style="color: #3b82f6; text-decoration: none;">{source}</a></li>' for source in brand_data.get('fontes', [])])) if brand_data.get('fontes') else ''}
                                        
                                        {'''
                                            </ul>
                                        </div>
                                        ''' if brand_data.get('fontes') else ''}
                                    </td>
                                </tr>
                            </table>

                            <!-- Call to Action Section -->
                            <table role="presentation" style="width: 100%; margin-bottom: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px;">
                                <tr>
                                    <td style="padding: 32px; text-align: center;">
                                        <h3 style="margin: 0 0 12px 0; color: white; font-size: 20px; font-weight: 600;">✨ Pronto para criar conteúdo impactante?</h3>
                                        <p style="margin: 0 0 20px 0; color: #e2e8f0; font-size: 16px; line-height: 1.5;">
                                            Use estes insights para criar posts que realmente conectam com seu público
                                        </p>
                                        <a href="{frontend_url}/weekly-context" style="display: inline-block; background-color: #ffffff; color: #667eea; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 16px;">
                                            Abrir Radar de Oportunidades
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <!-- Footer Section -->
                            <table role="presentation" style="width: 100%; background-color: #f8fafc; border-radius: 8px; border-top: 1px solid #e2e8f0;">
                                <tr>
                                    <td style="padding: 32px; text-align: center;">
                                        <p style="margin: 0 0 8px 0; color: #64748b; font-size: 14px; font-weight: 500;">
                                            📬 Você recebe este relatório semanalmente com insights personalizados para seu negócio.
                                        </p>
                                        <p style="margin: 0 0 8px 0; color: #6a7282; font-size: 12px;">
                                            Quer ajustar as configurações? Acesse sua conta no PostNow.
                                        </p>
                                        <p style="margin: 0; color: #6a7282; font-size: 12px; font-weight: 500;">
                                            © 2025 PostNow. Inteligência de mercado para seu crescimento.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>

    </table>
</body>
</html>"""

    return html


def generate_weekly_context_plain_text(context_data, user_data):
    """Generate plain text version for email clients that don't support HTML"""

    business_name = user_data.get('business_name', 'Sua Empresa')
    user_name = user_data.get(
        'user_name', user_data.get('user__first_name', 'Usuário'))

    # Map flat context_data structure to nested structure for compatibility
    market_data = {
        'panorama': context_data.get('market_panorama', ''),
        'tendencias': context_data.get('market_tendencies', []),
        'desafios': context_data.get('market_challenges', [])
    }

    competition_data = {
        'principais': context_data.get('competition_main', []),
        'estrategias': context_data.get('competition_strategies', ''),
        'oportunidades': context_data.get('competition_opportunities', '')
    }

    audience_data = {
        'perfil': context_data.get('target_audience_profile', ''),
        'comportamento_online': context_data.get('target_audience_behaviors', ''),
        'interesses': context_data.get('target_audience_interests', [])
    }

    trends_data = {
        'temas_populares': context_data.get('tendencies_popular_themes', []),
        'hashtags': context_data.get('tendencies_hashtags', []),
        'palavras_chave': context_data.get('tendencies_keywords', [])
    }

    # Brand and seasonal data
    brand_data = {
        'presenca_online': context_data.get('brand_online_presence', ''),
        'reputacao': context_data.get('brand_reputation', ''),
        'estilo_comunicacao': context_data.get('brand_communication_style', '')
    }

    seasonal_data = {
        'datas_relevantes': context_data.get('seasonal_relevant_dates', []),
        'eventos_locais': context_data.get('seasonal_local_events', [])
    }

    text = f"""
POSTNOW - CONTEXTO SEMANAL DE MERCADO
=====================================

Olá, {user_name}!

Aqui está seu resumo semanal personalizado para {business_name} com as principais 
tendências, insights de mercado e oportunidades para impulsionar seu negócio.

🏢 PANORAMA DO MERCADO
----------------------
{_format_text_data(market_data.get('panorama'), 'Dados do mercado não disponíveis nesta semana.')}

🔥 Principais Tendências:
{chr(10).join([f"• {trend}" for trend in market_data.get('tendencias', [])]) if market_data.get('tendencias') else "• Não disponível"}

⚠️ Desafios Identificados:
{chr(10).join([f"• {challenge}" for challenge in market_data.get('desafios', [])]) if market_data.get('desafios') else "• Não disponível"}

🎯 ANÁLISE DA CONCORRÊNCIA
--------------------------
Principais Concorrentes: {', '.join(competition_data.get('principais', [])) if competition_data.get('principais') else 'Não disponível'}

Estratégias Observadas:
{_format_text_data(competition_data.get('estrategias'), 'Análise competitiva não disponível nesta semana.')}

💡 Oportunidades de Diferenciação:
{_format_text_data(competition_data.get('oportunidades'), 'Análise de oportunidades em desenvolvimento.')}

👥 INSIGHTS DO PÚBLICO
----------------------
Perfil do Público:
{_format_text_data(audience_data.get('perfil'), 'Dados do público-alvo em análise.')}

Comportamento Online:
{_format_text_data(audience_data.get('comportamento_online'), 'Análise comportamental em desenvolvimento.')}

❤️ Principais Interesses:
{', '.join(audience_data.get('interesses', [])) if audience_data.get('interesses') else 'Não disponível'}

🔥 TENDÊNCIAS DA SEMANA
-----------------------
🌟 Temas Populares: {', '.join(trends_data.get('temas_populares', [])) if trends_data.get('temas_populares') else 'Não disponível'}

# Hashtags em Alta: {', '.join(trends_data.get('hashtags', [])) if trends_data.get('hashtags') else 'Não disponível'}

🔍 Palavras-chave Estratégicas: {', '.join(trends_data.get('palavras_chave', [])) if trends_data.get('palavras_chave') else 'Não disponível'}

🏢 ANÁLISE DA MARCA
-------------------
Presença Online:
{_format_text_data(brand_data.get('presenca_online'), 'Análise de presença online não disponível.')}

Reputação:
{_format_text_data(brand_data.get('reputacao'), 'Análise de reputação não disponível.')}

{f"""
Estilo de Comunicação:
{_format_text_data(brand_data.get('estilo_comunicacao'), 'Análise de comunicação não disponível.')}""" if brand_data.get('estilo_comunicacao') else ''}

📅 CALENDÁRIO ESTRATÉGICO
-------------------------
📆 Datas Relevantes:
{chr(10).join([f"• {date}" for date in seasonal_data.get('datas_relevantes', [])]) if seasonal_data.get('datas_relevantes') else "• Não disponível"}

🎪 Eventos Locais:
{chr(10).join([f"• {event}" for event in seasonal_data.get('eventos_locais', [])]) if seasonal_data.get('eventos_locais') else "• Não disponível"}

📚 FONTES CONSULTADAS
--------------------
Esta análise foi baseada em dados de fontes confiáveis. Acesse sua conta PostNow 
para ver os links completos das fontes utilizadas.

✨ PRÓXIMOS PASSOS
------------------
Use estes insights para criar posts que realmente conectam com seu público.
Acesse: https://postnow.ai/dashboard

© 2025 PostNow. Inteligência de mercado para seu crescimento.

Para ajustar suas preferências, acesse sua conta no PostNow.
"""

    return text.strip()
