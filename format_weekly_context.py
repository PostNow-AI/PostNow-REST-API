def format_weekly_context_data(context_data):
    """
    Formata dados de contexto semanal em formato legível em português.
    Remove campos de erro e ID.
    """

    # Mapear nomes dos campos para português
    field_mapping = {
        'market_panorama': 'Panorama do Mercado',
        'market_tendencies': 'Tendências do Mercado',
        'market_challenges': 'Desafios do Mercado',
        'market_sources': 'Fontes - Mercado',
        'competition_main': 'Principais Concorrentes',
        'competition_strategies': 'Estratégias da Concorrência',
        'competition_opportunities': 'Oportunidades na Concorrência',
        'competition_sources': 'Fontes - Concorrência',
        'target_audience_profile': 'Perfil do Público-Alvo',
        'target_audience_behaviors': 'Comportamentos do Público-Alvo',
        'target_audience_interests': 'Interesses do Público-Alvo',
        'target_audience_sources': 'Fontes - Público-Alvo',
        'tendencies_popular_themes': 'Temas Populares',
        'tendencies_hashtags': 'Hashtags Tendência',
        'tendencies_keywords': 'Palavras-Chave Tendência',
        'tendencies_sources': 'Fontes - Tendências',
        'seasonal_relevant_dates': 'Datas Relevantes Sazonais',
        'seasonal_local_events': 'Eventos Locais Sazonais',
        'seasonal_sources': 'Fontes - Sazonalidade',
        'brand_online_presence': 'Presença Online da Marca',
        'brand_reputation': 'Reputação da Marca',
        'brand_communication_style': 'Estilo de Comunicação da Marca',
        'brand_sources': 'Fontes - Marca',
        'created_at': 'Criado em',
        'updated_at': 'Atualizado em'
    }

    # Campos a serem ignorados
    ignored_fields = ['id', 'weekly_context_error',
                      'weekly_context_error_date', 'user']

    formatted_data = {}

    for key, value in context_data.items():
        if key in ignored_fields:
            continue

        # Usar nome em português se disponível, senão manter original
        display_name = field_mapping.get(key, key.replace('_', ' ').title())

        # Formatar valor baseado no tipo
        if isinstance(value, list):
            if value:  # Se a lista não estiver vazia
                formatted_data[display_name] = value
            else:
                formatted_data[display_name] = "Não disponível"
        elif isinstance(value, str):
            if value.strip():  # Se a string não estiver vazia
                formatted_data[display_name] = value
            else:
                formatted_data[display_name] = "Não disponível"
        else:
            formatted_data[display_name] = value

    return formatted_data


def format_weekly_context_output(context_data):
    """
    Formata dados de contexto semanal no formato solicitado:
    - Campo: Valor
    - Campo Lista:
        - Item 1,
        - Item 2
    """
    formatted_data = format_weekly_context_data(context_data)
    output_lines = []

    for field_name, value in formatted_data.items():
        if isinstance(value, list):
            # Para listas, mostrar o nome do campo e depois os itens indentados
            output_lines.append(f"- {field_name}:")
            for item in value:
                output_lines.append(f"    - {item},")
        else:
            # Para strings, mostrar campo: valor em uma linha
            output_lines.append(f"- {field_name}: {value},")

    return "\n".join(output_lines)
