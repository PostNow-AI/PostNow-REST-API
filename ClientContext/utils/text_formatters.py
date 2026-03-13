import os
from datetime import datetime


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

