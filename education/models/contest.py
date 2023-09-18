from django.db import models, transaction
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import gettext_lazy as _, gettext
from django.utils.functional import cached_property
from django.utils import timezone
from django.db.models import Q, F

from backend.models import Profile, Organization, User
from .problem import Problem
from education import contest_format


class Contest(models.Model):
    SCOREBOARD_VISIBLE = 'V'
    SCOREBOARD_AFTER_CONTEST = 'C'
    SCOREBOARD_AFTER_PARTICIPATION = 'P'
    SCOREBOARD_VISIBILITY = (
        (SCOREBOARD_VISIBLE, _('Visible')),
        (SCOREBOARD_AFTER_CONTEST, _('Hidden for duration of contest')),
        (SCOREBOARD_AFTER_PARTICIPATION, _('Hidden for duration of participation')),
    )
    key = models.CharField(max_length=20, verbose_name=_('contest id'), unique=True,
                           validators=[RegexValidator('^[a-z0-9]+$', _('contest id must be ^[a-z0-9]+$'))])
    name = models.CharField(max_length=100, verbose_name=_('contest name'), db_index=True)
    authors = models.ManyToManyField(Profile, help_text=_('These users will be able to edit the contest.'),
                                     related_name='authors+')
    curators = models.ManyToManyField(Profile, help_text=_('These users will be able to edit the contest, '
                                                           'but will not be listed as authors.'),
                                      related_name='curators+', blank=True)
    description = models.TextField(verbose_name=_('description'), blank=True)
    problems = models.ManyToManyField(Problem, verbose_name=_('problems'), through='ContestProblem')
    start_time = models.DateTimeField(verbose_name=_('start time'), db_index=True)
    end_time = models.DateTimeField(verbose_name=_('end time'), db_index=True)
    is_visible = models.BooleanField(verbose_name=_('publicly visible'), default=False,
                                     help_text=_('Should be set even for organization-private contests, where it '
                                                 'determines whether the contest is visible to members of the '
                                                 'specified organizations.'))
    view_contest_scoreboard = models.ManyToManyField(Profile, verbose_name=_('view contest scoreboard'), blank=True,
                                                     related_name='view_contest_scoreboard',
                                                     help_text=_('These users will be able to view the scoreboard.'))
    scoreboard_visibility = models.CharField(verbose_name=_('scoreboard visibility'), default=SCOREBOARD_VISIBLE,
                                             max_length=1, help_text=_('Scoreboard visibility through the duration '
                                                                       'of the contest'), choices=SCOREBOARD_VISIBILITY)
    is_private = models.BooleanField(verbose_name=_('private to specific users'), default=False)
    private_contestants = models.ManyToManyField(Profile, blank=True, verbose_name=_('private contestants'),
                                                 help_text=_('If private, only these users may see the contest'),
                                                 related_name='private_contestants+')
    is_organization_private = models.BooleanField(verbose_name=_('private to organizations'), default=False)
    organizations = models.ManyToManyField(Organization, blank=True, verbose_name=_('organizations'),
                                           help_text=_('If private, only these organizations may see the contest'))
    og_image = models.CharField(verbose_name=_('OpenGraph image'), default='', max_length=150, blank=True)
    logo_override_image = models.CharField(verbose_name=_('Logo override image'), default='', max_length=150,
                                           blank=True,
                                           help_text=_('This image will replace the default site logo for users '
                                                       'inside the contest.'))
    # tags = models.ManyToManyField(contestTag, verbose_name=_('contest tags'), blank=True, related_name='contests')
    user_count = models.IntegerField(verbose_name=_('the amount of live participants'), default=0)
    summary = models.TextField(blank=True, verbose_name=_('contest summary'),
                               help_text=_('Plain-text, shown in meta description tag, e.g. for social media.'))
    access_code = models.CharField(verbose_name=_('access code'), blank=True, default='', max_length=255,
                                   help_text=_('An optional code to prompt contestants before they are allowed '
                                               'to join the contest. Leave it blank to disable.'))
    banned_users = models.ManyToManyField(Profile, verbose_name=_('personae non gratae'), blank=True,
                                          help_text=_('Bans the selected users from joining this contest.'))
    format_name = models.CharField(verbose_name=_('contest format'), default='default', max_length=32,
                                   choices=contest_format.choices(), help_text=_('The contest format module to use.'))
    problem_label_script = models.TextField(verbose_name='contest problem label script', blank=True,
                                            help_text='A custom Lua function to generate problem labels. Requires a '
                                                      'single function with an integer parameter, the zero-indexed '
                                                      'contest problem index, and returns a string, the label.')
    points_precision = models.IntegerField(verbose_name=_('precision points'), default=3,
                                           validators=[MinValueValidator(0), MaxValueValidator(10)],
                                           help_text=_('Number of digits to round points to.'))

    def __str__(self) -> str:
        return self.name
    
    def get_absolute_url(self):
        return reverse("education:contest_detail", kwargs={'contest': self.key})
    
    @property
    def contest_window_length(self):
        return self.end_time - self.start_time

    @cached_property
    def _now(self):
        return timezone.now()

    @cached_property
    def format_class(self):
        return contest_format.formats[self.format_name]
    
    @cached_property
    def format(self):
        return self.format_class(self)
    
    @cached_property
    def get_label_for_problem(self):
        return self.format.get_label_for_problem

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('What is this? A contest that ended before it starts?')

        try:
            label = self.get_label_for_problem(0)
        except Exception as e:
            raise ValidationError('Contest problem label script: %s' % e)
        else:
            if not isinstance(label, str):
                raise ValidationError('Contest problem label script: script should return a string.')

    @cached_property
    def ended(self):
        return self.end_time < self._now

    @cached_property
    def can_join(self):
        return self.start_time <= self._now
        
    @property
    def time_before_start(self):
        if self.start_time >= self._now:
            return self.start_time - self._now
        else:
            return None

    @property
    def time_before_end(self):
        if self.end_time >= self._now:
            return self.end_time - self._now
        else:
            return None

    @cached_property
    def author_ids(self):
        return Contest.authors.through.objects.filter(contest=self).values_list('profile_id', flat=True)
    
    @cached_property
    def editor_ids(self):
        return self.author_ids.union(
            Contest.curators.through.objects.filter(contest=self).values_list('profile_id', flat=True)
        )

    def update_user_count(self):
        self.user_count = self.users.filter(virtual=0).count()
        self.save()

    update_user_count.alters_data = True

    class Inaccessible(Exception):
        pass

    class PrivateContest(Exception):
        pass

    def access_check(self, user: User):
        if not user.is_authenticated:
            if not self.is_visible:
                raise self.Inaccessible()
            if self.is_private or self.is_organization_private:
                raise self.PrivateContest()
            return
        
        profile = user.profile

        if user.has_perm('education.see_private_contest') or user.has_perm('education.edit_all_contest'):
            return
        
        if profile.id in self.editor_ids:
            return
        
        if not self.is_visible:
            raise self.Inaccessible()
        
        if not self.is_private and not self.is_organization_private:
            return

        if self.view_contest_scoreboard.filter(id=profile.id).exists():
            return

        in_org = self.organizations.filter(id__in=profile.organizations.all()).exists()
        in_users = self.private_contestants.filter(id=profile.id).exists()

        if self.is_private and not self.is_organization_private:
            if in_users:
                return
            raise self.PrivateContest()
        
        if self.is_private and self.is_organization_private:
            if in_org and in_users:
                return
            raise self.PrivateContest()
        
    def is_accessible_by(self, user: User):
        try:
            self.access_check(user)
        except (self.Inaccessible, self.PrivateContest):
            return False
        else:
            return True
        
    def has_completed_contest(self, user: User):
        if user.is_authenticated:
            participation = self.users.filter(virtual=ContestParticipation.LIVE, user=user.profile).first()
            if participation and participation.ended:
                return True
        return False

    @cached_property
    def show_scoreboard(self):
        if not self.can_join:
            return False
        if (self.scoreboard_visibility in (self.SCOREBOARD_AFTER_CONTEST, self.SCOREBOARD_AFTER_PARTICIPATION) and
                not self.ended):
            return False
        return True

    def is_in_contest(self, user: User):
        if user.is_authenticated:
            return user and user.profile.current_contest is not None and user.profile.current_contest.contest == self
        return False

    def can_see_own_scoreboard(self, user: User):
        if self.can_see_full_scoreboard(user):
            return True
        if not self.can_join:
            return False
        if not self.show_scoreboard and not self.is_in_contest(user):
            return False
        return True

    def can_see_full_scoreboard(self, user: User):
        if self.show_scoreboard:
            return True
        if not user.is_authenticated:
            return False
        if user.has_perm('education.see_private_contest') or user.has_perm('education.edit_all_contest'):
            return True
        if user.id in self.editor_ids:
            return True
        if self.view_contest_scoreboard.filter(id=user.profile.id).exists():
            return True
        if self.scoreboard_visibility == self.SCOREBOARD_AFTER_PARTICIPATION and self.has_completed_contest(user):
            return True
        return False

    @classmethod
    def get_visible_contests(cls, user: User):
        if not user.is_authenticated:
            return cls.objects.filter(is_visible=True, is_organization_private=False, is_private=False) \
                .defer('description').distinct()
        queryset = cls.objects.defer('description')
        profile = user.profile
        if not (user.has_perm('education.see_private_contest') or user.has_perm('education.edit_all_contest')):
            q = Q(is_visible=True)
            q &= (
                Q(view_contest_scoreboard=profile) |
                Q(is_organization_private=False, is_private=False) |
                Q(is_organization_private=False, is_private=True, private_contestants=profile) |
                Q(is_organization_private=True, is_private=False, organizations__in=profile.organizations.all()) |
                Q(is_organization_private=True, is_private=True, organizations__in=profile.organizations.all(),
                  private_contestants=profile)
            )
            q |= Q(authors=profile)
            q |= Q(curators=profile)
            queryset = queryset.filter(q)
        return queryset.distinct()

    def is_editable_by(self, user: User):
        if user.has_perm('education.edit_all_contest'):
            return True
        
        if user.has_perm('education.edit_own_contest') and user.profile.id in self.editor_ids:
            return True
        
        return False

    class Meta:
        permissions = (
            ('see_private_contest', _('See private contests')),
            ('edit_own_contest', _('Edit own contests')),
            ('edit_all_contest', _('Edit all contest')),
            ('clone_contest', _('Clone contest')),
            ('contest_rating', _('Rate contests')),
            ('create_private_contest', _('Create private contests')),
            ('change_contest_visibility', _('Change contest visibility')),
            ('contest_problem_label', _('Edit contest problem label script')),
            ('lock_contest', _('Change lock status of contest'))
        )
        verbose_name = _('contest')
        verbose_name_plural = _('contests')


class ContestParticipation(models.Model):
    LIVE = 0
    SPECTATE = -1
    
    contest = models.ForeignKey("education.Contest", verbose_name=_("contest"), on_delete=models.CASCADE,
                                related_name='users')
    user = models.ForeignKey("backend.Profile", verbose_name=_("user"), on_delete=models.CASCADE,
                                related_name='contest_history')
    score = models.FloatField(_("Participation's score"), default=0)

    real_start = models.DateTimeField(_("start time"), default=timezone.now, db_column='start')
    cumtime = models.PositiveIntegerField(_("cumulative time"), default=0)
    is_disqualified = models.BooleanField(_("is disqualified"), default=False,
                                help_text=_('Whether this participation is disqualified.'))
    tiebreaker = models.FloatField(_("tie-breaker field"), default=0.0)
    virtual = models.IntegerField(_("virtual participation id"), default=LIVE,
                                help_text=_('0 means non-virtual, otherwise the n-th virtual participation.'))
    format_data = models.JSONField(_("contest format specific data"), null=True, blank=True)

    def recompute_results(self):
        with transaction.atomic():
            self.contest.format.update_participation(self)
            if self.is_disqualified:
                self.score = -9999
                self.save(update_fields=['score'])
    recompute_results.alters_data = True

    def set_disqualified(self, disqualified):
        self.is_disqualified = disqualified
        self.recompute_results()
        if self.is_disqualified:
            if self.user.current_contest == self:
                self.user.remove_contest()
            self.contest.banned_users.add(self.user)
        else:
            self.contest.banned_users.remove(self.user)
    set_disqualified.alters_data = True

    @cached_property
    def _now(self):
        return timezone.now()
    
    @property
    def live(self):
        return self.virtual == self.LIVE
    
    @property
    def spectate(self):
        return self.virtual == self.SPECTATE

    @cached_property
    def start(self):
        contest = self.contest
        return contest.start_time if self.live or self.spectate else self.real_start

    def __str__(self) -> str:
        fullname = self.user.fullname if self.user.fullname else self.user.username
        if self.spectate:
            return gettext('%(fullname)s spectating in %(contest)s' % {
                'fullname': fullname, 
                'contest' : self.contest.name
            })
        if self.virtual:
            return gettext('%(fullname)s in %(contest)s, v%(virtual)d' % {
                'fullname': fullname, 
                'contest' : self.contest.name, 
                'virtual' : self.virtual
            })
        return gettext('%(fullname)s in %(contest)s' % {
            'fullname': fullname, 
            'contest' : self.contest.name
        })
    
    @cached_property
    def end_time(self):
        contest = self.contest
        if self.spectate:
            return contest.end_time
        if self.virtual:
            return self.real_start + (contest.end_time - contest.start_time)
        return contest.end_time

    @property
    def ended(self):
        return self.end_time is not None and self.end_time < self._now
    
    @property
    def time_remaining(self):
        end = self.end_time
        if end is not None and end >= self._now:
            return end - self._now

    class Meta:
        verbose_name = _('contest participation')
        verbose_name_plural = _('contest participations')

        unique_together = ('contest', 'user', 'virtual')


class ContestProblem(models.Model):
    problem = models.ForeignKey("education.Problem", verbose_name=_("problem"), related_name='contests', on_delete=models.CASCADE)
    contest = models.ForeignKey("education.Contest", verbose_name=_("contest"), related_name='contest_problems', on_delete=models.CASCADE)
    points = models.IntegerField(_("point"))
    order = models.PositiveIntegerField(_("order"), db_index=True)

    class Meta:
        unique_together = ('problem', 'contest')
        verbose_name = _('contest problem')
        verbose_name_plural = _('contest problems')
        ordering = ('order',)


class ContestSolution(models.Model):
    contest = models.ForeignKey("education.Contest", verbose_name=_("contest"), on_delete=models.SET_NULL, 
                                related_name='solution', null=True, blank=True)
    authors = models.ManyToManyField("backend.Profile", verbose_name=_("authors"))
    publish_on = models.DateTimeField(verbose_name=_('publish date'))
    is_full_markup = models.BooleanField(_('markup full'), default=False)
    is_public = models.BooleanField(verbose_name=_('public visibility'), default=False)
    content = models.TextField(_("editorial content"))

    @property
    def markdown_style(self):
        return 'description-full' if self.is_full_markup else 'description'
    
    def __str__(self):
        return _('Editorial for %s') % self.contest.name

    def is_accessiable_by(self, user: Profile):
        if self.is_public and self.publish_on < timezone.now():
            return True
        if self.contest.is_editable_by(user):
            return True
        return False