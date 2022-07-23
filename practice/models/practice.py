from django.db import models
from django.utils.translation import gettext_lazy as _

class Practice(models.Model):
  name = models.CharField(_("name"), max_length=255)
  level = models.ForeignKey("education.Level", verbose_name=_("level"), on_delete=models.CASCADE)

  def __str__(self) -> str:
    return self.name + ': ' + str(self.level)


class PracticeProblem(models.Model):
  problem = models.ForeignKey("education.Problem", verbose_name=_("problem"), on_delete=models.CASCADE, related_name='practice')
  contest = models.ForeignKey("practice.Practice", verbose_name=_("practice"), on_delete=models.CASCADE, related_name="problems")
  points = models.IntegerField(_("points"), default=1)
