from django import template
from education.models import ContestProblem
from practice.models.practice import PracticeProblem

register = template.Library()

@register.inclusion_tag('problem/multiple_choices.html')
def mc(problem, answers):
  if isinstance(problem, ContestProblem) or isinstance(problem, PracticeProblem):
    markdown = problem.problem.markdown_style
  else:
    markdown = problem.markdown_style
  return {
    'answers': answers,
    'index': problem.id,
    'markdown': markdown,
  }

@register.inclusion_tag('problem/fill_answer.html')
def fill(problem, answers):
  return {
    'index': problem.id,
    'max_length': len(answers[0][1])
  }