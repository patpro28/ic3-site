from django import template

from ..models import Profile

register = template.Library()

@register.inclusion_tag('user/link.html')
def link_user(user):
  if isinstance(user, Profile):
      user = user
  elif type(user).__name__ == 'ContestRankingProfile':
      user = user.user
  else:
      raise ValueError('Expected user, got %s' % (type(user),))
  return {'user': user}