import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def snippet(text, query):
    """A short excerpt of `text` around the first match of `query`, with matches in <mark>.

    Everything is HTML-escaped first, so the only markup in the result is our own <mark>.
    """
    text = (text or "").strip()
    query = (query or "").strip()
    limit = 140
    if not text:
        return ""
    start = 0
    if query:
        m = re.search(re.escape(query), text, re.IGNORECASE)
        if m:
            start = max(0, m.start() - 40)
    excerpt = text[start:start + limit]
    prefix = "…" if start > 0 else ""
    suffix = "…" if start + limit < len(text) else ""
    safe = escape(excerpt)
    if query:
        safe = re.sub("(" + re.escape(escape(query)) + ")", r"<mark>\1</mark>", safe, flags=re.IGNORECASE)
    return mark_safe(prefix + safe + suffix)
