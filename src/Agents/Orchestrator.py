from Agents.Model import Model
from Util.Email import Email
from Util.Evaluation import Evaluation
from Util.handlers import *

# Weightage given to each agent's evaluation

cutoff = 0.8
bias = 0.6

class Orchestrator:
    def __init__(self, weights : list[float], cutoff = 0.4, bias = 0.6, agents : tuple[Model] = ()):
        self.weights = weights
        self.cutoff = cutoff
        self.bias = bias
        self.agents : tuple[Model] = agents

        # Verification
        verify_weights(weights)
        if len(agents) != len(weights):
            raise Exception("Number of weights provided does not match number of agents!")

        
    def evaluate_email(self, email : Email) -> str:
        final_confidence_score = 0
        summary = ""
        highlight = []
        email_ident = email.get_ident()
        prompt_tokens, completion_tokens, total_tokens = 0, 0, 0
        agent_types = []
        agent_confidence = []

        for (idx, agent) in enumerate(self.agents):
            agent.evaluate(email)
            print(agent.get_confidence(email_ident))
            final_confidence_score += agent.get_confidence(email_ident) * self.weights[idx]
            summary += f"\n{agent.get_type()} : {agent.get_summary(email_ident)}\n"
            for h in agent.get_highlight(email_ident):
                highlight.append(h)
            agent_usage = agent.get_token_usage(email_ident)
            prompt_tokens += agent_usage["prompt_tokens"]
            completion_tokens += agent_usage["completion_tokens"]
            total_tokens += agent_usage["total_tokens"]
            agent_types.append(agent.get_type())
            agent_confidence.append(agent.get_confidence(email_ident))

        combined_usage = {
            "prompt_tokens" : prompt_tokens,
            "completion_tokens" : completion_tokens,
            "total_tokens" : total_tokens
        }

        eval_json = {
            "final_confidence" : final_confidence_score,
            "agent_types" : agent_types,
            "agent_confidence" :agent_confidence,
            "summary" : summary,
            "highlight" : highlight,
            "token_usage" : combined_usage
        }

        return eval_json
    