from .Model import Model
from src.LLM.LangWrapper import LanAnalysisWrapper
from src.Util.Email import Email
from src.Util.Evaluation import Evaluation

class LangModel(Model):
    def __init__(self):
        super().__init__()
        self.type = "Language Analysis Agent"
        self.llm_wrapper = LanAnalysisWrapper()

    def get_type(self):
        return self.type
    
    def evaluate(self, email : Email) -> None:
        """
        {
            "confidence_score": 1,
            "summary": "",
            "token_usage": 10,
            "highlight": [
                {
                    "s_idx": 6,
                    "e_idx": 18,
                    "reasoning": "MEOWMEOW"
                },{
                    "s_idx": 6,
                    "e_idx": 18,
                    "reasoning": "MEOWMEOW"
                }
            ]
        }
        """
        e = self.llm_wrapper.analyse_email(email.content)
        e_obj = Evaluation(
            confidence=e["confidence_score"],
            summary=e["summary"],
            token_usage=e["token_usage"],
            highlight=e["highlight"]
        )
        e_obj.set_ident(ident=email.get_ident())
        e_obj.set_evaluator(self.get_type())
        self.evals.append(e_obj)