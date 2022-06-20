from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils.functional import cached_property

from education.models.problem import Answer

SUBMISSION_RESULT = (
    ('AC', _('Accepted')),
    ('WA', _('Wrong Answer')),
    ('PE', _('Pending'))
)

RESULT_CLASS = {
    'AC': 'accept',
    'WA': ['wrong3', 'wrong5', 'wrong7', 'wrong9', 'pre_accept'],
    'PE': 'pending'
}

WRONG_LEVEL = (0.3, 0.5, 0.7, 0.9, 1)

def get_result_html(result, index, point):
    style = RESULT_CLASS.get(result, None)
    if style is None:
        return format_html('<td>???</td>')
    return format_html('<td class="center aligned {style}"><div class="ui header">{point}'
                        '</div></td>',
        style=style[index] if result == 'WA' else style,
        point=round(point, 2) if result != 'PE' else '---',
        # result=result
    )

class Submission(models.Model):
    RESULT = SUBMISSION_RESULT

    user = models.ForeignKey("education.ContestParticipation", verbose_name=_("user"), 
                             related_name='submissions', on_delete=models.CASCADE, null=True)
    profile = models.ForeignKey("backend.Profile", verbose_name=_("profile"), related_name='submissions', on_delete=models.CASCADE, null=True)
    contest = models.ForeignKey("education.Contest", verbose_name=_("contest"), on_delete=models.CASCADE, null=True)
    problem = models.ForeignKey("education.Problem", verbose_name=_("problem"), on_delete=models.CASCADE, null=True)
    is_contest = models.BooleanField(_('is contest'), default=True)
    date = models.DateTimeField(_('submission time'), auto_now_add=True, db_index=True)
    time = models.DateTimeField(_("completion time"), null=True, db_index=True)
    points = models.FloatField(_("points granted"), null=True, db_index=True, default=0.0)
    result = models.CharField(_("result"), max_length=3, choices=SUBMISSION_RESULT, 
                              default=None, null=True, blank=True, db_index=True)
    max_points = models.FloatField(_('max points'), null=True, db_index=True, default=1.0)
    
    @property
    def result_class(self):
        if self.result != 'WA':
            return get_result_html(self.result, 0, 100)
        for idx, level in enumerate(WRONG_LEVEL):
            if self.points < self.max_points * level:
                points = self.points * 100
                k = round(points / self.max_points)
                if points == k * self.max_points:
                    return get_result_html(self.result, idx, int(points / self.max_points))
                else:
                    return get_result_html(self.result, idx, float("{:.1f}".format(points / self.max_points)))

        return format_html('<td>???</td>')
    
    @property
    def time_excute(self):
        if self.time:
            return self.time - self.date
        return None
    
    def __str__(self) -> str:
        return 'Submission %d of %s by %s' % (self.id, self.contest.name, self.user.user.fullname)

    def get_absolute_url(self):
        return reverse("submission_status", kwargs={"pk": self.pk})

    def judge(self):
        self.points = 0.0
        self.max_points = 0.0
        if self.is_contest:
            for problem in self.contest.contest_problems.all():
                self.max_points += problem.points
            for problem in self.problems.all():
                problem.calculator()
                self.points += problem.points
            self.result = 'AC' if self.points == self.max_points else 'WA'
        else:
            self.max_points = 100
            for problem in self.problems.all():
                problem.calculatorTask()
                self.points += problem.points
            self.result = 'AC' if self.points == 100 else 'WA'
        self.save(update_fields=['points', 'max_points', 'result'])
    judge.alters_data = True
    
    def update_contest(self):
        self.user.recompute_results()

    class Meta:
        permissions = (
            ('view_all_submission', _('View all submission')),
            ('view_output_submission', _('View user submission output'))
        )
        verbose_name = _('submission')
        verbose_name_plural = _('submissions')


class SubmissionProblem(models.Model):
    submission = models.ForeignKey("education.Submission", verbose_name=_("submission"), 
                                   related_name='problems', on_delete=models.CASCADE)
    problem = models.ForeignKey("education.ContestProblem", verbose_name=_("contest problem"), on_delete=models.CASCADE, null=True)
    task = models.ForeignKey("education.Problem", verbose_name=_("problem"), on_delete=models.CASCADE, null=True)
    result = models.BooleanField(_("result"), default=False)
    points = models.FloatField(_("points granted"), null=True)
    output = models.TextField(_("student's answer"), blank=True)

    def calculator(self):
        if self.problem.problem.answer_type == 'mc':
            answer = Answer.objects.get(problem=self.problem.problem, is_correct=True)
        if self.problem.problem.answer_type == 'fill':
            answer = Answer.objects.filter(problem=self.problem.problem).first()
        self.result = answer.description == self.output
        if self.result:
            self.points = self.problem.points
        else:
            self.points = 0
        self.save(update_fields=['result', 'points'])
    calculator.alters_data = True
    
    def calculatorTask(self):
        if self.task.answer_type == 'mc':
            answer = Answer.objects.get(problem=self.task, is_correct=True)
        if self.task.answer_type == 'fill':
            answer = Answer.objects.filter(problem=self.task).first()
        self.result = answer.description == self.output
        if self.result:
            self.points = 100
        else:
            self.points = 0
        self.save(update_fields=['result', 'points'])
    calculatorTask.alters_data = True

    @cached_property
    def get_long_status(self):
        if self.result:
            return 'Correct'
        return 'Wrong'

    class Meta:
        unique_together = ('submission', 'problem')
        verbose_name = _('submission problem')
        verbose_name_plural = _('submission problems')