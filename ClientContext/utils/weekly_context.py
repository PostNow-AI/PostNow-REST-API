"""Re-exports for backwards compatibility.

Functions are now organized in:
- text_formatters.py: _format_text_data
- html_formatters.py: _render_json_as_bullets, _generate_ranked_opportunities_html
- email_templates.py: generate_*_email_template, generate_weekly_context_plain_text
"""

from ClientContext.utils.text_formatters import _format_text_data  # noqa: F401
from ClientContext.utils.html_formatters import (  # noqa: F401
    _render_json_as_bullets,
    _generate_ranked_opportunities_html,
)
from ClientContext.utils.email_templates import (  # noqa: F401
    generate_weekly_context_email_template,
    generate_weekly_context_plain_text,
    generate_opportunities_email_template,
    generate_market_intelligence_email_template,
)
