import itertools
import json

# from django.utils.http import urlquote
from jinja2.ext import Extension
from mptt.utils import get_cached_trees
# from statici18n.templatetags.statici18n import inlinei18n

from . import (datetime, gravatar, markdown, reference, render,
               spaceless, timedelta)
from . import registry

registry.function('str', str)
registry.filter('str', str)
registry.filter('json', json.dumps)
# registry.filter('urlquote', urlquote)
registry.filter('roundfloat', round)
# registry.function('inlinei18n', inlinei18n)
registry.function('mptt_tree', get_cached_trees)


@registry.function
def counter(start=1):
    return itertools.count(start).__next__


class EmathExtension(Extension):
    def __init__(self, env):
        super(EmathExtension, self).__init__(env)
        env.globals.update(registry.globals)
        env.filters.update(registry.filters)
        env.tests.update(registry.tests)
