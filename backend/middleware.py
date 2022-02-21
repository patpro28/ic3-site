

class EmathLoginMiddleware(object):
    def __init__(self, get_respone):
        self.get_response = get_respone
    
    def __call__(self, request):
        if request.user.is_authenticated:
            profile = request.profile = request.user
        else:
            profile = None