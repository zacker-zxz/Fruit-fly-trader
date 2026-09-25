import React, { useEffect, useRef } from 'react'

// Renders a fixed 2D layout of the sampled brain. Node positions are computed
// once from a deterministic layout; activation pulses and prune/trade events
// come from the live engine event stream.
export default function BrainCanvas({ events }) {
  const ref = useRef(null)
  const layout = useRef(null)
  const pulses = useRef([])
  const trades = useRef([])

  useEffect(() => {
    if (!layout.current) {
      // deterministic pseudo-layout: sensory arc, interior cloud, decision row
      const rng = mulberry(42)
      const nodes = []
      for (let i = 0; i < 90; i++) {
        let x, y
        if (i < 15) { // sensory
          x = 40 + i * 6
          y = 26
        } else if (i >= 87) { // decision neurons
          x = 40 + (i - 87) * 42 + 20
          y = 175
        } else {
          x = 30 + rng() * 250
          y = 55 + rng() * 100
        }
        nodes.push({ x, y, r: i >= 87 ? 5 : 2.5, sensory: i < 15, decision: i >= 87 })
      }
      const edges = []
      const erng = mulberry(7)
      for (let i = 0; i < 140; i++) {
        const a = Math.floor(erng() * nodes.length)
        const b = Math.floor(erng() * nodes.length)
        if (a !== b) edges.push({ a, b, w: 0.3 + erng() * 0.7 })
      }
      layout.current = { nodes, edges }
    }
  }, [])

  useEffect(() => {
    const last = events[events.length - 1]
    if (!last) return
    if (last.type === 'trade') trades.current.push({ polarity: last.polarity, t: Date.now() })
    if (last.type === 'prune') pulses.current.push({ id: last.id, prune: true, t: Date.now() })
    else pulses.current.push({ id: Math.floor(Math.random() * 90), t: Date.now() })
  }, [events])

  useEffect(() => {
    let raf
    const draw = () => {
      const canvas = ref.current
      if (!canvas || !layout.current) { raf = requestAnimationFrame(draw); return }
      const ctx = canvas.getContext('2d')
      const dpr = window.devicePixelRatio || 1
      const w = canvas.clientWidth, h = canvas.clientHeight
      if (canvas.width !== w * dpr) { canvas.width = w * dpr; canvas.height = h * dpr }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.clearRect(0, 0, w, h)

      const { nodes, edges } = layout.current
      const now = Date.now()

      // edges: thin gray lines, brightness by weight
      ctx.lineWidth = 1
      for (const e of edges) {
        const a = nodes[e.a], b = nodes[e.b]
        ctx.strokeStyle = `rgba(120,130,145,${0.12 + e.w * 0.15})`
        ctx.beginPath()
        ctx.moveTo(a.x, a.y)
        ctx.lineTo(b.x, b.y)
        ctx.stroke()
      }

      // recent trade polarity flashes the whole field subtly
      const recentTrade = trades.current.find(t => now - t.t < 900)
      if (recentTrade) {
        const alpha = 0.12 * (1 - (now - recentTrade.t) / 900)
        ctx.fillStyle = recentTrade.polarity > 0 ? `rgba(63,157,107,${alpha})` : `rgba(192,85,85,${alpha})`
        ctx.fillRect(0, 0, w, h)
      }

      // nodes
      const activePulse = new Set(pulses.current.filter(p => !p.prune && now - p.t < 700).map(p => p.id))
      const pruned = new Set(pulses.current.filter(p => p.prune && now - p.t > 700).map(p => p.id))
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i]
        if (pruned.has(i)) continue
        const isActive = activePulse.has(i)
        if (n.sensory) ctx.fillStyle = '#7d8b9c'
        else if (n.decision) ctx.fillStyle = '#4c8fd6'
        else ctx.fillStyle = isActive ? '#c8cdd6' : '#4a4f58'
        ctx.beginPath()
        ctx.arc(n.x, n.y, n.r + (isActive ? 2 : 0), 0, Math.PI * 2)
        ctx.fill()
      }

      pulses.current = pulses.current.filter(p => now - p.t < 900)
      if (pulses.current.length > 200) pulses.current = pulses.current.slice(-200)
      trades.current = trades.current.filter(t => now - t.t < 900)
      raf = requestAnimationFrame(draw)
    }
    raf = requestAnimationFrame(draw)
    return () => cancelAnimationFrame(raf)
  }, [])

  return <canvas ref={ref} />
}

function mulberry(seed) {
  let a = seed >>> 0
  return () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}
