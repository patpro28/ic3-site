from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.functional import cached_property
from django.utils.http import urlencode
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from sortedm2m.fields import SortedManyToManyField

from .choices import TIMEZONE, MATH_ENGINES_CHOICES

from backend.utils.unicode import utf8bytes

class ProfileManager(BaseUserManager):

    def create_user(self, username, fullname, password=None):
        if not username:
            raise ValueError('Username cant empty!')
        if not fullname:
            raise ValueError('Fullname cant empty!')
        user = self.model(
            username=username,
            fullname=fullname,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, fullname, password=None):
        if not username:
            raise ValueError('Username cant empty!')
        if not fullname:
            raise ValueError('Fullname cant empty!')
        user = self.create_user(
            username=username,
            fullname=fullname,
            password=password
        )
        user.is_staff = True
        user.is_superuser = True
        user.display_rank = 'admin'
        user.save(using=self._db)
        return user

    
class Profile(AbstractBaseUser, PermissionsMixin):

    DISPLAY_RANK = (
        ('user', _('Normal User')),
        ('setter', _('Problem Setter')),
        ('admin', _('Admin'))
    )

    username = models.CharField(_("Username"), max_length=30, unique=True)
    email = models.EmailField(_("Email"), max_length=254, blank=True)
    is_staff = models.BooleanField(_("is staff"), default=False)
    is_active = models.BooleanField(_("Active"), default=True)
    date_joined = models.DateTimeField(_("Date joined Emath"), default=now)
    fullname = models.CharField(_("Fullname"), max_length=50, null=False)
    timezone = models.CharField(max_length=50, verbose_name=_('location'), choices=TIMEZONE,
                                default=settings.DEFAULT_USER_TIME_ZONE)
    display_rank = models.CharField(_("display rank"), max_length=10, default='user', choices=DISPLAY_RANK)
    about = models.TextField(_("self-description"), null=True, blank=True)
    point = models.FloatField(_("point"), default=0.0)
    organizations = SortedManyToManyField('backend.Organization', verbose_name=_('organization'), blank=True,
                                            related_name='members', related_query_name='member')
    math_engine = models.CharField(verbose_name=_('math engine'), choices=MATH_ENGINES_CHOICES, max_length=4,
                                   default=settings.MATHOID_DEFAULT_TYPE,
                                   help_text=_('the rendering engine used to render math'))
    objects = ProfileManager()

    #Contest
    current_contest = models.ForeignKey("education.ContestParticipation", verbose_name=_("current contest"), 
                                        null=True, blank=True, related_name='+',on_delete=models.SET_NULL)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['fullname',]

    def __str__(self) -> str:
        return self.username

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
        ordering = ['username']