def format_semantic_analysis_data(analysis_data):
    """
    Formata dados de análise semântica em formato legível em português.
    """

    # Mapear nomes dos campos para português
    field_mapping = {
        'tema_principal': 'Tema Principal',
        'subtemas': 'Subtemas',
        'conceitos_visuais': 'Conceitos Visuais',
        'objetos_relevantes': 'Objetos Relevantes',
        'contexto_visual_sugerido': 'Contexto Visual Sugerido',
        'emoções_associadas': 'Emoções Associadas',
        'tons_de_cor_sugeridos': 'Tons de Cor Sugeridos',
        'ação_sugerida': 'Ação Sugerida',
        'sensação_geral': 'Sensação Geral',
        'palavras_chave': 'Palavras-Chave'
    }

    formatted_data = {}

    # Processar dados da análise semântica
    if 'analise_semantica' in analysis_data:
        semantic_data = analysis_data['analise_semantica']
    else:
        semantic_data = analysis_data

    for key, value in semantic_data.items():
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


def format_semantic_analysis_output(analysis_data):
    """
    Formata dados de análise semântica no formato solicitado:
    - Campo: Valor
    - Campo Lista:
        - Item 1,
        - Item 2
    """
    formatted_data = format_semantic_analysis_data(analysis_data)
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
