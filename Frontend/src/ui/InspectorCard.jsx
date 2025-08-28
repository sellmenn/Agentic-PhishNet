// InspectorCard.jsx
import React, { useMemo, useState } from 'react';
import { statusFromConfidence } from './utils.js';

export default function InspectorCard({ detection }) {
  const [open, setOpen] = useState(false);
  const has = detection && detection.highlight && detection.highlight.length > 0;

  const scores = useMemo(() => {
    let language = 0, factual = 0;
    if (detection && Array.isArray(detection.agent_types)) {
      detection.agent_types.forEach((t, i) => {
        const v = Array.isArray(detection.agent_confidence) ? detection.agent_confidence[i] || 0 : 0;
        if (/language/i.test(t)) language = Math.round(v * 100);
        if (/fact/i.test(t)) factual = Math.round(v * 100);
      });
    }
    return { language, factual };
  }, [detection]);

  if (!has) return null;

  const finalPct = Math.round((detection?.final_confidence ?? 0) * 100);
  const status = statusFromConfidence(detection?.final_confidence ?? 0);

  return (
    <>
      <div className="fixed bottom-6 right-2 z-40 flex items-end gap-2 select-none">
        <button className="pull-tab" onMouseEnter={() => setOpen(true)} title="Analysis">
          Analysis
        </button>
      </div>

      <div className={`fixed bottom-4 right-4 z-40 inspector ${open ? 'open' : ''}`}
           onMouseLeave={() => setOpen(false)} aria-hidden={!open}>
        <div className="w-[22rem] pill rounded-2xl p-4 shadow-glow">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-ink">Analysis</div>
            <div className="text-xs text-dim">
              Confidence {finalPct}% · <span style={{ color: status.color }}>{status.label}</span>
            </div>
          </div>

          <div className="mt-3 space-y-3 text-sm text-ink">
            {Bar('Factual Information', scores.factual, 'bg-emerald-400')}
            {Bar('Language', scores.language, 'bg-yellow-400')}
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
        <div className={`h-full ${color}`} style={{ width: `${v}%` }} />
      </div>
    </div>
  );
}
