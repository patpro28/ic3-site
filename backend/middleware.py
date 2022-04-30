import pytz
from django.conf import settings
from django.db import connection
from django.utils import timezone
from django.utils.timezone import make_aware

class EmathLoginMiddleware(object):
    def __init__(self, get_respone):
        self.get_response = get_respone
    
    def __call__(self, request):
        if request.user.is_authenticated:
            profile = request.profile = request.user
        else:
            profile = None


class ContestMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        profile = request.user
        if request.user.is_authenticated:
            profile.update_contest()
            request.participation = profile.current_contest
            request.in_contest = request.participation is not None
        else:
            request.in_contest = False
            request.participation = None
        return self.get_response(request)


class TimezoneMiddleware(object):
    def __init__(self, get_response=None):
        self.get_response = get_response

    def get_timezone(self, request):
        tzname = settings.DEFAULT_USER_TIME_ZONE
        if request.user.is_authenticated:
            tzname = request.user.timezone
        return pytz.timezone(tzname)

    def __call__(self, request):
        with timezone.override(self.get_timezone(request)):
            return self.get_response(request)


def from_database_time(datetime):
    tz = connection.timezone
    if tz is None:
        return datetime
    return make_aware(datetime, tz)
