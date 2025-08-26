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
        
    def is_legitimate(self, email : Email) -> bool:
        final_confidence_score = 0
        token_usage = 0
        summary = []
        highlights = []

        for (idx, agent) in enumerate(self.agents):
            agent.evaluate(email)
            final_confidence_score += agent.get_confidence() * weightage[idx]
            token_usage += agent.get_token_usage
            summary.append({agent.__class__(), agent.get_summary})
            highlights.append({agent.__class__(), agent.get_highlight()})

        if final_confidence_score <= self.bias:
            return True
        elif final_confidence_score >= self.cutoff:
            return (summary, highlights)
        return False