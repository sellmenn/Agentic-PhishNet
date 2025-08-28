from src.Agents.Orchestrator import Orchestrator
from src.Agents.FactModel import FactModel
from src.Agents.LangModel import LangModel
import json

class PhishNetMiddleware:
    """Ultra-simple demo middleware.

    - Before view: attach a note to request.META

    - After view: add an HTTP header `X-Example: demo`

    """
    def __init__(self, get_response ):
        self.get_response = get_response
        agents = (FactModel(), LangModel())
        O = Orchestrator([.5,.5], agents = agents)
        self.O = O

    def __call__(self, request):
        ct = request.META.get("CONTENT_TYPE", "")
        
        if "application/json" in ct:
            try:
                raw = request.body  # bytes, cached by Django
                request.json = json.loads((raw or b"{}").decode(request.encoding or "utf-8"))
            except Exception:
                request.json = None
        elif request.method in ("POST", "PUT", "PATCH"):
            # For form/multipart requests let Django parse it
            request.form = request.POST.dict()
        else:
            request.json = None
            request.form = {}

        request.query = request.GET.dict()
        
        print("query", request.query)
        print("body", request.body)

        response = self.get_response(request)
        return response
