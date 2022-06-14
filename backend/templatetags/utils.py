from urllib.parse import quote
from django import template

register = template.Library()

register.filter("urlquote", quote)