from .Model import Model
from Util.Email import Email
from Util.Evaluation import Evaluation
from Util.handlers import *
from concurrent.futures import ThreadPoolExecutor

class Orchestrator:
    def __init__(self, weights: list[float], cutoff=0.4, bias=0.6, agents: tuple[Model] = ()):
        self.weights = weights
        self.cutoff = cutoff
        self.bias = bias
        self.agents: tuple[Model] = agents

        verify_weights(weights)
        if len(agents) != len(weights):
            raise Exception("Number of weights provided does not match number of agents!")

    def _evaluate_agent(self, agent_index, agent, email_ident, email):
        agent.evaluate(email)
        confidence = agent.get_confidence(email_ident)
        summary = agent.get_summary(email_ident)
        highlight = agent.get_highlight(email_ident)
        token_usage = agent.get_token_usage(email_ident)
        agent_type = agent.get_type()

        return {
            "index": agent_index,
            "confidence": confidence,
            "summary": summary,
            "highlight": highlight,
            "token_usage": token_usage,
            "agent_type": agent_type,
        }

    def evaluate_email(self, email: Email) -> dict:
        email_ident = email.get_ident()
        final_confidence_score = 0
        summary = ""
        highlight = []
        prompt_tokens = completion_tokens = total_tokens = 0
        agent_types = []
        agent_confidence = []

        def worker(idx_agent):
            idx, agent = idx_agent
            agent.evaluate(email)
            return {
                "index": idx,
                "confidence": agent.get_confidence(email_ident),
                "summary": agent.get_summary(email_ident),
                "highlight": agent.get_highlight(email_ident),
                "token_usage": agent.get_token_usage(email_ident),
                "agent_type": agent.get_type(),
            }

        with ThreadPoolExecutor(max_workers=len(self.agents)) as executor:
            results = list(executor.map(worker, enumerate(self.agents)))

        for result in results:
            idx = result["index"]
            final_confidence_score += result["confidence"] * self.weights[idx]
            summary += f"\n{result['agent_type']} : {result['summary']}\n"
            # highlight.extend(result["highlight"])
            highlight.extend([result["highlight"]])
            usage = result["token_usage"]
            prompt_tokens += usage["prompt_tokens"]
            completion_tokens += usage["completion_tokens"]
            total_tokens += usage["total_tokens"]
            agent_types.append(result["agent_type"])
            agent_confidence.append(result["confidence"])

        combined_usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        }

        eval_json = {
            "final_confidence": final_confidence_score,
            "agent_types": agent_types,
            "agent_confidence": agent_confidence,
            "summary": summary,
            "highlight": highlight,
            "token_usage": combined_usage
        }

        return eval_json
