"""Helpers compartilhados entre templates de e-mail."""
import html


def escape_html(text) -> str:
    """Sanitiza texto para prevenir XSS."""
    if text is None:
        return ''
    return html.escape(str(text))


def format_list_as_text(data) -> str:
    """
    Converte uma lista Python em texto legível.
    Se for string, retorna escapada. Se for lista, junta com ponto e vírgula.
    """
    if data is None:
        return ''
    if isinstance(data, list):
        items = [escape_html(str(item).strip()) for item in data if item]
        return '; '.join(items) if items else ''
    return escape_html(str(data))


def get_user_name(user_data: dict) -> str:
    """
    Extrai o nome do usuário de forma robusta, tentando múltiplas chaves.
    """
    name = (
        user_data.get('greeting_name') or
        user_data.get('user_name') or
        user_data.get('user__first_name') or
        user_data.get('first_name') or
        user_data.get('name') or
        ''
    )
    if not name or name.strip() == '':
        return 'Usuário'
    return escape_html(name.strip())
