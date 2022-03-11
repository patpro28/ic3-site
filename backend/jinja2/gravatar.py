import hashlib

from django.contrib.auth.models import AbstractUser
from django.utils.http import urlencode

from backend.models import Profile
from backend.utils.unicode import utf8bytes
from . import registry


@registry.function
def gravatar(email, size=80, default=None):
    email = email.email

    gravatar_url = 'https://www.gravatar.com/avatar/' + hashlib.md5(utf8bytes(email.strip().lower())).hexdigest() + '?'
    args = {'d': 'identicon', 's': str(size)}
    if default:
        args['f'] = 'y'
    gravatar_url += urlencode(args)
    return gravatar_url
