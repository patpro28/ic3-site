from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from .choices import MATH_ENGINES_CHOICES, TIMEZONE


class User(AbstractUser):
    username_validator = ASCIIUsernameValidator()

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 ASCII characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )

    REQUIRED_FIELDS = []

    
class Profile(models.Model):

    DISPLAY_RANK = (
        ('user', _('Normal User')),
        ('setter', _('Problem Setter')),
        ('admin', _('Admin'))
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name=_("user"), on_delete=models.CASCADE, related_name='profile')

    timezone = models.CharField(max_length=50, verbose_name=_('location'), choices=TIMEZONE,
                                default=settings.DEFAULT_USER_TIME_ZONE)
    display_rank = models.CharField(_("display rank"), max_length=10, default='user', choices=DISPLAY_RANK)
    about = models.TextField(_("self-description"), null=True, blank=True)
    point = models.FloatField(_("point"), default=0.0)
    organizations = models.ManyToManyField('backend.Organization', verbose_name=_('organization'), blank=True,
                                            related_name='members', related_query_name='member')
    math_engine = models.CharField(verbose_name=_('math engine'), choices=MATH_ENGINES_CHOICES, max_length=4,
                                   default=settings.MATHOID_DEFAULT_TYPE,
                                   help_text=_('the rendering engine used to render math'))
    # status = models.BooleanField(_("status"), default=False)
    #Contest
    current_contest = models.ForeignKey("education.ContestParticipation", verbose_name=_("current contest"), 
                                        null=True, blank=True, related_name='+',on_delete=models.SET_NULL)


    @property
    def username(self):
        return self.user.username

    def __str__(self) -> str:
        return self.username

    @cached_property
    def css_class(self):
        return 'newbie'
    
    @property
    def fullname(self):
        return self.user.get_full_name() or self.username

    def get_absolute_url(self):
        return reverse("user_page", kwargs={"user": self.username})
    
    @cached_property
    def organization(self):
        orgs = self.organizations.all()
        return orgs.first() if orgs else None

    def remove_contest(self):
        self.current_contest = None
        self.save(update_fields=['current_contest'])
    
    remove_contest.alters_data = True

    def update_contest(self):
        contest = self.current_contest
        if contest is not None and (contest.ended or not contest.contest.is_accessible_by(self)):
            self.remove_contest()
    
    update_contest.alters_data = True

    class Meta:
        ordering = ['user__username']