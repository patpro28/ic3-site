from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from martor.models import MartorField

from sortedm2m.fields import SortedManyToManyField

from .choices import TIMEZONE, MATH_ENGINES_CHOICES

class ProfileManager(BaseUserManager):

    def create_user(self, username, fullname, password=None):
        if not username:
            raise ValueError('Username cant empty!')
        if not fullname:
            raise ValueError('Fullname cant empty!')
        user = self.model(
            username=username,
            fullname=fullname,
            display_rank='user'
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
    is_staff = models.BooleanField(_("Is staff"), default=False)
    is_superuser = models.BooleanField(_("Is superuser"), default=False)
    is_active = models.BooleanField(_("Active"), default=True)
    date_joined = models.DateTimeField(_("Date joined Emath"), default=now)
    fullname = models.CharField(_("Fullname"), max_length=50, null=False)
    timezone = models.CharField(max_length=50, verbose_name=_('location'), choices=TIMEZONE,
                                default=settings.DEFAULT_USER_TIME_ZONE)
    display_rank = models.CharField(_("display rank"), max_length=10, choices=DISPLAY_RANK)
    last_access = models.DateTimeField(_("last access time"), default=now)
    about = MartorField(_("self-description"), null=True, blank=True)
    math_engine = models.CharField(_("math engine"), max_length=4, choices=MATH_ENGINES_CHOICES,
                                default=settings.MATHOID_DEFAULT_TYPE,
                                help_text=_('the rendering engine used to render math'))

    organizations = SortedManyToManyField('backend.Organization', verbose_name=_('organization'), blank=True,
                                            related_name='members', related_query_name='member')
    
    objects = ProfileManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['fullname',]

    def __str__(self) -> str:
        return self.username

    def get_absolute_url(self):
        return reverse("user_page", kwargs={"user": self.username})
    

