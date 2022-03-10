

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