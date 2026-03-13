import os

from ClientContext.utils.text_formatters import _format_text_data


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
                if not text:
                    continue
            else:
                text = str(item)
            items += f'<li style="margin-bottom: 6px; font-size: 14px; color: #374151; line-height: 1.5;">{text}</li>'
        if not items:
            return f'<p style="font-size: 14px; color: #6b7280; font-style: italic;">{fallback}</p>'
        return f'<ul style="margin: 0; padding-left: 20px;">{items}</ul>'
    return f'<p style="font-size: 14px; color: #6b7280; font-style: italic;">{fallback}</p>'


def _generate_ranked_opportunities_html(tendencies_data):
    """Generate HTML for ranked opportunities from tendencies_data."""
    if not tendencies_data or not isinstance(tendencies_data, dict):
        return ""

    html_parts = []
    priority_order = ['polemica', 'educativo', 'newsjacking', 'futuro', 'estudo_caso', 'entretenimento', 'outros']

    colors = {
        'polemica': ('#ef4444', '#fef2f2'),
        'educativo': ('#3b82f6', '#eff6ff'),
        'newsjacking': ('#f59e0b', '#fffbeb'),
        'futuro': ('#8b5cf6', '#faf5ff'),
        'estudo_caso': ('#10b981', '#f0fdf4'),
        'entretenimento': ('#ec4899', '#fdf2f8'),
        'outros': ('#6b7280', '#f9fafb'),
    }

    for key in priority_order:
        if key not in tendencies_data:
            continue

        group = tendencies_data[key]
        items = group.get('items', [])

        if not items:
            continue

        title = group.get('titulo', key.title())
        border_color, bg_color = colors.get(key, ('#6b7280', '#f9fafb'))

        items_html = ""
        for item in items[:3]:
            titulo = item.get('titulo_ideia', 'Oportunidade')
            score = item.get('score', 0)
            gatilho = item.get('gatilho_criativo', '')

            items_html += f'''
            <div style="padding: 12px; background: white; border-radius: 6px; margin-bottom: 8px; border: 1px solid #e5e7eb;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="color: #374151; font-size: 14px;">{titulo}</strong>
                    <span style="background: {border_color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">{score}%</span>
                </div>
                {f'<p style="color: #6b7280; font-size: 12px; margin: 4px 0 0 0;">{gatilho}</p>' if gatilho else ''}
            </div>'''

        html_parts.append(f'''
        <div style="margin-bottom: 20px; padding: 16px; background: {bg_color}; border-left: 4px solid {border_color}; border-radius: 8px;">
            <h4 style="margin: 0 0 12px 0; color: #374151;">{title}</h4>
            {items_html}
        </div>''')

    return "".join(html_parts)
