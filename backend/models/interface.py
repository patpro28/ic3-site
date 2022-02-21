import re

from mptt.models import MPTTModel
from mptt.fields import TreeForeignKey

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_regex(regex):
    try:
        re.compile(regex, re.VERBOSE)
    except re.error as e:
        raise ValidationError('Invalid regex: %s' % e.message)

class NavigationBar(MPTTModel):
    class Meta:
        verbose_name = _('navigation item')
        verbose_name_plural = _('navigation bar')

    class MPTTMeta:
        order_insertion_by = ['order']
    
    order = models.PositiveIntegerField(_("order"), db_index=True)
    key = models.CharField(_("identifier"), max_length=15)
    label = models.CharField(_("label"), max_length=20)
    path = models.CharField(_("link path"), max_length=255)
    regex = models.TextField(_("hightlight regex"), validators=[validate_regex])
    parent = TreeForeignKey('self', verbose_name=_('parent item'), null=True, blank=True,
                            related_name='children', on_delete=models.CASCADE)
    
    def __str__(self) -> str:
        return self.label
    
    @property
    def pattern(self, cache = {}):
        if self.regex in cache:
            return cache[self.regex]
        else:
            pattern = cache[self.regex] = re.compile(self.regex, re.VERBOSE)
            return pattern