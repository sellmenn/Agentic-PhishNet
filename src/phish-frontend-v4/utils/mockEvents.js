export function subscribeToNewEmails(callback) {
  const handler = (e) => callback(e.detail);
  window.addEventListener("newEmail", handler);
  return () => window.removeEventListener("newEmail", handler);
}

export function mockSendEmail(email) {
  window.dispatchEvent(new CustomEvent("newEmail", { detail: email }));
}

export function mockLegit() {
  mockSendEmail({ sender: "friend@mail.com", subject: "Lunch?", body: "Wanna grab lunch tomorrow?", type: "legit" });
}
export function mockQuestionable() {
  mockSendEmail({ sender: "promo@odd.biz", subject: "You won", body: "Claim prize now", type: "questionable" });
}
export function mockPhish() {
  window.dispatchEvent(new CustomEvent("spamEmail", { detail: {
    sender:"scam@fakebank.com",
    subject:"Urgent: Verify Your Account",
    body:"Dear user please login immediately to avoid suspension",
    type:"phishing",
    highlights:[
      { word:"login", category:"Factual", reason:"Banks don't ask to log in via email links" },
      { word:"immediately", category:"Language", reason:"Urgency is a phishing tactic" }
    ]
  }}));
}
