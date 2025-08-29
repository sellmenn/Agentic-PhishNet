import React, { useMemo } from 'react';
import TooltipCard from './TooltipCard.jsx';

function kindFromAgentName(name = '') {
  if (/fact/i.test(name)) return 'Factual';
  if (/language/i.test(name)) return 'Language';
  return 'Other';
}

// helpers used for merging + tooltip
const normText = (s = '') => s.replace(/\s+/g, ' ').trim().toLowerCase();
const reasonSig = (entries) => {
  // signature of reasons per type (ignore s/e): ensures segments only merge if reasons match
  const set = new Set(
    entries.map((m) => `${m.kind}|${normText(m.reason || '')}`)
  );
  return Array.from(set).sort().join('||');
};
const dedupeEntriesByReasonAndSpan = (entries) => {
  const seen = new Set();
  const out = [];
  for (const m of entries) {
    const key = `${m.kind}|${normText(m.reason || '')}|${m.s}|${m.e}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(m);
  }
  return out;
};

export default function HighlightedText({ text = '', detection }) {
  const segments = useMemo(() => {
    if (!text || !detection) return [{ s: 0, e: text.length, entries: [], kinds: [], sig: '' }];

    const agentKinds = (detection.agent_types || []).map(kindFromAgentName);
    const hl = detection.highlight || [];
    const marks = [];

    // Build marks: {s,e,kind,reason}
    if (Array.isArray(hl) && Array.isArray(hl[0])) {
      hl.forEach((arr, agentIdx) => {
        const kind = agentKinds[agentIdx] || 'Other';
        (arr || []).forEach((h) => {
          if (h && Number.isFinite(h.s_idx) && Number.isFinite(h.e_idx) && h.e_idx > h.s_idx) {
            marks.push({ s: h.s_idx, e: h.e_idx, kind, reason: h.reasoning || '' });
          }
        });
      });
    } else if (Array.isArray(hl)) {
      (hl || []).forEach((h) => {
        if (h && Number.isFinite(h.s_idx) && Number.isFinite(h.e_idx) && h.e_idx > h.s_idx) {
          marks.push({ s: h.s_idx, e: h.e_idx, kind: 'Language', reason: h.reasoning || '' });
        }
      });
    }

    if (marks.length === 0) return [{ s: 0, e: text.length, entries: [], kinds: [], sig: '' }];

    // Split by all boundaries from all marks
    const stops = new Set([0, text.length]);
    marks.forEach((m) => {
      stops.add(Math.max(0, Math.min(text.length, m.s)));
      stops.add(Math.max(0, Math.min(text.length, m.e)));
    });
    const edges = Array.from(stops).sort((a, b) => a - b);

    // initial small segments (leaf pieces)
    const leafSegs = [];
    for (let i = 0; i < edges.length - 1; i++) {
      const s = edges[i], e = edges[i + 1];
      if (e <= s) continue;
      const entries = marks.filter((m) => m.s <= s && m.e >= e);
      const kinds = Array.from(new Set(entries.map((m) => m.kind))).sort();
      const dedup = dedupeEntriesByReasonAndSpan(entries);
      const sig = reasonSig(dedup); // signature by reasons (type+normalized text)
      leafSegs.push({ s, e, entries: dedup, kinds, sig });
    }

    // Merge adjacent segments only if both the kind set AND reason signature match
    const merged = [];
    for (const seg of leafSegs) {
      const last = merged[merged.length - 1];
      const same =
        last &&
        last.e === seg.s &&
        last.sig === seg.sig &&
        last.kinds.length === seg.kinds.length &&
        last.kinds.every((k, idx) => k === seg.kinds[idx]);
      if (same) {
        // extend, keep entries as-is (they are the same reason set)
        last.e = seg.e;
      } else {
        merged.push({ ...seg });
      }
    }

    return merged;
  }, [text, detection]);

  return (
    <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
      {segments.map((seg, i) => {
        const slice = text.slice(seg.s, seg.e);
        if (seg.entries.length === 0) return <span key={i}>{slice}</span>;

        const hasF = seg.kinds.includes('Factual');
        const hasL = seg.kinds.includes('Language');
        // Colors: Factual (cyan), Language (amber), overlap = blended gradient
        const FACT_BG = 'rgba(34, 211, 238, 0.22)';   // cyan-400/22
        const FACT_BORDER = 'rgba(34, 211, 238, 0.65)';
        const LANG_BG = 'rgba(245, 158, 11, 0.22)';   // amber-500/22
        const LANG_BORDER = 'rgba(245, 158, 11, 0.65)';
        const MIX_BORDER = 'rgba(167, 139, 250, 0.65)'; // violet border for overlap

        const cls = 'relative inline align-baseline group rounded';
        const spanStyle = {
          boxDecorationBreak: 'clone',
          WebkitBoxDecorationBreak: 'clone',
        };
        if (hasF && hasL) {
          spanStyle.backgroundImage = `linear-gradient(90deg, ${FACT_BG} 0 50%, ${LANG_BG} 50% 100%)`;
          spanStyle.boxShadow = `0 0 0 2px ${MIX_BORDER}`;
        } else if (hasF) {
          spanStyle.backgroundColor = FACT_BG;
          spanStyle.boxShadow = `0 0 0 1px ${FACT_BORDER}`;
        } else {
          spanStyle.backgroundColor = LANG_BG;
          spanStyle.boxShadow = `0 0 0 1px ${LANG_BORDER}`;
        }

        // Tooltip items for THIS spliced piece:
        // choose entries that cover seg.s..seg.e, then per type keep most specific (smallest width)
        const covering = seg.entries.filter((e) => e.s <= seg.s && e.e >= seg.e && e.reason);
        const bestByTypeReason = new Map(); // key: type|normReason -> {type,reason,width}
        for (const e of covering) {
          const type = e.kind;
          const rkey = normText(e.reason || '');
          if (!rkey) continue;
          const id = `${type}|${rkey}`;
          const width = e.e - e.s;
          const cur = bestByTypeReason.get(id);
          if (!cur || width < cur.width) bestByTypeReason.set(id, { type, reason: e.reason, width });
        }
        let items = Array.from(bestByTypeReason.values());

        // sort: Factual first, then Language, then Other; narrower first within type
        const order = (t) => (t === 'Factual' ? 0 : t === 'Language' ? 1 : 2);
        items.sort((a, b) => (order(a.type) - order(b.type)) || (a.width - b.width));

        return (
          <span
            key={i}
            className={cls}
            style={spanStyle}
          >
            {slice}
            <TooltipCard
              items={items.map(({ type, reason }) => ({ type, reason }))}
              className="
                opacity-0 translate-y-1
                group-hover:opacity-100 group-hover:translate-y-0
                transition duration-150 ease-out
              "
            />
          </span>
        );
      })}
    </div>
  );
}
