
from django.http import JsonResponse

def ping(request):
    """One tiny demo endpoint: GET /api/ping/ -> {status: ok}

    The middleware adds an 'X-Example' header to this response.
    """
    # Echo something the middleware attached (if present)
    note = request.META.get("X_REQUEST_NOTE", "")
    return JsonResponse({"status": "ok", "note": note})
