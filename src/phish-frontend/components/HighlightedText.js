function Tooltip({ children, title, meta }) {
  return (
    <span className="relative group">
      {children}
      <div className="pointer-events-none absolute left-0 top-full mt-2 hidden w-72 rounded-lg bg-[#0c1424] border border-cyan-400/20 p-2 text-xs text-gray-200 group-hover:block z-10">
        <div className="font-semibold text-accent">{meta?.category || 'Reason'}</div>
        <div className="text-gray-300">{title}</div>
      </div>
    </span>
  );
}

export default function HighlightedText({ text, highlights = [] }) {
  const parts = text.split(/(\s+)/);
  return (
    <div className="leading-relaxed text-gray-200">
      {parts.map((chunk, i) => {
        if (/^\s+$/.test(chunk)) return <span key={i}>{chunk}</span>;
        const hl = highlights.find((h) => h.word === chunk);
        if (hl) {
          const tip = `${hl.reason}`;
          return (
            <Tooltip key={i} title={tip} meta={{category: hl.category}}>
              <span className="bg-yellow-300/20 border border-yellow-400/30 px-1 rounded-sm cursor-help">{chunk}</span>
            </Tooltip>
          );
        }
        return <span key={i}>{chunk}</span>;
      })}
    </div>
  );
}
