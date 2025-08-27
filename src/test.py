from Agents.LangModel import LangModel
from Agents.Orchestrator import Orchestrator
from Util.Email import Email

def create_demo_email(file_name : str) -> Email:
    demo = Email()
    demo.ident = 1
    demo.attachments = ["abc", "def"]
    with open(file_name, "r") as f:
        demo.content = " ".join(f.readlines())
    return demo

def test_lang_model():
    print("\n\n*** Testing Language Analysis Model ***")
    agent = LangModel()
    email = create_demo_email("/Users/ariqkoh/Desktop/Agentic-PhishNet/Sample/positive/pearsonpdt.txt")
    email_id = email.get_ident()
    agent.evaluate(email)
    e = agent.get_e_obj(email_id)
    print(e)

def test_orchestrator():
    print("\n\n*** Testing Orchestrator ***")
    demo_email = create_demo_email("/Users/ariqkoh/Desktop/Agentic-PhishNet/Sample/positive/pearsonpdt.txt")
    weights = [1]
    lang_agent = LangModel()
    agents = []
    agents.append(lang_agent)

    o = Orchestrator(
        weights=weights,
        agents=agents
    )

    eval = o.evaluate_email(demo_email)
    print(eval)

def run_all_tests():
    test_lang_model()
    test_orchestrator()
    
if __name__ == "__main__":
    run_all_tests()