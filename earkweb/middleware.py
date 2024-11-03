from django.http import JsonResponse

class JsonApi404Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 404:
            if request.path.startswith('/earkweb/api/'):  
                response_data = {
                    "error": "Not Found",
                    "status_code": 404
                }
                return JsonResponse(response_data, status=404)
        return response
