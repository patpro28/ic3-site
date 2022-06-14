from django import template

register = template.Library()

@register.inclusion_tag('problem/multiple_choices.html')
def mc(problem, answers):
  return {
    'answers': answers,
    'index': problem.id,
    'markdown': problem.problem.markdown_style
  }

@register.inclusion_tag('problem/fill_answer.html')
def fill(problem, answers):
  return {
    'index': problem.id,
    'max_length': len(answers[0][1])
  }