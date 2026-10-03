from decimal import Decimal
from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()


@register.filter(name='inr')
def inr(value):
    """
    Format a numeric value using the Indian numbering system.
    Example: 123456 -> ₹1,23,456
    """
    if value is None or value == '':
        return '₹0'

    try:
        if isinstance(value, str):
            value = value.strip().replace(',', '')
        num = Decimal(str(value))
    except Exception:
        return f"₹{value}"

    is_negative = num < 0
    num = abs(num)

    # Convert to int part (rounding or ignoring decimal if .00)
    int_part = int(num)
    s = str(int_part)

    if len(s) <= 3:
        formatted = s
    else:
        # Last 3 digits
        last_three = s[-3:]
        remaining = s[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        formatted = ','.join(groups) + ',' + last_three

    result = f"₹{formatted}"
    if is_negative:
        result = f"-{result}"
    return result


@register.simple_tag(takes_context=True)
def active_link(context, url_name):
    """
    Return 'active' if the current request path matches the given URL name.
    """
    request = context.get('request')
    if not request:
        return ''

    try:
        target_url = reverse(url_name)
        if request.path == target_url:
            return 'active'
        if target_url != '/' and request.path.startswith(target_url):
            return 'active'
    except NoReverseMatch:
        pass

    if hasattr(request, 'resolver_match') and request.resolver_match:
        if request.resolver_match.url_name == url_name:
            return 'active'

    return ''
