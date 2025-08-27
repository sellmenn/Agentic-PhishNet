import React from 'react'

export default function RightInspector({ email, onClose }){
  const open = Boolean(email)
  return (
    <div className={`fixed inset-0 z-30 pointer-events-none ${open? '':'hidden'}`}>
      <div className={`absolute right-0 top-[64px] h-[calc(100vh-64px)] w-[29rem] pointer-events-auto transform transition-transform duration-300 ${open? 'translate-x-0':'translate-x-full'}`}>
        <div className="h-full rounded-l-2xl border-l border-line right-overlay p-4">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-ink">Inspector</div>
            <button onClick={onClose} className="chip">Close</button>
          </div>
          <div className="mt-3 space-y-3 text-sm text-ink">
            <div className="pill rounded-xl p-3 space-y-2">
              <div className="text-xs text-dim">Verdict</div>
              {!email ? null :
                email.type==='phishing' ? <div className="badge" style={{color:'#fca5a5', borderColor:'rgba(252,165,165,.35)'}}>Phishing</div> :
                email.type==='questionable' ? <div className="badge">Questionable</div> :
                <div className="badge">Legitimate</div>}
            </div>
            <div className="pill rounded-xl p-3">
              <div className="text-xs text-dim mb-2">Signals</div>
              <div className="space-y-2">
                {Bar('Domain Reputation', 72, 'bg-emerald-400')}
                {Bar('Urgency Language', 54, 'bg-yellow-400')}
                {Bar('Link Mismatch', 15, 'bg-red-400')}
              </div>
            </div>
            <div className="pill rounded-xl p-3">
              <div className="text-xs text-dim mb-2">Quick Actions</div>
              <div className="flex flex-wrap gap-2">
                {['Quarantine','Allowlist','Report','Mute Thread'].map(x=>(<button key={x} className="chip">{x}</button>))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function Bar(label, v, color){
  return (
    <div>
      <div className="flex items-center justify-between text-xs text-dim"><span>{label}</span><span>{v}</span></div>
      <div className="w-full h-1.5 rounded bg-[#0b1423]"><div className={`h-full ${color}`} style={{width:`${v}%`}}/></div>
    </div>
  )
}
