
from django.http import JsonResponse
from src.Util.Email import Email
import json
import uuid

def processEmail(request):
    
    ochestrator = request.phishnet.orchestrator

   

    ct = request.META.get("CONTENT_TYPE", "")
        
    if "application/json" in ct:
        try:
            raw = request.body  
            request.json = json.loads((raw or b"{}").decode(request.encoding or "utf-8"))
        except Exception:
            request.json = None
    elif request.method in ("POST", "PUT", "PATCH"):
        
        request.form = request.POST.dict()
    else:
        request.json = None
        request.form = {}

    emails = request.json['emails']
    print("incoming: ",emails)
    emailResults = []

    for e_json in emails:
        print(e_json)
        email = Email()
        email.ident = uuid.uuid4().hex
        email.content = e_json["body"]
        email.sender = e_json["sender"]
        email.subject = e_json["subject"]
        emailResults.append(ochestrator.evaluate_email(email))


    print("emailResults",emailResults)

    return JsonResponse({"success": True, "emailResults": emailResults}, status=200)