import React from 'react'
export default function HighlightedText({ text, highlights = [] }){
  const parts = text.split(/(\s+)/)
  return (
    <div className="leading-relaxed text-ink">
      {parts.map((chunk,i)=>{
        if(/^\s+$/.test(chunk)) return <span key={i}>{chunk}</span>
        const h = highlights.find(x=> x.word === chunk)
        if(h){
          return (
            <span key={i} className="tooltip bg-yellow-300/20 border border-yellow-400/30 px-1 rounded-sm cursor-help">
              {chunk}
              <div className="panel">
                <div className="font-semibold text-accent">{h.category}</div>
                <div className="text-dim">{h.reason}</div>
              </div>
            </span>
          )
        }
        return <span key={i}>{chunk}</span>
      })}
    </div>
  )
}
