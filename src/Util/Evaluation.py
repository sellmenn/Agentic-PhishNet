from Agents.Model import Model

class Evaluation:
    def __init__(
            self, 
            confidence : float,
            summary : str,
            token_usage : dict,
            highlight : list
        ):

        self.ident = None
        self.evaluator : Model = None
        self.confidence = confidence
        self.summary = summary
        self.token_usage = token_usage
        self.highlight = highlight

    def set_ident(self, ident: str) -> None:
        self.ident = ident

    def get_ident(self) -> str | None:
        return self.ident

    def set_evaluator(self, evaluator : Model):
        self.evaluator = evaluator

    def get_confidence(self) -> float:
        return self.confidence
    
    def get_summary(self) -> str:
        return self.summary
    
    def get_token_usage(self) -> dict:
        """
        Returns a dict of form: 
        {
            "prompt_tokens" : int,
            "completion_tokens" : int,
            "total_tokens" : int
        }
        """
        return self.token_usage
    
    def get_highlight(self) -> list:
        """
        Returns a list of the form:
        [
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
        """
        return self.highlight