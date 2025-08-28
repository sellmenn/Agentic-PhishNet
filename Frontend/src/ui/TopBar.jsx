import React from 'react';
export default function TopBar({ onHamburgerHover }) {
  return (
    <header className="sticky top-0 z-20 bg-[rgba(6,18,30,.65)] backdrop-blur-xs border-b border-line shadow-insetSoft">
      <div className="flex items-center gap-3 px-4 py-3">
        <div
          className="group"
          onMouseEnter={onHamburgerHover}
        >
          <div className="w-9 h-9 rounded-xl glass flex flex-col items-center justify-center gap-0.5 cursor-pointer shadow-glow">
            <span className="w-5 h-0.5 bg-accent" />
            <span className="w-5 h-0.5 bg-accent" />
            <span className="w-5 h-0.5 bg-accent" />
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl glass border border-line flex items-center justify-center text-accent font-bold">
            Φ
          </div>
          <span className="font-semibold text-ink">PhishNetMail</span>
        </div>
        <div className="flex-1" />
        <div className="relative w-[38%]">
          <input
            className="w-full rounded-xl glass border border-line text-ink placeholder-dim outline-none px-4 py-2 text-sm shadow-insetSoft"
            placeholder="Search mail"
          />
          <div className="absolute right-3 top-2.5 text-dim">⌕</div>
        </div>
        <div className="flex items-center gap-2 ml-3">
          <button className="chip">Compose</button>
          <button className="chip">Filters</button>
          <div className="w-8 h-8 rounded-full glass border border-line" />
        </div>
      </div>
    </header>
  );
}
