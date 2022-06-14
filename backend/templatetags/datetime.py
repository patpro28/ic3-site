from django import template
from django.templatetags.tz import utc
from django.template.defaultfilters import date

register = template.Library()

register.filter('utc', utc)

@register.filter(name="utctime")
def utcdate(value, arg='Y-m-d\TH:i:s'):
  return date(utc(value), arg)