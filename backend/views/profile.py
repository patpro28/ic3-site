from django.utils.functional import cached_property
from django.http import Http404
from django.views.generic.detail import DetailView
from django.contrib.auth.views import redirect_to_login
from django.utils.translation import gettext_lazy as _

from backend.models import Profile
from backend.utils.views import TitleMixin, generic_message

class UserMixin(object):
    model = Profile
    slug_field = 'username'
    slug_url_kwarg = 'user'
    context_object_name = 'user'


class UserPage(TitleMixin, UserMixin, DetailView):
    template_name = 'user/user-page.html'

    def get_object(self, queryset = None):
        if self.kwargs.get(self.slug_url_kwarg, None) is None:
            return self.request.user
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
        return (_('My account') if self.request.user == self.object else 
                _('User %s') % self.object.username)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context[""] = 
        return context
    

# class ProfileDetail(UserPage):
    