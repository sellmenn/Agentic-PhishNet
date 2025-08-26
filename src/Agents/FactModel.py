from Model import Model

class FactModel(Model):
    def __init__(self):
        super().__init__()
        self.type = "Fact Checking Agent"

    def get_type(self):
        return self.type