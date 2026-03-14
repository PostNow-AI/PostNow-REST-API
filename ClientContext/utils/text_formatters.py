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

