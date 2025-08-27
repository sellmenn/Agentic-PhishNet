export default function TopBar() {
  return (
    <header className="sticky top-0 z-10 bg-panel/90 backdrop-blur border-b border-cyan-400/10">
      <div className="gradient-bar" />
      <div className="flex items-center gap-3 px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-md bg-cyan-500/20 border border-cyan-400/30 flex items-center justify-center text-accent font-bold">Φ</div>
          <span className="text-accent font-semibold drop-shadow-glow">Agentic‑PhishNet</span>
        </div>
        <div className="flex-1" />
        <div className="relative w-[40%]">
          <input
            className="w-full rounded-lg bg-[#0c1424] border border-cyan-400/20 focus:border-accent/60 outline-none px-4 py-2 text-sm placeholder-gray-400"
            placeholder="Search mail"
          />
          <div className="absolute right-2 top-2 text-accent/60">⌕</div>
        </div>
        <div className="flex items-center gap-2 ml-4">
          <button className="chip">Compose</button>
          <button className="chip">Filters</button>
          <div className="w-8 h-8 rounded-full bg-[#111a2e] border border-cyan-400/20" />
        </div>
      </div>
    </header>
  );
}
