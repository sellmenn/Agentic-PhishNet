from Agents.Model import Model
from Util.Email import Email

weightage = [0.5, 0.5]
bias = 0.6

class Ochestrator:
    def __init__(self, weightage = [0.5, 0.5], cutoff = 0.4, bias = 0.6, agents : list[Model] = []):
        self.weightage = weightage
        self.cutoff = cutoff
        self.bias = bias
        self.agents : list[Model] = agents
        
    def evaluate_confidence(self, email : Email) -> dict:
        """
        Returns the following
        {
            "confidence" : final_confidence_score,
            "summary" : summary,
            "highlights" : highlights
        }
        """
        final_confidence_score = 0
        summary = []
        highlights = []
        email_ident = email.get_ident()

        for (idx, agent) in enumerate(self.agents):
            agent.evaluate(email)
            final_confidence_score += agent.get_confidence(email_ident) * weightage[idx]
            summary.append({agent.__class__(), agent.get_summary(email_ident)})
            highlights.append({agent.__class__(), agent.get_highlight(email_ident)})

        context = {
            "confidence" : final_confidence_score,
            "summary" : summary,
            "highlights" : highlights
        }

        return context