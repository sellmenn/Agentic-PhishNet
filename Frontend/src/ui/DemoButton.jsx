import React, { useMemo, useState } from 'react'
import Orchestrator from '../../../Agents'

export default function DemoButton({  }) { }
function sendDemoMail() {
    
}

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:3000/api/sendDemoEmails';

async function request(path, { method = 'GET', data, signal } = {}) {
    data = [
        {
            senderEmail: "",
            title: "",
            body: "",
        }, {
            senderEmail: "",
            title: "",
            body: "",
        }, {
            senderEmail: "",
            title: "",
            body: "",
        },
    ]


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