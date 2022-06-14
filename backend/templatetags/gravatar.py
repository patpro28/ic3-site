import hashlib

from django.utils.http import urlencode
from backend.utils.unicode import utf8bytes
from django import template

register = template.Library()

@register.simple_tag
def gravatar(user, size=80, default=None):
    email = user.email

    gravatar_url = 'https://www.gravatar.com/avatar/' + hashlib.md5(utf8bytes(email.strip().lower())).hexdigest() + '?'
    args = {'d': 'identicon', 's': str(size)}
    if default:
        args['f'] = 'y'
    gravatar_url += urlencode(args)
    return gravatar_url
