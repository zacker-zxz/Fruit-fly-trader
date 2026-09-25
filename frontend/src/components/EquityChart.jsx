import React from 'react'

export default function EquityChart({ points }) {
  if (points.length < 2) return <Empty />
  const w = 600, h = 100
  const min = Math.min(...points), max = Math.max(...points)
  const span = max - min || 1
  const path = points.map((v, i) => {
    const x = (i / (points.length - 1)) * w
    const y = h - ((v - min) / span) * (h - 10) - 5
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
  const up = points[points.length - 1] >= points[0]
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      <path d={path} fill="none" stroke={up ? '#3f9d6b' : '#c05555'} strokeWidth="1.2" />
    </svg>
  )
}

function Empty() {
  return <svg viewBox="0 0 600 100" preserveAspectRatio="none" />
}
