# PhishNetMail — React Web (Neon Theme, Resizable)

- Adjustable middle split: **drag the vertical neon bar** to give more or less space to the inbox list or reading pane.
- Hidden left rail (hover to reveal).
- Right inspector appears with translucent overlay when an email is open.
- A **mock phishing email** is opened by default so you can test highlights + inspector immediately.
- Still includes helpers to inject mail from the browser console.

## Run
```bash
npm install
npm run dev
# open http://localhost:3000
```

## Inject emails (browser console)
```js
PhishNetMail.mockLegit();
PhishNetMail.mockQuestionable();
PhishNetMail.mockPhish();   // re-opens the demo phishing email
PhishNetMail.send({ sender:'boss@corp.com', subject:'Status', body:'Send the report by EOD', type:'legit' });
```
