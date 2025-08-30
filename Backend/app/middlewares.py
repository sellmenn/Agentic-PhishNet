from src.Agents.Orchestrator import Orchestrator
from src.Agents.FactModel import FactModel
from src.Agents.LangModel import LangModel
from types import SimpleNamespace

class PhishNetMiddleware:
    """Ultra-simple demo middleware.

    - Before view: attach a note to request.META

    - After view: add an HTTP header `X-Example: demo`

    """
    def __init__(self, get_response ):
        self.get_response = get_response
        agents = [FactModel(), LangModel()] # 2 more agents are added by default, SenderModel and SubjectModel
        O = Orchestrator([.25,.25, .25, .25], agents = agents)
        self.O = O

    def __call__(self, request):
        request.phishnet = SimpleNamespace(
            orchestrator=self.O,
        )
        return self.get_response(request)
