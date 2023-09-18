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
  publish = models.DateTimeField(_("publish on time"), auto_now_add=True)

  visible = models.BooleanField(_("visible"), default=False)

  def is_editable_by(self, user):
    if not user.is_authenticated:
        return False
    if user.has_perm('social.edit_all_post'):
        return True
    return user.has_perm('social.change_blogpost') and self.authors.filter(id=user.profile.id).exists()

  class Meta:
    permissions = (
      ('edit_all_post', _('Edit all post')),
      ('change_blogpost', _('Change blogpost')),
    )