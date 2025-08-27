from Util.Email import Email
from Util.Evaluation import Evaluation
import json 

class Model:
    def __init__(self):
        self.temp : float = 0
        self.evals : list[Evaluation] = []
        self.type : str = None

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
        raise NotImplementedError("To be implemented in subclass.")
    
    def get_e_obj(self, ident):
        for e in self.evals:
            if e.get_ident() == ident:
                return e
        return None

    def get_evaluation(self, ident):
        return self.get_e_obj(ident)

    def get_confidence(self, ident): 
        return self.get_e_obj(ident).get_confidence()

    def get_summary(self, ident): 
        return self.get_e_obj(ident).get_summary()

    def get_token_usage(self, ident): 
        return self.get_e_obj(ident).get_token_usage()
    
    def get_highlight(self, ident): 
        return self.get_e_obj(ident).get_highlight()