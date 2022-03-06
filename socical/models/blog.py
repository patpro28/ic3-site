from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class Blog(models.Model):
  title = models.CharField(_("title"), max_length=255,
                          help_text=_('Title of this post'))
  description = models.TextField(_("description"), blank=False,
                          help_text=_('Content of this post'))
  author = models.ForeignKey("backend.Profile", verbose_name=_("author"), on_delete=models.CASCADE,
                          help_text=_('Creator of this post'))
  publish = models.DateTimeField(_("publish on time"), default=timezone.now)

  visible = models.BooleanField(_("visible"), default=False)