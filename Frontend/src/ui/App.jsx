// App.jsx
import React, { useEffect, useMemo, useState } from 'react';
import TopBar from './TopBar.jsx';
import HoverSidebar from './HoverSidebar.jsx';
import EmailList from './EmailList.jsx';
import EmailViewer from './EmailViewer.jsx';
import BgCircuits from './BgCircuits.jsx';
import InspectorCard from './InspectorCard.jsx';
import DemoButton from './DemoButton.jsx';
import { statusFromConfidence } from './utils.js';
import LoadingModal from './LoadingModal.jsx';

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/';

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

export default function App() {
    // three demo inputs (what you POST)
    const [requestEmails] = useState([
        // PHISHING — urgency + typosquatted domain + request for credentials
        {
            sender: 'alerts@m1crosoft-secure.com',
            subject: 'Password Reset Required — mailbox will be locked in 90 minutes',
            body:
                'Dear user,\n\n' +
                'Unusual sign-in activity was detected on your Microsoft 365 account. To keep your mailbox active, you must reset your password within 90 minutes.\n\n' +
                'Reset now using our secure page:\n' +
                'https://m1crosoft-secure.com/reset?id=87321\n\n' +
                'You will be asked to confirm your current password and MFA code to verify ownership.\n\n' +
                'Thank you,\nSecurity Operations'
        },

        // LEGIT — specific context, no urgency, no request for sensitive info, official domain
        {
            sender: 'no-reply@zoom.us',
            subject: 'Zoom meeting scheduled: Product Sync — Wed 3:00 PM',
            body:
                'Hi Alex,\n\n' +
                'Your meeting has been scheduled.\n\n' +
                'Topic: Product Sync\n' +
                'Time: Wed, 3:00 PM – 3:45 PM (SGT)\n' +
                'Join: https://zoom.us/j/123456789?pwd=Pd8K3a\n' +
                'Meeting ID: 123 456 789\n' +
                'Passcode: 437219\n\n' +
                'This is an automated notification from Zoom. We will never ask for your password or payment details by email.\n\n' +
                'Best,\nZoom Notifications'
        },

        // SUSPICIOUS — vague sender, shortened URL, small fee + urgency/threat language
        {
            sender: 'support@dhl-parcels.co',
            subject: 'Delivery attempt failed — pay S$1.20 customs fee',
            body:
                'Hello,\n\n' +
                'We tried to deliver your package but a small customs fee is pending. Your parcel will be returned today unless payment is received immediately.\n\n' +
                'Pay now to release parcel:\n' +
                'http://bit.ly/dhl-fee-120\n\n' +
                'Do not reply to this automated message.\n\n' +
                'DHL Support'
        }
    ]);

    // inbox now starts EMPTY per your request
    const [emails, setEmails] = useState([]);
    const [selected, setSelected] = useState(null);
    const [split, setSplit] = useState(42);
    const [dragging, setDragging] = useState(false);
    const [sidebarPulse, setSidebarPulse] = useState(0);
    const [loading, setLoading] = useState(false);

    // splitter drag
    const startDrag = () => {
        setDragging(true);
        document.body.classList.add('no-select');
        document.body.style.cursor = 'col-resize';
    };
    useEffect(() => {
        if (!dragging) return;
        const onMove = (e) => {
            const w = window.innerWidth;
            const x = e.touches ? e.touches[0].clientX : e.clientX;
            let p = Math.round((x / w) * 100);
            if (p < 20) p = 20;
            if (p > 75) p = 75;
            setSplit(p);
        };
        const onUp = () => {
            setDragging(false);
            document.body.classList.remove('no-select');
            document.body.style.cursor = 'auto';
        };
        window.addEventListener('mousemove', onMove);
        window.addEventListener('mouseup', onUp);
        window.addEventListener('touchmove', onMove, { passive: false });
        window.addEventListener('touchend', onUp);
        return () => {
            window.removeEventListener('mousemove', onMove);
            window.removeEventListener('mouseup', onUp);
            window.removeEventListener('touchmove', onMove);
            window.removeEventListener('touchend', onUp);
        };
    }, [dragging]);
    const [demoDone, setDemoDone] = useState(false);

    // DEMO: send request and map results to inbox
    const runDemo = async () => {
        if (loading || demoDone) return; // avoid re-entry
        try {
            setLoading(true);
            const payload = { emails: requestEmails }; // or just requestEmails if that’s what your API expects
            const res = await request('processEmail', { method: 'POST', data: payload });
            const results = res?.emailResults || [];

            const next = requestEmails.map((src, i) => {
                const det = results[i] || null;
                const fc = det?.final_confidence ?? 0;
                const status = statusFromConfidence(fc); // ← 0.4 / 0.6 thresholds
                return {
                    sender: src.sender,
                    subject: src.subject,
                    body: src.body,
                    detection: det,
                    type: status.key, // 'phishing' | 'flagged' | 'cleared'
                };
            });

            setEmails(next);
            setSelected(next[0] || null);
            setDemoDone(true); // ← disable button after a successful load
        } catch (e) {
            console.error(e);
            alert(e.message || 'Demo failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="h-full flex flex-col relative">
            <BgCircuits />
            <TopBar onHamburgerHover={() => setSidebarPulse((x) => x + 1)} />
            <HoverSidebar pulse={sidebarPulse} />

            {/* Loading overlay */}
            {loading && (
                <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs">
                    <div className="pill rounded-2xl px-5 py-3 text-ink bg-[rgba(12,20,32,.9)] border border-line shadow-glow">
                        Processing demo emails…
                    </div>
                </div>
            )}
            <LoadingModal show={loading} title="Processing demo emails…" />

            <div className="flex w-full" style={{ height: 'calc(100vh - 64px)' }}>
                <DemoButton onClick={runDemo} loading={loading} disabled={demoDone} />

                <EmailList emails={emails} onSelect={setSelected} style={{ width: split + '%' }} />
                <div className="splitter" onMouseDown={startDrag} onTouchStart={startDrag} />
                <EmailViewer email={selected} style={{ width: 100 - split + '%' }} />
            </div>

            <InspectorCard detection={selected?.detection} />
        </div>
    );
}
