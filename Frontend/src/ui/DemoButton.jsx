import React, { useMemo, useState } from 'react';

export default function DemoButton({ onClick }) {
  return (
    <button
      onClick={onClick}
      className="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 active:bg-green-800 text-white font-medium transition"
    >
      Demo
    </button>
  );
}

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:3000/api/';

async function request(path, { method = 'GET', data, signal } = {}) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: data ? { 'Content-Type': 'application/json' } : undefined,
    body: data ? JSON.stringify(data) : undefined,
    signal,
  });

  const ct = res.headers.get('content-type') || '';
  const body = ct.includes('application/json') ? await res.json() : await res.text();
  if (!res.ok) throw new Error(body?.detail || res.statusText);
  return body;
}

async function sendDemoMail() {
  data = [
    // PHISHING
    {
      senderEmail: 'security@paypaI-security.com', // note: lookalike domain
      title: 'URGENT: Verify your account to avoid suspension',
      body:
        'Dear Customer,\n\n' +
        'We detected unusual activity on your account. For your protection, your access will be limited in 12 hours unless you verify your information.\n\n' +
        'Please confirm your identity at our secure portal:\n' +
        'https://paypaI-security.com/verify\n\n' +
        'You will be asked to confirm your full name, date of birth, and card details so we can restore your account.\n\n' +
        'Thank you,\nAccount Protection Team',
    },

    // NORMAL / LEGIT
    {
      senderEmail: 'notifications@github.com',
      title: 'Your pull request #42 was merged 🎉',
      body:
        'Hi Alex,\n\n' +
        'Good news! Your pull request #42 (feat: improve phishing highlights) was merged into main.\n\n' +
        '• Repository: agentic-phishnet\n' +
        '• Author: alex-siek\n' +
        '• Merge SHA: a1b2c3d\n\n' +
        'You can review the changes here: https://github.com/agentic-phishnet/compare\n\n' +
        'Thanks for contributing!',
    },

    // SUSPICIOUS
    {
      senderEmail: 'it-support@university-helpdesk.co',
      title: 'Action Required: Email quota exceeded — re-validate now',
      body:
        'Hello,\n\n' +
        'Your mailbox has reached the storage quota and may stop receiving messages. To keep your email active, re-validate immediately using the link below:\n\n' +
        'http://bit.ly/uni-mail-validate\n\n' +
        'If not validated within 24 hours, your account could be disabled. Do not reply to this message.\n\n' +
        'IT Support (Automated)',
    },
  ];

  // emailResult = await request('processEmail', { method:'GET', data:data })

  console.log(await request('processEmail', { method: 'GET', data: data }));
}
