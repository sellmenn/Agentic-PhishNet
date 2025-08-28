import React, { useMemo } from 'react';
import { classifyReasoning } from './utils.js';
export default function HighlightedText({ text, detection }) {
  const segments = useMemo(() => {
    if (!detection || !Array.isArray(detection.highlight)) return [{ type: 'text', text }];
    const ranges = detection.highlight
      .map((h) => ({
        s: h.s_idx,
        e: h.e_idx,
        reason: h.reasoning,
        types: classifyReasoning(h.reasoning),
      }))
      .filter(
        (r) =>
          Number.isFinite(r.s) &&
          Number.isFinite(r.e) &&
          r.s >= 0 &&
          r.e <= text.length &&
          r.e > r.s,
      )
      .sort((a, b) => a.s - b.s || a.e - b.e);
    const out = [];
    let c = 0;
    for (const r of ranges) {
      if (r.s > c) out.push({ type: 'text', text: text.slice(c, r.s) });
      out.push({ type: 'hl', text: text.slice(r.s, r.e), reason: r.reason, types: r.types });
      c = r.e;
    }
    if (c < text.length) out.push({ type: 'text', text: text.slice(c) });
    return out;
  }, [text, detection]);
  return (
    <div className="leading-relaxed text-ink">
      {segments.map((seg, i) =>
        seg.type === 'hl' ? (
          <span
            key={i}
            className="tooltip bg-yellow-300/20 border border-yellow-400/30 px-1 rounded-sm cursor-help"
          >
            {seg.text}
            <div className="panel">
              {seg.types.map((t) => (
                <div
                  key={t}
                  className="mb-1"
                >
                  <span className="text-danger mr-1">!</span>
                  <span className="font-semibold">{t}</span>
                </div>
              ))}
              <div className="text-dim">{seg.reason}</div>
            </div>
          </span>
        ) : (
          <span key={i}>{seg.text}</span>
        ),
      )}
    </div>
  );
}
