from django.conf import settings

from backend.utils.caniuse import CanIUse, SUPPORT

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
    }

def math_setting(request):
    caniuse = CanIUse(request.META.get('HTTP_USER_AGENT', ''))

    if request.user.is_authenticated:
        engine = request.user.math_engine
    else:
        engine = settings.MATHOID_DEFAULT_TYPE
    if engine == 'auto':
        engine = 'mml' if bool(settings.MATHOID_URL) and caniuse.mathml == SUPPORT else 'jax'
    return {'MATH_ENGINE': engine, 'REQUIRE_JAX': engine == 'jax', 'caniuse': caniuse}
