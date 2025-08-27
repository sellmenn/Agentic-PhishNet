from Model import Model

class LangModel(Model):
    def __init__(self):
        super().__init__()
        self.type = "Language Analysis Agent"

    def get_type(self):
        return self.name