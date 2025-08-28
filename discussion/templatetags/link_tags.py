from django import template
from django.utils.html import urlize
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter(name="urlize_target_blank", is_safe=True, needs_autoescape=True)
def urlize_target_blank(value, autoescape=True):
    """
    Convert URLs in plain text to anchor tags and ensure they open in a new tab
    with rel attributes for security.
    Usage: {{ text|urlize_target_blank }}
    """
    # Use Django's urlize to convert URLs to links (respects autoescape)
    html = urlize(value, nofollow=True, autoescape=autoescape)

    # Add target and rel to all anchor tags
    def add_attrs(match):
        tag = match.group(0)
        has_target = re.search(r"\btarget=", tag, flags=re.IGNORECASE)
        has_rel = re.search(r"\brel=", tag, flags=re.IGNORECASE)
        if not has_target:
            tag = tag[:-1] + ' target="_blank">'
        if not has_rel:
            tag = tag[:-1] + ' rel="noopener noreferrer">'
        return tag

    html = re.sub(r"<a\s+[^>]*>", add_attrs, html)
    return mark_safe(html)
