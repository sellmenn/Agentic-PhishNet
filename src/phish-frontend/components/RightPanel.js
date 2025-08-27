export default function RightPanel({ email }) {
  return (
    <aside className="w-80 bg-panel border-l border-cyan-400/10 p-4 space-y-4">
      <div className="text-sm font-semibold text-gray-200">Inspector</div>
      <div className="rounded-lg p-3 bg-[#0c1424] border border-cyan-400/10 space-y-2">
        <div className="text-xs text-gray-400">Verdict</div>
        {email?.type === "phishing" ? (
          <div className="badge badge-red">Phishing</div>
        ) : email?.type === "questionable" ? (
          <div className="badge badge-yellow">Questionable</div>
        ) : email ? (
          <div className="badge badge-green">Legitimate</div>
        ) : <div className="text-xs text-gray-500">No email selected</div>}
      </div>
      <div className="rounded-lg p-3 bg-[#0c1424] border border-cyan-400/10">
        <div className="text-xs text-gray-400 mb-2">Signals</div>
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-gray-300"><span>Domain Reputation</span><span>72</span></div>
          <div className="w-full h-1.5 rounded bg-[#0b1423]"><div className="h-full bg-emerald-400" style={{width:"72%"}}/></div>
          <div className="flex items-center justify-between text-xs text-gray-300"><span>Urgency Language</span><span>54</span></div>
          <div className="w-full h-1.5 rounded bg-[#0b1423]"><div className="h-full bg-yellow-400" style={{width:"54%"}}/></div>
          <div className="flex items-center justify-between text-xs text-gray-300"><span>Link Mismatch</span><span>15</span></div>
          <div className="w-full h-1.5 rounded bg-[#0b1423]"><div className="h-full bg-red-400" style={{width:"15%"}}/></div>
        </div>
      </div>
      <div className="rounded-lg p-3 bg-[#0c1424] border border-cyan-400/10">
        <div className="text-xs text-gray-400 mb-2">Quick Actions</div>
        <div className="flex flex-wrap gap-2">
          {["Quarantine","Allowlist","Report","Mute Thread"].map(x=>(
            <button key={x} className="chip">{x}</button>
          ))}
        </div>
      </div>
      <div className="rounded-lg p-3 bg-[#0c1424] border border-cyan-400/10">
        <div className="text-xs text-gray-400 mb-2">Upcoming</div>
        <div className="text-xs text-gray-500">No calendar items linked.</div>
      </div>
    </aside>
  );
}
