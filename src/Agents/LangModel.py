from Model import Model

class LangModel(Model):
    def __init__(self):
        super().__init__()
        self.name = "Language Analysis Agent"

    def get_type(self):
        return self.type