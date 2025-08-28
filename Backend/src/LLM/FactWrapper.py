from src.Agents.Train.fact_verification_agent import FactVerificationAgent

from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o-mini"

class FactAnalysisWrapper:
    def __init__(self):
        self.client = FactVerificationAgent(model=MODEL)

    def analyse_email(self, email_content : str) -> dict:
        return self.client.analyze_email(email_content=email_content)
