from reversion import revisions

from .problem import *
from .contest import *
from .submission import *
from .course import *

revisions.register(Problem)
revisions.register(ProblemGroup)
revisions.register(Contest, follow=['contest_problems'])

del revisions