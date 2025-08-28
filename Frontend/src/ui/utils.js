export function classifyReasoning(r) {
  const t = (r || '').toLowerCase();
  const L = ['generic','urgency','improper','impersonal','tone','vague','keep the email','engage','language','phrasing'];
  const F = ['claim','verified','format','id','domain','order','access','support page','link','sensitive information'];
  const s = new Set();
  if (L.some((k) => t.includes(k))) s.add('Language');
  if (F.some((k) => t.includes(k))) s.add('Factual');
  if (s.size === 0) s.add('Language');
  return [...s];
}

// NEW: confidence → status mapping
export function statusFromConfidence(c = 0) {
  if (c <= 0.4) return { key: 'phishing', label: 'Phishing', color: '#fca5a5' };
  if (c < 0.6)  return { key: 'flagged',  label: 'Flagged',  color: '#fbbf24' };
  return { key: 'cleared', label: 'Cleared', color: '#34d399' };
}