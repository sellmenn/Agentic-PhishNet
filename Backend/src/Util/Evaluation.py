class Evaluation:
    def __init__(
            self, 
            confidence : float,
            summary : str,
            token_usage : dict,
            highlight : list
        ):

        self.ident = None
        self.evaluator_type : str = None
        self.confidence = confidence
        self.summary = summary
        self.token_usage = token_usage
        self.highlight = highlight

    def __repr__(self):
        str_rep = (
            "----------Evaluation Object----------\n"
            f"* ident -> {self.ident if self.ident else "None"}\n"
            f"* evaluator -> {self.evaluator_type}\n"
            f"* confidence -> {self.confidence}\n"
            f"* summary -> {self.summary}\n"
            f"* highlight -> {self.highlight}\n"
            f"* token usage -> {self.token_usage}\n\n"
        )
        return str_rep

    def set_ident(self, ident: str) -> None:
        self.ident = ident

    def get_ident(self) -> str | None:
        return self.ident

    def set_evaluator(self, evaluator):
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