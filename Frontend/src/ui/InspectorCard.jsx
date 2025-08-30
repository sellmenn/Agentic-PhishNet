// InspectorCard.jsx
import React, { useMemo, useState } from 'react';
import { statusFromConfidence } from './utils.js';

export default function InspectorCard({ detection }) {
  const [open, setOpen] = useState(false);

  // Show the card when there is a detection with any highlights
  const has = !!(detection && Array.isArray(detection.highlight) && detection.highlight.length);

  // Collect confidence per agent type (0..100)
  const scores = useMemo(() => {
    const out = { factual: 0, language: 0, sender: 0, subject: 0 };
    if (!detection || !Array.isArray(detection.agent_types)) return out;

    const { agent_types = [], agent_confidence = [] } = detection;
    agent_types.forEach((t, i) => {
      const pct = Math.round(((agent_confidence[i] ?? 0) * 100));
      if (/fact/i.test(t)) out.factual = pct;
      else if (/language/i.test(t)) out.language = pct;
      else if (/sender/i.test(t)) out.sender = pct;     // NEW
      else if (/subject/i.test(t)) out.subject = pct;   // NEW
    });
    return out;
  }, [detection]);

  if (!has) return null;

  const finalPct = Math.round((detection?.final_confidence ?? 0) * 100);
  const status = statusFromConfidence(detection?.final_confidence ?? 0);

  return (
    <>
      {/* Pull tab */}
      <div className="fixed bottom-6 right-2 z-40 flex items-end gap-2 select-none">
        <button className="pull-tab" onMouseEnter={() => setOpen(true)} title="Analysis">
          Analysis
        </button>
      </div>

      {/* Inspector card */}
      <div
        className={`fixed bottom-4 right-4 z-40 inspector ${open ? 'open' : ''}`}
        onMouseLeave={() => setOpen(false)}
        aria-hidden={!open}
      >
        <div className="w-[22rem] pill rounded-2xl p-4 shadow-glow">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-ink">Analysis</div>
            <div className="text-xs text-dim">
              Confidence {finalPct}% · <span style={{ color: status.color }}>{status.label}</span>
            </div>
          </div>

          <div className="mt-3 space-y-3 text-sm text-ink">
            {Bar('Factual Information Analysis', scores.factual, 'bg-emerald-400')}
            {Bar('Language Analysis',            scores.language, 'bg-yellow-400')}
            {Bar('Sender Analysis',              scores.sender, 'bg-cyan-400')}
            {Bar('Subject Analysis',             scores.subject, 'bg-violet-400')}
          </div>

          {detection?.summary && (
            <div className="mt-3 text-xs text-dim whitespace-pre-line">
              {detection.summary.trim()}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function Bar(label, v, color) {
  return (
    <div>
      <div className="flex items-center justify-between text-xs text-dim">
        <span>{label}</span>
        <span>{v}%</span>
      </div>
      <div className="w-full h-1.5 rounded bg-[#0b1423]">
        <div className={`h-full rounded ${color}`} style={{ width: `${v}%` }} />
      </div>
    </div>
  );
}
