import React, { useEffect, useMemo, useRef, useState } from 'react'
import TopBar from './TopBar.jsx'
import HoverSidebar from './HoverSidebar.jsx'
import EmailList from './EmailList.jsx'
import EmailViewer from './EmailViewer.jsx'
import RightInspector from './RightInspector.jsx'
import BgCircuits from './BgCircuits.jsx'

export default function App(){
  // Adjustable split percentage for inbox list (left)
  const [split, setSplit] = useState(42) // percent
  const [dragging, setDragging] = useState(false)
  const containerRef = useRef(null)

  const startDrag = () => {
    setDragging(true)
    document.body.classList.add('no-select')
    document.body.style.cursor = 'col-resize'
  }
  useEffect(()=>{
    if(!dragging) return
    const onMove = (e) => {
      const w = window.innerWidth
      const x = e.touches ? e.touches[0].clientX : e.clientX
      let p = Math.round((x / w) * 100)
      if (p < 20) p = 20
      if (p > 75) p = 75
      setSplit(p)
    }
    const onUp = () => {
      setDragging(false)
      document.body.classList.remove('no-select')
      document.body.style.cursor = 'auto'
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    window.addEventListener('touchmove', onMove, {passive:false})
    window.addEventListener('touchend', onUp)
    return () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
      window.removeEventListener('touchmove', onMove)
      window.removeEventListener('touchend', onUp)
    }
  }, [dragging])

  // Inbox/selection
  const [emails, setEmails] = useState(()=>[
    { sender:'noreply@cloudbox.com', subject:'Your invoice is ready', body:'Hi, your monthly invoice is attached. Thanks!', type:'legit' },
    { sender:'promo@odd.biz', subject:'Win a prize!', body:'Claim your reward now', type:'questionable' },
  ])

  // Seed a phishing email as the open item to demo inspector + highlights
  const phishingDemo = useMemo(()=> ({
    sender:'security@faksebank.com',
    subject:'Immediate action required: verify your account',
    type:'phishing',
    body:'Please login immediately to verify your account or it will be suspended. Visit http://faksebank.com/login to continue.',
    highlights:[
      { word:'login', category:'Factual', reason:'Banks rarely ask to log in via email links' },
      { word:'immediately', category:'Language', reason:'Urgency is a common phishing tactic' },
      { word:'http://faksebank.com/login', category:'Links', reason:'Suspicious domain mismatch' }
    ]
  }), [])

  const [selected, setSelected] = useState(phishingDemo)
  const [sidebarPulse, setSidebarPulse] = useState(0)

  useEffect(()=>{
    // Dev helpers to simulate messages or integrate your agent
    window.PhishNetMail = {
      send: e => setEmails(prev => e.type==='phishing' ? prev : [e, ...prev]),
      mockLegit: ()=> window.PhishNetMail.send({sender:'tina@company.com',subject:'Standup notes',body:'Here are the notes from daily.',type:'legit'}),
      mockQuestionable: ()=> window.PhishNetMail.send({sender:'promo@odd.biz',subject:'Win a prize!',body:'Claim your reward now',type:'questionable'}),
      mockPhish: ()=> setSelected(phishingDemo)
    }
  }, [phishingDemo])

  return (
    <div className="h-full flex flex-col relative" ref={containerRef}>
      <BgCircuits />
      <TopBar onHamburgerHover={()=> setSidebarPulse(x=>x+1)} />
      <HoverSidebar pulse={sidebarPulse} />
      <div className="flex w-full" style={{height:'calc(100vh - 64px)'}}>
        <EmailList emails={emails} onSelect={setSelected} style={{ width: split + '%' }} />
        {/* splitter */}
        <div className="splitter" onMouseDown={startDrag} onTouchStart={startDrag} />
        <EmailViewer email={selected} style={{ width: (100 - split) + '%'}} />
      </div>
      <RightInspector email={selected} onClose={()=> setSelected(null)} />
    </div>
  )
}
