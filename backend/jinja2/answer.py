from . import registry

@registry.function
@registry.render_with('problem/multiple_choices.html')
def mc(problem, answers):
  return {
    'answers': answers,
    'index': problem.id,
    'markdown': problem.problem.markdown_style
  }

@registry.function
@registry.render_with('problem/fill_answer.html')
def fill(problem, answers):
  return {
    'index': problem.id,
    'max_length': len(answers[0][1])
  }