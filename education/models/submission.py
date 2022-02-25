from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

SUBMISSION_RESULT = (
    ('AC', _('Accepted')),
    ('WA', _('Wrong Answer'))
)

class Submission(models.Model):
    RESULT = SUBMISSION_RESULT

    user = models.ForeignKey("backend.Profile", verbose_name=_("user"), on_delete=models.CASCADE)
    contest = models.ForeignKey("education.Contest", verbose_name=_("contest"), on_delete=models.CASCADE)
    time = models.FloatField(_("completion time"), null=True, db_index=True)
    points = models.FloatField(_("points granted"), null=True, db_index=True)
    result = models.CharField(_("result"), max_length=3, choices=SUBMISSION_RESULT, 
                              default=None, null=True, blank=True, db_index=True)
    
    @property
    def result_class(self):
        return self.result
    
    def __str__(self) -> str:
        return 'Submission %d of %s by %s' % (self.id, self.contest.name, self.user.fullname)

    def get_absolute_url(self):
        return reverse("submission_status", kwargs={"pk": self.pk})
    
    class Meta:
        permissions = (
            ('view_all_submission', _('View all submission')),
        )
        verbose_name = _('submission')
        verbose_name_plural = _('submissions')


class SubmissionProblem(models.Model):
    submission = models.ForeignKey("education.Submission", verbose_name=_("submission"), on_delete=models.CASCADE)
    problem = models.ForeignKey("education.ContestProblem", verbose_name=_("problem"), on_delete=models.CASCADE)
    result = models.BooleanField(_("result"), default=False)
    points = models.FloatField(_("points granted"), null=True)
    output = models.TextField(_("student's answer"), blank=True)

    class Meta:
        unique_together = ('submission', 'problem')
        verbose_name = _('submission problem')
        verbose_name_plural = _('submission problems')