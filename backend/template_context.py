from functools import partial
from django.conf import settings
from django.contrib.auth.context_processors import PermWrapper
from django.utils.functional import SimpleLazyObject, new_method_proxy

from backend.utils.caniuse import CanIUse, SUPPORT
from backend.models.interface import NavigationBar

class FixedSimpleLazyObject(SimpleLazyObject):
    if not hasattr(SimpleLazyObject, '__iter__'):
        __iter__ = new_method_proxy(iter)

def site_name(request):
    return {
        'SITE_NAME': settings.SITE_NAME,
        'SITE_LONG_NAME': settings.SITE_LONG_NAME,
        'SITE_ADMIN_EMAIL': settings.SITE_ADMIN_EMAIL
    }

def get_resources(request):
    use_https = settings.SSL

    if use_https == 1:
        scheme = 'https' if request.is_secure() else 'http'
    elif use_https > 1:
        scheme = 'https'
    else:
        scheme = 'http'
    return {
        'PYGMENT_THEME': settings.PYGMENT_THEME,
        'INLINE_JQUERY': settings.INLINE_JQUERY,
        'INLINE_FONTAWESOME': settings.INLINE_FONTAWESOME,
        'JQUERY_JS': settings.JQUERY_JS,
        'FONTAWESOME_CSS': settings.FONTAWESOME_CSS,
        'MATERIAL_ICONS': settings.MATERIAL_ICONS,
        'EMATH_SCHEME': scheme,
        'DMOJ_CANONICAL': settings.DMOJ_CANONICAL,
        'THEME': settings.FRONTEND_THEME
    }

def math_setting(request):
    caniuse = CanIUse(request.META.get('HTTP_USER_AGENT', ''))

    if request.user.is_authenticated:
        engine = request.user.math_engine
    else:
        engine = settings.MATHOID_DEFAULT_TYPE
    if engine == 'auto':
        engine = 'mml' if bool(settings.MATHOID_URL) and caniuse.mathml == SUPPORT else 'jax'
    # print(engine)
    return {'MATH_ENGINE': engine, 'REQUIRE_JAX': engine == 'jax', 'caniuse': caniuse}


def __nav_tab(path):
    result = list(NavigationBar.objects.extra(where=['%s REGEXP BINARY regex'], params=[path])[:1])
    return result[0].get_ancestors(include_self=True).values_list('key', flat=True) if result else []


def general_info(request):
    path = request.get_full_path()
    return {
        'nav_tab': FixedSimpleLazyObject(partial(__nav_tab, request.path)),
        'nav_bar': NavigationBar.objects.all(),
        'LOGIN_RETURN_PATH': '' if path.startswith('/accounts/') else path,
        'perms': PermWrapper(request.user),
        'HAS_WEBAUTHN': bool(settings.WEBAUTHN_RP_ID),
    }
