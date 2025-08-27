from Agents.LangModel import LangModel
from Util.Email import Email

def create_demo_email(file_name : str) -> Email:
    demo = Email()
    demo.ident = 1
    demo.attachments = ["abc", "def"]
    with open(file_name, "r") as f:
        demo.content = " ".join(f.readlines())
    return demo

def test_lang_model():
    agent = LangModel()
    email = create_demo_email("/Users/ariqkoh/Desktop/Agentic-PhishNet/Sample/positive/pearsonpdt.txt")
    email_id = email.get_ident()
    agent.evaluate(email)
    e = agent.get_e_obj(email_id)
    print(e)
    
if __name__ == "__main__":
    test_lang_model()