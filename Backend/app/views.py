
from django.http import JsonResponse

def processEmail(request):
    # Echo something the middleware attached (if present)
    note = request.META.get("X_REQUEST_NOTE", "")
    return JsonResponse({"status": "ok", "note": note})
