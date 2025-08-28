// EmailViewer.jsx
import React from 'react';
import HighlightedText from './HighlightedText.jsx';
import { statusFromConfidence } from './utils.js';

export default function EmailViewer({ email, style }) {
  if (!email) {
    return (
      <div className="flex-1 flex items-center justify-center text-dim" style={style}>
        Select an email
      </div>
    );
  }

  const fc = email?.detection?.final_confidence ?? null;
  const status = fc != null ? statusFromConfidence(fc) : null;

  return (
    <div className="p-6 overflow-y-auto" style={style}>
      <div className="pill rounded-2xl p-5 mb-4">
        <h1 className="font-semibold text-lg text-ink">{email.subject}</h1>
        <p className="text-sm text-dim mb-2">{email.sender}</p>
        <div className="flex gap-2 flex-wrap">
          <span className="badge">Verified DKIM</span>
          <span className="badge">External</span>
          {status && (
            <span className="badge" style={{ color: status.color, borderColor: `${status.color}55` }}>
              {status.label}
            </span>
          )}
        </div>
      </div>

      <div className="pill rounded-2xl p-5">
        <HighlightedText text={email.body} detection={email.detection} />
      </div>
    </div>
  );
}
