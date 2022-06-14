import re
from django import template
from django.template.defaultfilters import date
from django.utils.translation import gettext_lazy as _

from backend.templatetags.variable import SetNewVariable

register = template.Library()

@register.filter
def time_left(contest, arg=_("M j, Y, G:i")):
  return date(contest.start_time, arg) + ' - ' + date(contest.end_time, arg)

@register.inclusion_tag('contest/join_button.html', name="join")
def contest_join(request, contest):
  return {
    'contest': contest,
    'request': request
  }

@register.inclusion_tag('contest/head_contest.html')
def head(contest):
  return {
    'contest': contest
  }

@register.simple_tag
def in_contest(contest, user):
  return contest.is_in_contest(user)

@register.simple_tag
def label(contest, id):
  return contest.get_label_for_problem(id)