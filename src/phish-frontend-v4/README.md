# Phish-Frontend v4 — Cyberpunk UI
Dark, neon, Gmail-like layout with extra skeleton widgets. Pure frontend (Next.js + Tailwind).

## Run
```bash
npm install
npm run dev
# open http://localhost:3000
```

PowerShell policy error? Run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Simulate mail in console
```js
import { mockLegit, mockQuestionable, mockPhish, mockSendEmail } from "@/utils/mockEvents";
mockLegit();         // legit → Inbox
mockQuestionable();  // questionable → Inbox
mockPhish();         // phishing → Spam with highlights
```

## Notes
- Left sidebar shows folders, labels, storage (skeleton).
- Top bar has search, compose, filters (non-functional placeholders).
- Right panel contains Inspector, Signals bars, and Quick Actions (non-functional).
- Email list includes tabs, quick filters, and animated skeleton rows.
- Phishing emails render with inline hover tooltips sourced from `highlights` JSON.
