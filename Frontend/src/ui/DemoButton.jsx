// DemoButton.jsx
import React from 'react';

export default function DemoButton({ onClick, loading, disabled }) {
  const isDisabled = !!loading || !!disabled;
  const label = loading ? 'Running…' : disabled ? 'Loaded' : 'Demo';

  return (
    <button
      onClick={onClick}
      disabled={isDisabled}
      aria-disabled={isDisabled}
      className={`absolute bottom-5 left-7 px-4 py-2 rounded-lg text-white font-medium transition
        ${isDisabled
          ? 'bg-green-800 opacity-70 cursor-not-allowed'
          : 'bg-green-600 hover:bg-green-700 active:bg-green-800'}`}
      title={disabled ? 'Demo already loaded' : undefined}
    >
      {label}
    </button>
  );
}