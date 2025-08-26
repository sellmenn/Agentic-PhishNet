class Email:
    def __init__(self):
        self.sender : str = None
        self.subject : str = None
        self.cc : str = None
        self.bcc : str = None
        self.attachments : list[any] = None
        self.content : str

    def __repr__(self):
        email_object = {
            "sender" : self.sender,
            "subject" : self.subject,
            "cc" : self.cc,
            "bcc" : self.bcc,
            "attachments" : self.attachments,
            "content" : self.content
        }
        return email_object


