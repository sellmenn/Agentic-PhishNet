import React, { useEffect, useMemo, useState } from 'react';
import TopBar from './TopBar.jsx';
import HoverSidebar from './HoverSidebar.jsx';
import EmailList from './EmailList.jsx';
import EmailViewer from './EmailViewer.jsx';
import BgCircuits from './BgCircuits.jsx';
import InspectorCard from './InspectorCard.jsx';
const demoDetection = {
  final_confidence: 0.65135,
  agent_types: ['Language Analysis Agent', 'Fact Checking Agent'],
  agent_confidence: [0.6, 0.7027],
  summary:
    '\nLanguage Analysis Agent : The email appears to be a legitimate communication from Pearson Education, but it contains some elements that could raise suspicion, such as the generic greeting and the request for sensitive information.\n\nFact Checking Agent : Verified 7 factual claim(s); 4 appear suspicious. Overall confidence: 0.70.\n',
  highlight: [
    {
      s_idx: 0,
      e_idx: 11,
      reasoning:
        'Generic greeting that lacks personalization, which is common in phishing attempts.',
    },
    { s_idx: 43, e_idx: 86, reasoning: 'Creates a sense of urgency without a specific deadline.' },
    { s_idx: 104, e_idx: 174, reasoning: 'Vague instructions that could lead to phishing links.' },
    {
      s_idx: 329,
      e_idx: 367,
      reasoning: 'Impersonal phrasing that could indicate a lack of genuine customer service.',
    },
    {
      s_idx: 41,
      e_idx: 83,
      reasoning:
        'Creates a sense of urgency to keep the email, which is a common tactic in phishing.',
    },
    { s_idx: 109, e_idx: 164, reasoning: 'Vague instructions that could lead to phishing links.' },
    {
      s_idx: 292,
      e_idx: 327,
      reasoning: 'Generic question that could be used to elicit a response or further engagement.',
    },
    {
      s_idx: 265,
      e_idx: 280,
      reasoning: 'Encourages clicking a link, which is a common phishing tactic.',
    },
    {
      s_idx: 329,
      e_idx: 392,
      reasoning: 'Requests sensitive information that could be used for social engineering.',
    },
    {
      s_idx: 54,
      e_idx: 75,
      reasoning:
        'The Course ID format does not align with typical educational institution practices, raising suspicion about its legitimacy.',
    },
    {
      s_idx: 196,
      e_idx: 218,
      reasoning:
        'The claim lacks sufficient context and does not match typical account ID formats or verification processes.',
    },
    {
      s_idx: 221,
      e_idx: 240,
      reasoning:
        'The order ID format does not align with standard practices for legitimate transactions, raising suspicion.',
    },
    {
      s_idx: 138,
      e_idx: 161,
      reasoning:
        'The claim lacks specificity and does not align with typical access authority structures in educational institutions.',
    },
  ],
};
export default function App() {
  const [split, setSplit] = useState(42);
  const [dragging, setDragging] = useState(false);
  const [emails, setEmails] = useState(() => [
    {
      sender: 'noreply@cloudbox.com',
      subject: 'Your invoice is ready',
      body: 'Hi, your monthly invoice is attached. Thanks!',
      type: 'legit',
    },
    {
      sender: 'promo@odd.biz',
      subject: 'Win a prize!',
      body: 'Claim your reward now',
      type: 'questionable',
    },
  ]);
  const demoText =
    'Dear Student, Please keep this email for your records. To continue using your account, login now to verify your details and maintain access to course materials. If you have questions, visit our support page or reply to this message. Kindly provide your Course ID and account ID along with your order ID for verification. Our team aims to respond as soon as possible.';
  const phishingDemo = useMemo(
    () => ({
      sender: 'support@pearson-edu.example',
      subject: 'Important: Verify your course access',
      type: 'phishing',
      body: demoText,
      detection: demoDetection,
    }),
    [],
  );
  const [selected, setSelected] = useState(phishingDemo);
  const [sidebarPulse, setSidebarPulse] = useState(0);
  const startDrag = () => {
    setDragging(true);
    document.body.classList.add('no-select');
    document.body.style.cursor = 'col-resize';
  };
  useEffect(() => {
    if (!dragging) return;
    const onMove = (e) => {
      const w = window.innerWidth;
      const x = e.touches ? e.touches[0].clientX : e.clientX;
      let p = Math.round((x / w) * 100);
      if (p < 20) p = 20;
      if (p > 75) p = 75;
      setSplit(p);
    };
    const onUp = () => {
      setDragging(false);
      document.body.classList.remove('no-select');
      document.body.style.cursor = 'auto';
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    window.addEventListener('touchmove', onMove, { passive: false });
    window.addEventListener('touchend', onUp);
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      window.removeEventListener('touchmove', onMove);
      window.removeEventListener('touchend', onUp);
    };
  }, [dragging]);
  useEffect(() => {
    window.PhishNetMail = {
      send: (e) => setEmails((p) => (e.type === 'phishing' ? p : [e, ...p])),
      mockLegit: () =>
        window.PhishNetMail.send({
          sender: 'tina@company.com',
          subject: 'Standup notes',
          body: 'Here are the notes from daily.',
          type: 'legit',
        }),
      mockQuestionable: () =>
        window.PhishNetMail.send({
          sender: 'promo@odd.biz',
          subject: 'Win a prize!',
          body: 'Claim your reward now',
          type: 'questionable',
        }),
      mockPhish: () => setSelected(phishingDemo),
    };
  }, [phishingDemo]);
  return (
    <div className="h-full flex flex-col relative">
      <BgCircuits />
      <TopBar onHamburgerHover={() => setSidebarPulse((x) => x + 1)} />
      <HoverSidebar pulse={sidebarPulse} />
      <div
        className="flex w-full"
        style={{ height: 'calc(100vh - 64px)' }}
      >
        <EmailList
          emails={emails}
          onSelect={setSelected}
          style={{ width: split + '%' }}
        />
        <div
          className="splitter"
          onMouseDown={startDrag}
          onTouchStart={startDrag}
        />
        <EmailViewer
          email={selected}
          style={{ width: 100 - split + '%' }}
        />
      </div>
      <InspectorCard detection={selected?.detection} />
    </div>
  );
}
