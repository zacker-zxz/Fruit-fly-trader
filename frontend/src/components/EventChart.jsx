import React from 'react'

export default function EventChart({ rewards, sizes }) {
  const w = 600, h = 90
  const maxLen = Math.max(rewards.length, sizes.length)
  if (maxLen < 2) return <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" />
  const bars = rewards.slice(-120).map((r, i) => {
    const x = (i / Math.max(1, rewards.slice(-120).length - 1)) * w
    const bh = Math.abs(r.v) * (h / 2 - 4)
    const y = r.v >= 0 ? h / 2 - bh : h / 2
    return <rect key={i} x={x} y={y} width={Math.max(1, w / 140)} height={Math.max(0.5, bh)}
      fill={r.v >= 0 ? '#3f9d6b' : '#c05555'} opacity="0.8" />
  })
  const line = sizes.slice(-120)
  const maxN = Math.max(...line.map(s => s.n), 1)
  const path = line.map((s, i) => {
    const x = (i / Math.max(1, line.length - 1)) * w
    const y = h - 4 - (s.n / maxN) * (h / 3)
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      <line x1="0" y1={h / 2} x2={w} y2={h / 2} stroke="#2a2d33" strokeWidth="1" />
      {bars}
      <path d={path} fill="none" stroke="#8a8f98" strokeWidth="1" strokeDasharray="3 3" />
    </svg>
  )
}
