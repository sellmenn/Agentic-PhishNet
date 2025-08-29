import React from 'react';
const Chip = ({ children }) => <button className="chip">{children}</button>;
export default function EmailList({ emails, onSelect, style }) {
  return (
    <div
      className="bg-transparent border-r border-line"
      style={style}
    >
      <div className="px-3 py-2 flex items-center gap-2 border-b border-line">
        {['Primary', 'Social', 'Promotions', 'Updates'].map((t) => (
          <Chip key={t}>{t}</Chip>
        ))}
      </div>
      <div className="px-3 py-2 flex items-center gap-2 border-b border-line">
        {['Unread', 'Starred', 'Attachments', 'From bank', 'Has links'].map((f) => (
          <Chip key={f}>{f}</Chip>
        ))}
      </div>
      <div
        className="overflow-y-auto scrollbar"
        style={{ height: 'calc(100vh - 128px)' }}
      >
        {emails.length === 0 && (
          <div className="p-6 text-dim">
            No emails yet. Run the demo.
          </div>
        )}
        {emails.map((m, i) => (
          <div
            key={i}
            onClick={() => onSelect(m)}
            className="flex items-center gap-3 px-3 py-3 border-b border-line hoverable cursor-pointer"
          >
            <div className="w-8 h-8 rounded-full glass border border-line" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <p className="font-medium text-ink truncate">{m.sender}</p>
                {(m.type === 'questionable' || m.type === 'flagged') && (
                  <span className="badge">flagged</span>
                )}
                {m.type === 'phishing' && (
                  <span
                    className="badge"
                    style={{ color: '#fca5a5', borderColor: 'rgba(252,165,165,.3)' }}
                  >
                    phishing
                  </span>
                )}
              </div>
              <p className="text-sm text-dim truncate">{m.subject}</p>
            </div>
            <div className="text-xs text-dim">12:34</div>
            <div className="w-4 h-4 rounded-sm glass border border-line" />
          </div>
        ))}
      </div>
    </div>
  );
}
