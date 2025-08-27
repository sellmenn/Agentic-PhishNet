import React from 'react'
export default function BgCircuits(){
  return (
    <svg className="pointer-events-none absolute inset-0 opacity-15" xmlns="http://www.w3.org/2000/svg">
      <defs><linearGradient id="g1" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stopColor="#56e2ff"/><stop offset="100%" stopColor="#8b5cf6"/></linearGradient></defs>
      <g stroke="url(#g1)" strokeWidth="2" fill="none">
        <path d="M120,120 h120 v40 h40" /><circle cx="120" cy="120" r="4" fill="#56e2ff" />
        <path d="M220,300 h160 v-60 h60" /><circle cx="220" cy="300" r="4" fill="#56e2ff"/>
        <path d="M60,520 h200 v-40 h60" /><circle cx="60" cy="520" r="4" fill="#56e2ff"/>
      </g>
    </svg>
  )
}
