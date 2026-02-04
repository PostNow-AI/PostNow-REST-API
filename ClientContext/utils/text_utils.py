"""
Utility functions for text processing in Weekly Context service.
"""
import re


def is_blocked_filetype(url: str) -> bool:
    """Check if URL points to a blocked file type."""
    u = (url or "").lower()
    return u.endswith((".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"))


def sanitize_query_for_allowlist(query: str) -> str:
    """
    Remove site operators from query to avoid conflicts with allowlist injection.
    """
    if not query:
        return ""
    q = re.sub(r"(?i)(-?site:[^\s]+)", " ", query)
    q = re.sub(r"\s+", " ", q).strip()
    # Avoid overly long queries (CSE is sensitive to size)
    return q[:220]


def extract_json_block(text: str) -> str:
    """
    Extract the first valid JSON block from a string using brace counting.
    Supports objects {} and lists [].
    """
    text = text.strip()

    start_idx = -1
    stack = []

    for i, char in enumerate(text):
        if char == '{':
            if start_idx == -1:
                start_idx = i
            stack.append('{')
        elif char == '}':
            if stack and stack[-1] == '{':
                stack.pop()
                if not stack and start_idx != -1:
                    return text[start_idx:i+1]
        elif char == '[':
            if start_idx == -1:
                start_idx = i
            stack.append('[')
        elif char == ']':
            if stack and stack[-1] == '[':
                stack.pop()
                if not stack and start_idx != -1:
                    return text[start_idx:i+1]

    # Fallback: try simple regex if stack logic fails (e.g., malformed json)
    match = re.search(r'\{.*\}|\[.*\]', text, re.DOTALL)
    if match:
        return match.group(0)

    return "{}"
