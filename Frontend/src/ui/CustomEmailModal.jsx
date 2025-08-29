// CustomEmailModal.jsx
import React, { useEffect, useRef, useState } from 'react';

const isValidEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/i.test(String(v || '').trim());

export default function CustomEmailModal({ open, onClose, onSubmit }) {
  const [sender, setSender] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [touched, setTouched] = useState(false);
  const boxRef = useRef(null);

  useEffect(() => {
    if (open) {
      setSender('');
      setSubject('');
      setBody('');
      setTouched(false);
    }
  }, [open]);

  if (!open) return null;

  const emailOk = isValidEmail(sender);
  const canSubmit = emailOk && subject.trim() && body.trim();

  const handleSubmit = (e) => {
    e.preventDefault();
    setTouched(true);
    if (!canSubmit) return;
    onSubmit?.({
      sender: sender.trim(),
      subject: subject.trim(),
      body,
    });
    onClose?.();
  };

  return (
    <div
      className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center"
      aria-modal="true"
      role="dialog"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose?.();
      }}
    >
      {/* backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* panel */}
      <form
        ref={boxRef}
        onSubmit={handleSubmit}
        className="relative w-full sm:max-w-xl bg-[rgba(10,18,28,.96)] border border-line rounded-2xl p-5 shadow-glow m-3
                   animate-[modalIn_.18s_ease-out] will-change-transform"
        style={{
          animationName:
            '@keyframes modalIn{from{opacity:.001;transform:translateY(10px) scale(.98)}to{opacity:1;transform:translateY(0) scale(1)}}',
        }}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-ink font-semibold text-lg">Compose</h2>
          <button
            type="button"
            onClick={onClose}
            className="px-2.5 py-1 rounded-md hoverable text-dim"
            aria-label="Close compose dialog"
          >
            ✕
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="text-xs text-dim block mb-1">From (email)</label>
            <input
              type="email"
              value={sender}
              onChange={(e) => setSender(e.target.value)}
              onBlur={() => setTouched(true)}
              placeholder="you@domain.com"
              className="w-full rounded-md bg-transparent border border-line focus:border-cyan-400/60 outline-none px-3 py-2 text-ink"
              required
            />
            {touched && !emailOk && (
              <div className="text-xs text-red-300 mt-1">Please enter a valid email.</div>
            )}
          </div>

          <div>
            <label className="text-xs text-dim block mb-1">Subject</label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Subject…"
              className="w-full rounded-md bg-transparent border border-line focus:border-cyan-400/60 outline-none px-3 py-2 text-ink"
              required
            />
          </div>

          <div>
            <label className="text-xs text-dim block mb-1">Body</label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Write your message…"
              rows={10}
              className="w-full rounded-md bg-transparent border border-line focus:border-cyan-400/60 outline-none px-3 py-2 text-ink leading-relaxed"
              required
            />
          </div>
        </div>

        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            className="px-4 py-2 rounded-md hoverable text-dim"
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={!canSubmit}
            className={`px-4 py-2 rounded-md text-white font-medium ${
              canSubmit
                ? 'bg-cyan-600 hover:bg-cyan-700 active:bg-cyan-800'
                : 'bg-cyan-900/60 cursor-not-allowed'
            }`}
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}