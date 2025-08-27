export default function EmailList({ emails, onSelect }) {
  const Row = ({ mail }) => (
    <div
      className="p-3 border-b border-cyan-400/10 hover:bg-white/5 cursor-pointer flex items-center gap-3"
      onClick={() => onSelect(mail)}
    >
      <div className="w-8 h-8 rounded-full bg-[#111a2e] border border-cyan-400/20" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="font-semibold text-gray-200 truncate">{mail.sender}</p>
          {mail.type === "questionable" && <span className="badge badge-yellow">questionable</span>}
          {mail.type === "phishing" && <span className="badge badge-red">phishing</span>}
        </div>
        <p className="text-sm text-gray-400 truncate">{mail.subject}</p>
      </div>
      <div className="text-xs text-gray-500">12:34</div>
      <div className="w-4 h-4 rounded-sm border border-cyan-400/20" />
    </div>
  );

  return (
    <div className="flex-1 border-r border-cyan-400/10 bg-panel">
      <div className="px-3 py-2 flex items-center gap-2 border-b border-cyan-400/10">
        {["Primary","Social","Promotions","Updates"].map(tab => (
          <button key={tab} className="chip">{tab}</button>
        ))}
        <div className="flex-1" />
        <div className="text-xs text-gray-400">1–50 of 7,016</div>
      </div>
      <div className="px-3 py-2 flex items-center gap-2 border-b border-cyan-400/10">
        {["Unread","Starred","Attachments","From bank","Has links"].map(f => (
          <button key={f} className="chip">{f}</button>
        ))}
      </div>
      <div className="overflow-y-auto" style={{height: "calc(100vh - 160px)"}}>
        {emails.length === 0 && (
          <div className="p-6 text-gray-500">No emails yet. Open console and use mock helpers to inject.</div>
        )}
        {emails.map((m,i)=>(<Row key={i} mail={m} />))}
        {/* skeleton placeholders */}
        {Array.from({length:8}).map((_,i)=> (
          <div key={`s${i}`} className="p-3 border-b border-cyan-400/10 flex items-center gap-3 animate-pulse">
            <div className="w-8 h-8 rounded-full bg-[#0e1628]" />
            <div className="flex-1 min-w-0">
              <div className="h-3 w-40 bg-[#0e1628] rounded mb-2" />
              <div className="h-3 w-60 bg-[#0e1628] rounded" />
            </div>
            <div className="h-3 w-10 bg-[#0e1628] rounded" />
            <div className="w-4 h-4 rounded-sm bg-[#0e1628]" />
          </div>
        ))}
      </div>
    </div>
  );
}
