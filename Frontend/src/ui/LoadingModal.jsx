// src/ui/LoadingModal.jsx
import React, { useEffect, useMemo, useRef, useState } from 'react';

export default function LoadingModal({ show, title = 'Assembling analysis…' }) {
  if (!show) return null;

  // ---- timings (tweak as you like) ----
  const rows = 4;
  const cols = 7;
  const stepMs = 80;         // stagger per brick
  const buildMs = 560;       // single brick build
  const unbuildMs = 420;     // single brick unbuild
  const pauseAfterBuild = 500;
  const pauseAfterUnbuild = 500;

  const totalBricks = rows * cols;
  const totalBuildTime = (totalBricks - 1) * stepMs + buildMs;
  const totalUnbuildTime = (totalBricks - 1) * stepMs + unbuildMs;

  // Animation phases
  const [phase, setPhase] = useState('build');
  const timerRef = useRef(null);

  // Elapsed time
  const [elapsedMs, setElapsedMs] = useState(0);
  const startRef = useRef(null);
  const tickRef = useRef(null);

  // Bricks list (stored bottom→top, left→right for building)
  const bricks = useMemo(() => {
    const list = [];
    for (let r = rows - 1; r >= 0; r--) {
      for (let c = 0; c < cols; c++) {
        list.push({ r, c, key: `${r}-${c}` });
      }
    }
    return list;
  }, [rows, cols]);

  // Phase driver (loop build/hold/unbuild/hold)
  useEffect(() => {
    if (!show) return;
    const clear = () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
    const advance = () => {
      switch (phase) {
        case 'build':
          timerRef.current = setTimeout(() => setPhase('holdBuilt'), totalBuildTime);
          break;
        case 'holdBuilt':
          timerRef.current = setTimeout(() => setPhase('unbuild'), pauseAfterBuild);
          break;
        case 'unbuild':
          timerRef.current = setTimeout(() => setPhase('holdEmpty'), totalUnbuildTime);
          break;
        case 'holdEmpty':
          timerRef.current = setTimeout(() => setPhase('build'), pauseAfterUnbuild);
          break;
        default:
          setPhase('build');
      }
    };
    advance();
    return clear;
  }, [phase, show, totalBuildTime, pauseAfterBuild, totalUnbuildTime, pauseAfterUnbuild]);

  // Elapsed timer lifecycle
  useEffect(() => {
    if (!show) return;
    startRef.current = Date.now();
    setElapsedMs(0);
    tickRef.current = setInterval(() => {
      setElapsedMs(Date.now() - startRef.current);
    }, 250);
    return () => {
      if (tickRef.current) clearInterval(tickRef.current);
    };
  }, [show]);

  const mm = String(Math.floor(elapsedMs / 60000)).padStart(2, '0');
  const ss = String(Math.floor((elapsedMs % 60000) / 1000)).padStart(2, '0');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="relative rounded-2xl border border-line bg-[rgba(6,18,30,.95)] shadow-glow p-6 modal-in">
        <div className="text-sm font-semibold text-ink mb-3">
          {title}
        </div>
        <div className="text-sm font-semibold text-ink mb-3">
          <span className="text-dim">{mm}:{ss} elapsed</span>
        </div>

        <div
          className="grid"
          style={{
            gridTemplateColumns: `repeat(${cols}, 16px)`,
            gap: '6px',
          }}
        >
          {bricks.map((b, i) => {
            // BUILD order: bottom-left → top-right (as listed)
            // UNBUILD order: TOP-left → bottom-right
            //   Compute a top-first index: smaller r = top rows first
            const topFirstIndex = b.r * cols + b.c; // r=0 is top row
            const delay =
              phase === 'unbuild'
                ? topFirstIndex * stepMs               // start removing from the TOP
                : i * stepMs;                          // build as before (bottom up)

            const animName =
              phase === 'build'
                ? 'brickIn'
                : phase === 'unbuild'
                ? 'brickOut'
                : phase === 'holdBuilt'
                ? 'brickHold'
                : 'brickIdle';

            const animDuration =
              phase === 'build'
                ? `${buildMs}ms`
                : phase === 'unbuild'
                ? `${unbuildMs}ms`
                : '1200ms';

            return (
              <span
                key={b.key}
                className={`inline-block rounded-[3px] brick ${animName}`}
                style={{
                  width: 16,
                  height: 10,
                  animationDelay: `${delay}ms`,
                  animationDuration: animDuration,
                }}
              />
            );
          })}
        </div>

        <div className="mt-3 text-xs text-dim">Assembling analysis…</div>
      </div>

      {/* Local keyframes (scoped) */}
      <style>{`
        .modal-in {
          animation: modalIn 320ms cubic-bezier(0.22, 1, 0.36, 1) both;
        }
        @keyframes modalIn {
          from { opacity: 0; transform: translateY(6px) scale(0.98); }
          to   { opacity: 1; transform: translateY(0)    scale(1); }
        }

        .brick {
          background: linear-gradient(180deg, rgba(72,210,156,0.25), rgba(72,210,156,0.12));
          outline: 1px solid rgba(72,210,156,0.35);
          box-shadow: 0 0 8px rgba(72,210,156,0.15);
          transform-origin: 50% 100%;
          animation-fill-mode: both;
          animation-timing-function: cubic-bezier(0.2, 0.8, 0.2, 1);
        }

        @keyframes brickIn {
          0%   { opacity: 0; transform: translateY(14px) scale(0.92) rotateX(12deg); }
          65%  { opacity: 1; transform: translateY(0)    scale(1.02) rotateX(0deg); }
          100% { opacity: 1; transform: translateY(0)    scale(1.00) rotateX(0deg); }
        }
        .brickIn { animation-name: brickIn; }

        @keyframes brickOut {
          0%   { opacity: 1; transform: translateY(0)    scale(1.00) rotateX(0deg); }
          100% { opacity: 0; transform: translateY(14px) scale(0.92) rotateX(12deg); }
        }
        .brickOut { animation-name: brickOut; }

        @keyframes brickHoldKey {
          0%   { filter: brightness(1);    box-shadow: 0 0 8px rgba(72,210,156,0.15); }
          100% { filter: brightness(1.25); box-shadow: 0 0 14px rgba(72,210,156,0.25); }
        }
        .brickHold {
          animation-name: brickHoldKey;
          animation-direction: alternate;
          animation-iteration-count: infinite;
        }

        .brickIdle { opacity: 0; }
      `}</style>
    </div>
  );
}