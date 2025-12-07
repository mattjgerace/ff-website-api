from ffwebsite.utils import wait_for_db

class WaitForDatabaseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        wait_for_db()
        return self.get_response(request)