from Util.Email import Email
from Util.Evaluation import Evaluation
import json 

class Model:
    def __init__(self):
        self.temp : float = 0
        self.evals : list[Evaluation]
        self.name : str = None

    def get_type(self) -> str:
        raise NotImplementedError("To be implemented in subclass.")
        
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
        e = None # Model outputs evaluation as json -> e
        e_obj = Evaluation(
            confidence=e["confidence_score"],
            summary=e["summary"],
            token_usage=e["token_usage"],
            highlight=e["highlight"]
        )
        e_obj.set_ident(ident=email.get_ident())
        self.evals.append(e_obj)

    def get_e_obj(self, ident) -> Evaluation | None: 
        for e in self.evals:
            if e.get_ident() == ident:
                return e
        return None

    def get_confidence(self, ident): 
        return self.get_e_obj(ident).get_confidence()

    def get_summary(self, ident): 
        return self.get_e_obj(ident).get_summary()

    def get_token_usage(self, ident): 
        return self.get_e_obj(ident).get_token_usage()
    
    def get_highlight(self, ident): 
        return self.get_e_obj(ident).get_highlight()