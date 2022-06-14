import datetime

from backend.utils.timedelta import nice_repr
from django import template

register = template.Library()


@register.filter
def timedelta(value, display='long'):
    if value is None:
        return value
    return nice_repr(value, display)


@register.filter
def timestampdelta(value, display='long'):
    value = datetime.timedelta(seconds=value)
    return timedelta(value, display)


@register.filter
def seconds(timedelta):
    return timedelta.total_seconds()


@register.inclusion_tag('time-remaining-fragment.html')
def as_countdown(timedelta):
    return {'countdown': timedelta}
