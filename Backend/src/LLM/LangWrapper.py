from Agents.Train.language_analysis_agent import LanguageAnalysisAgent

from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o-mini"

class LanAnalysisWrapper:
    def __init__(self):
        self.client = LanguageAnalysisAgent(model=MODEL)

    def analyse_email(self, email_content : str) -> dict:
        return self.client.analyze_email(email_content=email_content)
