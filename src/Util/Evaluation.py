class Evaluation:
    def __init__(
            self, 
            confidence : float,
            summary : str,
            token_usage : dict,
            highlights : list
        ):

        self.ident = None
        self.confidence = confidence
        self.summary = summary
        self.token_usage = token_usage
        self.highlight = highlights

    def set_ident(self, ident: str):
        self.ident = ident