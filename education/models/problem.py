from email.quoprimime import unquote
from django.db import models
from django.db.models import Q, F
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from backend.models import Profile, Organization

def disallowed_characters_validator(text):
    common_disallowed_characters = set(text) & settings.PROBLEM_STATEMENT_DISALLOWED_CHARACTERS
    if common_disallowed_characters:
        raise ValidationError(_('Disallowed characters: %(value)s'),
                              params={'value': ''.join(common_disallowed_characters)})


class ProblemGroup(models.Model):
    name = models.CharField(_("Fullname"), max_length=100, unique=True)
    short_name = models.CharField(_("Short name"), max_length=20)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name = _('problem group')
        verbose_name_plural = _('problem groups')

class Problem(models.Model):
    DIFFICULT = (
        ('newbie', _('Newbie')),
        ('amateur', _('Amateur')),
        ('expert', _('Expert')),
        ('cmaster', _('Candidate Master')),
        ('master', _('Master')),
        ('gmaster', _('Grandmaster'))
    )
    code = models.CharField(_("problem code"), max_length=20, unique=True,
                            validators=[RegexValidator('^[a-z0-9]+$', _('Problem code must be ^[a-z0-9]+$'))],
                            help_text=_('A short, unique code for the problem, '
                                        'used in the url after /problem/'))
    name = models.CharField(_("problem name"), max_length=100, db_index=True,
                            help_text=_('The full name of the problem, '
                                        'as shown in the problem list.'))
    authors = models.ManyToManyField(Profile, verbose_name=_("authors"), blank=True, related_name=_("authors"),
                            help_text=_('These users will be able to edit the problem, '
                                                 'and be listed as authors.'))
    description = models.TextField(verbose_name=_('problem body'), validators=[disallowed_characters_validator])
    # answer = models.ManyToManyField(Answer, verbose_name=_("answers of problem"))
    number_answer = models.IntegerField(_("Number of answer"), default=0)
    is_public = models.BooleanField(verbose_name=_('publicly visible'), db_index=True, default=False)
    organizations = models.ManyToManyField(Organization, blank=True, verbose_name=_('organizations'),
                                           help_text=_('If private, only these organizations may see the problem.'))
    is_organization_private = models.BooleanField(verbose_name=_('private to organizations'), default=False)

    group = models.ForeignKey(ProblemGroup, verbose_name=_("group"), 
                            help_text=_('The group of problem, shown under Category in the problem list.'), on_delete=models.CASCADE)
    
    difficult = models.CharField(_("Difficult of problem"), max_length=10, default='newbie', choices=DIFFICULT)
    
    is_full_markup = models.BooleanField(verbose_name=_('allow full markdown access'), default=False)

    class Meta:
        verbose_name = _("Math Problem")
        verbose_name_plural = _("Math Problems")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('education:problem_detail', kwargs={'problem': self.code})
        
    @classmethod
    def get_visible_problems(cls, user):
        if not user.is_authenticated:
            return cls.get_public_problems
        
        queryset = cls.objects.defer('description')
        if not (user.has_perm('education.view_private_problem') or user.has_perm('education.edit_all_problem')):
            q = Q(is_public=True)
            if not (user.has_perm('education.see_organization_problem') or user.has_perm('education.edit_public_problem')):
                q &= (
                    Q(is_organization_private=False) or
                    Q(is_organization_private=True, organizations__in=user.organizations.all())
                )
            if user.has_perm('education.edit_own_problem'):
                q |= Q(is_organization_private=True, organizations__in=user.admin_of.all())
            q |= Q(authors=user)
            queryset = queryset.filter(q)

        return queryset


    @classmethod
    def get_public_problems(cls):
        return cls.objects.filter(is_public=True, is_organization_private=False).defer('description')

    @classmethod
    def get_editable_problems(cls, user):
        if not user.has_perm('education.edit_own_problem'):
            return cls.objects.none()
        if user.has_perm('education.edit_all_problem'):
            return cls.objects.all()
        
        q = Q(authors=user)
        q |= Q(is_organization_private=True, organizations__in=user.admin_of.all())

        if user.has_perm('education.edit_public_problem'):
            q |= Q(is_public=True)
        
        return cls.objects.filter(q)

    @cached_property
    def author_ids(self):
        return Problem.authors.through.objects.filter(problem=self).values_list('profile_id', flat=True)

    def is_editable_by(self, user):
        if not user.is_authenticated:
            return False
        if user.has_perm('education.edit_all_problem') or user.has_perm('education.edit_public_problem') and self.is_public:
            return True
        return user.has_perm('education.edit_own_problem') and \
            (user.id in self.author_ids or
                self.is_organization_private and self.organizations.filter(admins=user).exists())

    @property
    def markdown_style(self):
        return 'problem-full' if self.is_full_markup else 'problem'

    class Meta:
        permissions = (
            ('view_private_problem', _('View private Math problems')),
            ('edit_own_problem', _('Edit own Math problems')),
            ('edit_all_problem', _('Edit all Math problems')),
            ('edit_public_problem', _('Edit all public Math problems')),
            ('see_organization_problem', _('See organizations-private Math problems')),
            ('change_public_visibility', _('Change public math problem visibility'))
        )


class Answer(models.Model):
    problem = models.ForeignKey(Problem, verbose_name=_("problem"), related_name='answers', null=True, on_delete=models.CASCADE)
    description = models.CharField(_("Content"), max_length=100, blank=False)
    is_correct = models.BooleanField(_("Correct answer"), default=False)

