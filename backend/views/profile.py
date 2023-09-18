from django.utils.functional import cached_property
from django.http import Http404, HttpResponseRedirect
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView, FormView, CreateView
from django.contrib.auth.views import (
    redirect_to_login, 
    LoginView as BaseLoginView, 
    LogoutView as BaseLogoutView,
    PasswordChangeView as BasePasswordChangeView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.core.exceptions import PermissionDenied

from reversion import revisions

from backend.models import Profile
from backend.utils.views import TitleMixin, generic_message, QueryStringSortMixin, DiggPaginatorMixin
from backend.forms import EditProfileForm, RegisterForm, LoginForm

class UserMixin(object):
    model = Profile
    slug_field = 'user__username'
    slug_url_kwarg = 'user'
    context_object_name = 'user'

    @cached_property
    def can_edit(self):
        if self.object.user == self.request.user or self.request.user.is_superuser:
            return True
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_edit"] = self.can_edit
        return context
    


class UserPage(TitleMixin, UserMixin, DetailView):
    template_name = 'user/user-page.html'

    def get_object(self, queryset = None):
        if self.kwargs.get(self.slug_url_kwarg, None) is None:
            return self.request.user.profile
        return super(UserPage, self).get_object(queryset)

    def dispatch(self, request, *args, **kwargs):
        if self.get(self.slug_url_kwarg, None) is None:
            if not self.request.user.is_authenticated:
                return redirect_to_login(self.request.get_full_path())
        try:
            return super(UserPage, self).dispatch(request, *args, **kwargs)
        except Http404:
            return generic_message(request, _('No such user'), _('No user handle "%s".') %
                                   self.kwargs.get(self.slug_url_kwarg, None)) 
    
    def get_title(self):
        return (_('My account') if self.request.profile == self.object else 
                _('User %s') % self.object.user.username)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.request.user.is_authenticated:
            raise Http404()
        return context
    

class UserList(QueryStringSortMixin, DiggPaginatorMixin, TitleMixin, ListView):
    model = Profile
    title = _('Leaderboard')
    context_object_name = 'users'
    template_name = 'user/list.html'
    paginate_by = 50
    all_sorts = frozenset(('user__username'))
    default_desc = all_sorts
    default_sort = 'user__username'

    def get_queryset(self):
        return Profile.objects.order_by(self.order).only('display_rank', 'user__username')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = context['users']
        start = self.paginate_by * (context['page_obj'].number - 1)
        context['users'] = []
        for user in users:
            start += 1
            context['users'].append((start, user))
        context['first_page_href'] = '.'
        context.update(self.get_sort_context())
        context.update(self.get_sort_paginate_context())
        return context


class EditProfile(LoginRequiredMixin, TitleMixin, UserMixin, UpdateView):
    template_name = "user/edit_profile.html"
    form_class = EditProfileForm

    def get_title(self):
        return _('Editing %s') % self.object.fullname

    def get_object(self, queryset=None):
        user = super().get_object(queryset)
        if not self.request.user.is_superuser and self.request.profile != user:
            raise PermissionDenied()
        return user

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        return form

    def form_valid(self, form):
        with revisions.create_revision(atomic=True):
            revisions.set_comment(_('Edited from site'))
            revisions.set_user(self.request.user)
            return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except PermissionDenied:
            return generic_message(request, _("Can't edit user"),
                                   _('You are not allowed to edit this user.'), status=403)


class RegistrationView(TitleMixin, CreateView, SuccessMessageMixin):
    form_class = RegisterForm
    template_name = 'user/register.html'
    success_url = '/'
    success_message = _('Your user registration was successful.')
    model = Profile
    title = _('Register')

    def form_valid(self, form):
        output = super().form_valid(form)
        login(self.request, self.object)
        return output


    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(request.profile.get_absolute_url())
        return super().dispatch(request, *args, **kwargs)


class LoginView(TitleMixin, BaseLoginView):
    template_name = 'user/login_form.html'
    title = _('Login')
    success_url = '/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['login'] = True
        return context
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse('user_page', kwargs={'user': request.user.username}))
        return super().dispatch(request, *args, **kwargs)

class LogoutView(BaseLogoutView):
    template_name = 'user/logout.html'
    form_class = LoginForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super().dispatch(request, *args, **kwargs)

class PasswordChangeView(BasePasswordChangeView):
    template_name = 'user/change_password.html'
    success_message = _('You have changed your password successfully')

    def get_success_url(self) -> str:
        return reverse('user_page', kwargs={'user': self.request.user.username})