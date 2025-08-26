from Util.Email import Email

class Model:
    def __init__(self):
        self.temp : float = 0
        
    def evaluate(self, email : Email):
        raise NotImplementedError