import os
import errno

from django.conf import settings
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db.models.signals import post_save
from django.dispatch import receiver

from education.models.contest import ContestProblem

from .models import Problem, Contest

def get_pdf_path(basename):
    return os.path.join(settings.PDF_PROBLEM_CACHE, basename)

def unlink_if_exists(file):
    try:
        os.unlink(file)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise

@receiver(post_save, sender=Contest)
def contest_update(sender, instance, **kwargs):
  cache.delete_many([make_template_fragment_key('problem_html', (problem.problem.id, 'jax'))
                    for problem in ContestProblem.objects.filter(contest=instance)])
  unlink_if_exists(get_pdf_path('%s.pdf' % (instance.key)))


@receiver(post_save, sender=Problem)
def problem_update(sender, instance, **kwargs):
  cache.delete_many([make_template_fragment_key('problem_html', (instance.id, 'jax'))])

  for contest in ContestProblem.objects.filter(problem=instance):
    unlink_if_exists(get_pdf_path('%s.pdf' % (contest.contest.key)))
