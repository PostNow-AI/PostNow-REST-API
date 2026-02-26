import os


def _generate_enriched_opportunities_html(tendencies_data: dict) -> str:
    """Generate HTML for enriched opportunities section."""
    if not tendencies_data:
        return ''

    html_parts = []
    category_colors = {
        'polemica': {'bg': '#fef2f2', 'border': '#ef4444', 'text': '#dc2626'},
        'educativo': {'bg': '#f0fdf4', 'border': '#22c55e', 'text': '#16a34a'},
        'newsjacking': {'bg': '#fefce8', 'border': '#eab308', 'text': '#ca8a04'},
        'entretenimento': {'bg': '#fdf4ff', 'border': '#d946ef', 'text': '#c026d3'},
        'estudo_caso': {'bg': '#eff6ff', 'border': '#3b82f6', 'text': '#2563eb'},
        'futuro': {'bg': '#f5f3ff', 'border': '#8b5cf6', 'text': '#7c3aed'},
        'outros': {'bg': '#f8fafc', 'border': '#64748b', 'text': '#475569'},
    }

    for category_key, category_data in tendencies_data.items():
        if not isinstance(category_data, dict):
            continue
        titulo = category_data.get('titulo', '')
        items = category_data.get('items', [])
        if not items:
            continue
        colors = category_colors.get(category_key, category_colors['outros'])

        html_parts.append(f'''
        <div style="margin-bottom: 24px; border: 1px solid {colors['border']}; border-radius: 8px; overflow: hidden;">
            <div style="background-color: {colors['border']}; padding: 12px 16px;">
                <h4 style="margin: 0; color: white; font-size: 16px; font-weight: 600;">{titulo}</h4>
            </div>
            <div style="padding: 16px; background-color: {colors['bg']};">
        ''')

        for i, item in enumerate(items[:3]):
            titulo_ideia = item.get('titulo_ideia', '')
            descricao = item.get('descricao', '')
            score = item.get('score', 0)
            url_fonte = item.get('url_fonte', '')
            enriched_sources = item.get('enriched_sources', [])
            enriched_analysis = item.get('enriched_analysis', '')

            html_parts.append(f'''
                <div style="{'margin-top: 16px; padding-top: 16px; border-top: 1px solid #e5e7eb;' if i > 0 else ''}">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                        <h5 style="margin: 0; color: {colors['text']}; font-size: 15px; font-weight: 600; flex: 1;">{titulo_ideia}</h5>
                        <span style="background-color: {colors['border']}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; margin-left: 8px;">Score: {score}</span>
                    </div>
                    <p style="margin: 0 0 12px 0; color: #4b5563; font-size: 14px; line-height: 1.5;">{descricao}</p>
            ''')

            if enriched_analysis:
                html_parts.append(f'''
                    <div style="background-color: white; border-left: 3px solid {colors['border']}; padding: 12px; margin-bottom: 12px; border-radius: 4px;">
                        <p style="margin: 0 0 4px 0; color: {colors['text']}; font-size: 12px; font-weight: 600;">Analise Aprofundada:</p>
                        <p style="margin: 0; color: #374151; font-size: 13px; line-height: 1.5;">{enriched_analysis}</p>
                    </div>
                ''')

            html_parts.append('<div style="margin-top: 8px;"><p style="margin: 0 0 6px 0; color: #6b7280; font-size: 12px; font-weight: 500;">Fontes:</p><div style="display: flex; flex-wrap: wrap; gap: 6px;">')

            if url_fonte:
                html_parts.append(f'<a href="{url_fonte}" style="display: inline-block; background-color: white; color: #3b82f6; padding: 4px 8px; border-radius: 4px; font-size: 11px; text-decoration: none; border: 1px solid #e5e7eb;">Fonte principal</a>')

            for j, source in enumerate(enriched_sources[:3]):
                source_url = source.get('url', '')
                source_title = source.get('title', f'Fonte {j + 2}')
                if len(source_title) > 30:
                    source_title = source_title[:27] + '...'
                if source_url:
                    html_parts.append(f'<a href="{source_url}" style="display: inline-block; background-color: white; color: #3b82f6; padding: 4px 8px; border-radius: 4px; font-size: 11px; text-decoration: none; border: 1px solid #e5e7eb;">{source_title}</a>')

            html_parts.append('</div></div></div>')
        html_parts.append('</div></div>')

    if not html_parts:
        return ''

    return f'''
        <table role="presentation" style="width: 100%; margin-bottom: 40px; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
            <tr><td style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); padding: 20px; color: white;">
                <h2 style="margin: 0; font-size: 20px; font-weight: 600;">Oportunidades de Conteudo da Semana</h2>
                <p style="margin: 8px 0 0 0; font-size: 14px; opacity: 0.9;">Ideias ranqueadas e enriquecidas com fontes adicionais</p>
            </td></tr>
            <tr><td style="padding: 24px;">{''.join(html_parts)}</td></tr>
        </table>
    '''


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

    # Enriched opportunities data (Phase 2)
    tendencies_data = context_data.get('tendencies_data', {})
    enriched_opportunities_html = _generate_enriched_opportunities_html(tendencies_data)

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

                            <!-- Enriched Opportunities Section (Phase 2) -->
                            {enriched_opportunities_html}

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
                                            {market_data.get('panorama', 'Dados do mercado não disponíveis nesta semana.')}
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
                                            {competition_data.get('estrategias', 'Análise competitiva não disponível nesta semana.')}
                                        </p>
                                        
                                        <div style="background-color: #f0fdf4; border-left: 4px solid #22c55e; padding: 16px; border-radius: 4px;">
                                            <h4 style="margin: 0 0 8px 0; color: #15803d; font-size: 14px; font-weight: 600;">💡 Oportunidades de Diferenciação:</h4>
                                            <p style="margin: 0; color: #166534; font-size: 14px; line-height: 1.5;">
                                                {competition_data.get('oportunidades', 'Análise de oportunidades em desenvolvimento.')}
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
                                            {audience_data.get('perfil', 'Dados do público-alvo em análise.')}
                                        </p>
                                        
                                        <p style="margin: 0 0 20px 0; color: #374151; font-size: 16px; line-height: 1.6;">
                                            <strong>Comportamento Online:</strong><br>
                                            {audience_data.get('comportamento_online', 'Análise comportamental em desenvolvimento.')}
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
                                            {brand_data.get('presenca_online', 'Análise de presença online não disponível.')}
                                        </p>
                                        
                                        <p style="margin: 0 0 16px 0; color: #374151; font-size: 16px; line-height: 1.6;">
                                            <strong>Reputação:</strong><br>
                                            {brand_data.get('reputacao', 'Análise de reputação não disponível.')}
                                        </p>
                                        
                                        {'''
                                        <p style="margin: 0 0 16px 0; color: #374151; font-size: 16px; line-height: 1.6;">
                                            <strong>Estilo de Comunicação:</strong><br>
                                            {brand_data.get('estilo_comunicacao', 'Análise de comunicação não disponível.')}
                                        </p>
                                        ''' if brand_data.get('estilo_comunicacao') else ''}
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
                                        <a href="{os.getenv('FRONTEND_URL')}" style="display: inline-block; background-color: #ffffff; color: #667eea; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 16px;">
                                            Acessar Dashboard
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
{market_data.get('panorama', 'Dados do mercado não disponíveis nesta semana.')}

🔥 Principais Tendências:
{chr(10).join([f"• {trend}" for trend in market_data.get('tendencias', [])]) if market_data.get('tendencias') else "• Não disponível"}

⚠️ Desafios Identificados:
{chr(10).join([f"• {challenge}" for challenge in market_data.get('desafios', [])]) if market_data.get('desafios') else "• Não disponível"}

🎯 ANÁLISE DA CONCORRÊNCIA
--------------------------
Principais Concorrentes: {', '.join(competition_data.get('principais', [])) if competition_data.get('principais') else 'Não disponível'}

Estratégias Observadas:
{competition_data.get('estrategias', 'Análise competitiva não disponível nesta semana.')}

💡 Oportunidades de Diferenciação:
{competition_data.get('oportunidades', 'Análise de oportunidades em desenvolvimento.')}

👥 INSIGHTS DO PÚBLICO
----------------------
Perfil do Público:
{audience_data.get('perfil', 'Dados do público-alvo em análise.')}

Comportamento Online:
{audience_data.get('comportamento_online', 'Análise comportamental em desenvolvimento.')}

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
{brand_data.get('presenca_online', 'Análise de presença online não disponível.')}

Reputação:
{brand_data.get('reputacao', 'Análise de reputação não disponível.')}

{f"""
Estilo de Comunicação:
{brand_data.get('estilo_comunicacao', 'Análise de comunicação não disponível.')}""" if brand_data.get('estilo_comunicacao') else ''}

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
