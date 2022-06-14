from django import template

register = template.Library()

@register.inclusion_tag('title.html', takes_context=True)
def title(context, title=None):
  return {
    'content_title': context['content_title'] if 'content_title' in context else None,
    'title': title if title is not None else context['title']
  }

class SetNewVariable(template.Node):
  def __init__(self, name, value) -> None:
    self.name = name
    self.value = value
  def render(self, context) -> str:
    context[self.name] = self.value
    return ''
  
@register.tag(name='set')
def do_set(parser, token):
  try:
    tag_name, name, value = token.split_contents()
  except ValueError:
    raise template.TemplateSyntaxError(
      "%r tag requires exactly two arguments" % token.contents.split()[0]
    )
  return SetNewVariable(name, value)