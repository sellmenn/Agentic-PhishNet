import React from 'react';

export default function TooltipCard({ items = [], className = '' }) {
  return (
    <div className={"pointer-events-none absolute -top-2 left-0 -translate-y-full z-50 " + className}>
      <div className="opacity-0">\</div>
      <div className="rounded-xl border border-line bg-[rgba(6,18,30,.95)] shadow-glow p-3 min-w-[260px] max-w-[380px]">
        <div className="text-xs font-semibold text-ink mb-1">Signals</div>
        <ul className="space-y-1 text-xs text-ink leading-relaxed">
          {items.map((it, i) => (
            <li key={i} className="flex gap-2">
              <span
                className={
                  'mt-0.5 inline-flex h-4 w-4 items-center justify-center rounded-full ' +
                  (it.type === 'Factual'
                    ? 'bg-emerald-400/20 ring-1 ring-emerald-400/60'
                    : it.type === 'Language'
                    ? 'bg-yellow-300/20 ring-1 ring-yellow-400/60'
                    : 'bg-amber-400/20 ring-1 ring-amber-400/60')
                }
              >
                !
              </span>
              <span>
                <b>{it.type}:</b> {it.reason}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
