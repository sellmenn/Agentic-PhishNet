export default function Sidebar() {
  const Item = ({ label, active, danger }) => (
    <div className={`flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer hover:bg-white/5 ${active ? 'bg-white/10 text-accent' : 'text-gray-300'} ${danger ? 'text-red-300' : ''}`}>
      <div className="w-5 h-5 rounded-sm bg-[#111a2e] border border-cyan-400/20" />
      <span className="text-sm">{label}</span>
    </div>
  );
  return (
    <aside className="w-72 bg-panel border-r border-cyan-400/10 p-3 space-y-2">
      <Item label="Inbox" active />
      <Item label="Starred" />
      <Item label="Snoozed" />
      <Item label="Sent" />
      <Item label="Drafts" />
      <Item label="Spam / Junk" danger />
      <div className="mt-4 text-xs uppercase text-gray-400">Labels</div>
      <div className="grid grid-cols-2 gap-2">
        {["Finance","School","Hackathon","Vendors","Security","Family"].map(x=>(
          <div key={x} className="chip text-gray-300">{x}</div>
        ))}
      </div>
      <div className="mt-4 text-xs uppercase text-gray-400">Storage</div>
      <div className="w-full h-2 rounded bg-[#0c1424] overflow-hidden neon-border">
        <div className="h-full bg-gradient-to-r from-accent via-magenta to-lemon" style={{width:"38%"}} />
      </div>
      <div className="text-[11px] text-gray-400">2.6 GB of 7 GB used</div>
      <div className="mt-4 p-3 rounded-lg border border-cyan-400/10 bg-[#0c1424]">
        <div className="text-sm font-semibold text-emerald-300">Live Agent</div>
        <div className="text-xs text-gray-400">Monitoring inbox…</div>
        <div className="mt-2 flex gap-2">
          <span className="badge badge-green">Online</span>
          <span className="badge badge-yellow">3 queues</span>
        </div>
      </div>
    </aside>
  );
}
