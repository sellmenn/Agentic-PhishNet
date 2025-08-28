import React from 'react';
import HighlightedText from './HighlightedText.jsx';
export default function EmailViewer({ email, style }) {
  if (!email) {
    return (
      <div
        className="flex-1 flex items-center justify-center text-dim"
        style={style}
      >
        Select an email
      </div>
    );
  }
  return (
    <div
      className="p-6 overflow-y-auto"
      style={style}
    >
      <div className="pill rounded-2xl p-5 mb-4">
        <h1 className="font-semibold text-lg text-ink">{email.subject}</h1>
        <p className="text-sm text-dim mb-2">{email.sender}</p>
        <div className="flex gap-2 flex-wrap">
          <span className="badge">Verified DKIM</span>
          <span className="badge">External</span>
          {email.detection && email.detection.final_confidence >= 0.5 && (
            <span
              className="badge"
              style={{ color: '#fca5a5', borderColor: 'rgba(252,165,165,.35)' }}
            >
              Agent flagged
            </span>
          )}
        </div>
      </div>
      <div className="pill rounded-2xl p-5">
        <HighlightedText
          text={email.body}
          detection={email.detection}
        />
      </div>
    </div>
  );
}
