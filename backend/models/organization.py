from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .profile import Profile


class Organization(models.Model):
    name = models.CharField(_("organization name"), max_length=128)
    slug = models.CharField(_("organization slug"), max_length=128,
                            help_text=_('Organization name shown in URL'))
    short_name = models.CharField(_("short name"), max_length=20,
                            help_text=_('Displayed beside user name during exams'))
    about = models.TextField(_("organization description"))
    admins = models.ManyToManyField("backend.profile", verbose_name=_("administrators"), related_name='admin_of',
                            help_text=_('Those who can edit this organization'))
    creation_date = models.DateTimeField(_("creation date"), auto_now_add=True)
    is_open = models.BooleanField(_("is open organization?"),
                            help_text=_('Allow joining organization'), default=True)
    slots = models.IntegerField(_("maximun size"), null=True, blank=True,
                            help_text=_('Maximun amount of users in this organization, '
                                        'only applicable to private organizations'))
    access_code = models.CharField(_("access code"), max_length=7, null=True, blank=True,
                            help_text=_('Student access code'))
    logo = models.FileField(_("Logo override image"), upload_to=None, max_length=150)


    def __contains__(self, item):
        if isinstance(item, int):
            return self.members.filter(id=item).exists()
        elif isinstance(item, Profile):
            return self.members.filter(id=item.id).exists()
        else:
            raise TypeError('Organization membership test must be Profile or primany key')
    
    def __str__(self) -> str:
        return self.name
    
    def get_absolute_url(self):
        return reverse("backend:organization_home", args=(self.id, self.slug))

    def get_users_url(self):
        return reverse('backend:organization_users', args=(self.id, self.slug))

    class Meta:
        ordering = ['name']
        permissions = (
            ('organization_admin', _('Administer organizations')),
            ('edit_all_organization', _('Edit all organizations')),
        )
        verbose_name = _('organization')
        verbose_name_plural = _('organizations')


class OrganizationRequest(models.Model):

    STATE = (
        ('P', 'Pending'),
        ('A', 'Approved'),
        ('R', 'Rejected'),
    )

    user = models.ForeignKey("backend.Profile", verbose_name=_("users"), on_delete=models.CASCADE, related_name='requests')
    organization = models.ForeignKey(Organization, verbose_name=_("organization"), related_name='requests', on_delete=models.CASCADE)
    time = models.DateTimeField(_("request time"), auto_now_add=True)
    state = models.CharField(_("state"), max_length=1, choices=STATE)

    reason = models.TextField(_("reason"))

    class Meta:
        verbose_name = _('organization join request')
        verbose_name_plural = _('organization join requests')