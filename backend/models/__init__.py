from reversion import revisions

from .profile import *
from .organization import *
from .interface import *
from .choices import *

revisions.register(Profile, exclude=['last_access',])
revisions.register(Organization)

del revisions