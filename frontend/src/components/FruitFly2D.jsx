import React, { useEffect, useRef, useState } from 'react'

/**
 * 2D Anatomical Model of Drosophila melanogaster (Fruit Fly).
 * 
 * Features:
 * - Animated compound eyes flashing with sensory market vision (Green: Bullish, Red: Bearish, Amber: Volatile)
 * - Twitching sensory antennae responding to market momentum/volume
 * - Transparent head capsule showing Optic Lobe, Antennal Lobe, Mushroom Body, and Central Complex
 * - Translucent venated wings flapping dynamically (BUY: green burst, SELL: red dive, HOLD: hover)
 * - Abdominal neuromodulatory reservoir showing Dopamine (green/profit) and Octopamine (gold/arousal)
 * - Live biological telemetry: biological latency vs engine compute time, wingbeat Hz, and behavioral state
 * - Dockable in the corner with minimize/maximize controls
 */
export default function FruitFly2D({
  decision = 'HOLD',
  confidence = {},
  neurotransmitters = { dopamine: 0.5, octopamine: 0.3, serotonin: 0.6 },
  bioLatencyMs = 26.4,
  inferenceMs = 1.2,
  firingRateHz = 135,
  activeNeurons = 0,
  clusters = {},
  isTrading = false,
  latestTrade = null,
}) {
  const [minimized, setMinimized] = useState(false)
  const canvasRef = useRef(null)
  const wingPhase = useRef(0)
  const antennaPhase = useRef(0)

  // Behavioral state based on neurotransmitters and decision
  let flyState = 'FORAGING'
  let stateColor = '#3b82f6'
  if (decision === 'BUY') {
    flyState = 'HUNTING STRIKE (UP)'
    stateColor = '#10b981'
  } else if (decision === 'SELL') {
    flyState = 'DIVING EVASION (DOWN)'
    stateColor = '#ef4444'
  } else if (neurotransmitters.octopamine > 0.6) {
    flyState = 'HIGH-AROUSAL SCOUTING'
    stateColor = '#f59e0b'
  }

  useEffect(() => {
    let animId
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    const render = () => {
      if (minimized) return
      const dpr = window.devicePixelRatio || 1
      const w = canvas.clientWidth
      const h = canvas.clientHeight
      if (canvas.width !== w * dpr) {
        canvas.width = w * dpr
        canvas.height = h * dpr
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.clearRect(0, 0, w, h)

      const cx = w / 2
      const cy = h / 2 + 10

      // Speed of wing flapping depends on decision and octopamine
      const flapSpeed = decision === 'HOLD' ? 0.25 : 0.65 + (neurotransmitters.octopamine * 0.4)
      wingPhase.current += flapSpeed
      antennaPhase.current += 0.08

      const wingFlap = Math.sin(wingPhase.current)
      const antTwitch = Math.sin(antennaPhase.current) * 4

      // --- 1. WINGS (Rendered behind body) ---
      ctx.save()
      const wingColor = decision === 'BUY'
        ? 'rgba(16, 185, 129, 0.45)'
        : decision === 'SELL'
        ? 'rgba(239, 68, 68, 0.45)'
        : 'rgba(147, 197, 253, 0.25)'
      
      const wingBorder = decision === 'BUY'
        ? 'rgba(16, 185, 129, 0.8)'
        : decision === 'SELL'
        ? 'rgba(239, 68, 68, 0.8)'
        : 'rgba(191, 219, 254, 0.6)'

      // Left Wing
      ctx.save()
      ctx.translate(cx - 14, cy - 12)
      ctx.rotate(-0.45 + wingFlap * 0.22)
      ctx.beginPath()
      ctx.ellipse(-38, -35, 48, 18, -Math.PI / 4, 0, Math.PI * 2)
      ctx.fillStyle = wingColor
      ctx.fill()
      ctx.lineWidth = 1.5
      ctx.strokeStyle = wingBorder
      ctx.stroke()
      // Wing veins
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)'
      ctx.beginPath()
      ctx.moveTo(-10, -10)
      ctx.lineTo(-65, -55)
      ctx.moveTo(-25, -20)
      ctx.lineTo(-60, -35)
      ctx.stroke()
      ctx.restore()

      // Right Wing
      ctx.save()
      ctx.translate(cx + 14, cy - 12)
      ctx.rotate(0.45 - wingFlap * 0.22)
      ctx.beginPath()
      ctx.ellipse(38, -35, 48, 18, Math.PI / 4, 0, Math.PI * 2)
      ctx.fillStyle = wingColor
      ctx.fill()
      ctx.lineWidth = 1.5
      ctx.strokeStyle = wingBorder
      ctx.stroke()
      // Wing veins
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)'
      ctx.beginPath()
      ctx.moveTo(10, -10)
      ctx.lineTo(65, -55)
      ctx.moveTo(25, -20)
      ctx.lineTo(60, -35)
      ctx.stroke()
      ctx.restore()
      ctx.restore()

      // --- 2. LEGS ---
      ctx.strokeStyle = '#475569'
      ctx.lineWidth = 2
      ctx.lineCap = 'round'
      // 3 pairs of segmented legs
      const legOffsets = [-15, 0, 15]
      legOffsets.forEach((off, idx) => {
        // Left leg
        ctx.beginPath()
        ctx.moveTo(cx - 15, cy + off)
        ctx.lineTo(cx - 38 - idx * 3, cy + off + 8)
        ctx.lineTo(cx - 52 - idx * 4, cy + off + 26)
        ctx.stroke()
        // Right leg
        ctx.beginPath()
        ctx.moveTo(cx + 15, cy + off)
        ctx.lineTo(cx + 38 + idx * 3, cy + off + 8)
        ctx.lineTo(cx + 52 + idx * 4, cy + off + 26)
        ctx.stroke()
      })

      // --- 3. ABDOMEN (Segmented with glowing neuromodulator reservoir) ---
      const da = Math.max(0.1, Math.min(1.0, neurotransmitters.dopamine || 0.5))
      const oa = Math.max(0.1, Math.min(1.0, neurotransmitters.octopamine || 0.3))
      
      const abdoGrad = ctx.createLinearGradient(cx, cy + 8, cx, cy + 70)
      abdoGrad.addColorStop(0, '#1e293b')
      abdoGrad.addColorStop(0.5, `rgba(16, 185, 129, ${0.2 + da * 0.5})`) // Dopamine green
      abdoGrad.addColorStop(1, `rgba(245, 158, 11, ${0.15 + oa * 0.45})`) // Octopamine gold

      ctx.beginPath()
      ctx.ellipse(cx, cy + 38, 20, 32, 0, 0, Math.PI * 2)
      ctx.fillStyle = abdoGrad
      ctx.fill()
      ctx.lineWidth = 2
      ctx.strokeStyle = '#334155'
      ctx.stroke()

      // Abdominal Stripes (Drosophila tergites)
      ctx.strokeStyle = 'rgba(15, 23, 42, 0.85)'
      ctx.lineWidth = 3.5
      for (let s = cy + 20; s < cy + 62; s += 8) {
        ctx.beginPath()
        ctx.moveTo(cx - 16, s)
        ctx.lineTo(cx + 16, s)
        ctx.stroke()
      }

      // --- 4. THORAX (Flight muscle center) ---
      const thoraGrad = ctx.createRadialGradient(cx, cy - 8, 3, cx, cy - 8, 20)
      thoraGrad.addColorStop(0, '#475569')
      thoraGrad.addColorStop(0.7, '#1e293b')
      thoraGrad.addColorStop(1, '#0f172a')
      ctx.beginPath()
      ctx.ellipse(cx, cy - 6, 18, 17, 0, 0, Math.PI * 2)
      ctx.fillStyle = thoraGrad
      ctx.fill()
      ctx.lineWidth = 2
      ctx.strokeStyle = '#64748b'
      ctx.stroke()

      // Thorax scutellum triangle
      ctx.fillStyle = '#64748b'
      ctx.beginPath()
      ctx.moveTo(cx - 6, cy + 4)
      ctx.lineTo(cx + 6, cy + 4)
      ctx.lineTo(cx, cy + 11)
      ctx.closePath()
      ctx.fill()

      // --- 5. HEAD CAPSULE & BRAIN ---
      ctx.beginPath()
      ctx.ellipse(cx, cy - 30, 16, 14, 0, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(15, 23, 42, 0.95)'
      ctx.fill()
      ctx.lineWidth = 1.8
      ctx.strokeStyle = '#475569'
      ctx.stroke()

      // Visualized Connectome Sub-regions inside transparent head
      // Mushroom Body (Associative Memory)
      ctx.fillStyle = da > 0.6 ? '#10b981' : '#3b82f6'
      ctx.shadowColor = ctx.fillStyle
      ctx.shadowBlur = 6
      ctx.beginPath()
      ctx.arc(cx - 5, cy - 32, 3, 0, Math.PI * 2)
      ctx.arc(cx + 5, cy - 32, 3, 0, Math.PI * 2)
      ctx.fill()

      // Central Complex (Navigation & Steering)
      ctx.fillStyle = decision === 'BUY' ? '#10b981' : decision === 'SELL' ? '#ef4444' : '#f59e0b'
      ctx.beginPath()
      ctx.arc(cx, cy - 28, 4, 0, Math.PI * 2)
      ctx.fill()
      ctx.shadowBlur = 0

      // --- 6. COMPOUND EYES (Left & Right) ---
      const eyeColor = decision === 'BUY'
        ? '#10b981'
        : decision === 'SELL'
        ? '#ef4444'
        : neurotransmitters.octopamine > 0.5
        ? '#f59e0b'
        : '#dc2626' // Drosophila wildtype brick-red eyes

      // Left Eye
      ctx.save()
      ctx.translate(cx - 15, cy - 32)
      ctx.rotate(-0.25)
      ctx.beginPath()
      ctx.ellipse(0, 0, 8, 12, 0, 0, Math.PI * 2)
      ctx.fillStyle = eyeColor
      ctx.shadowColor = eyeColor
      ctx.shadowBlur = decision !== 'HOLD' ? 12 : 4
      ctx.fill()
      ctx.strokeStyle = '#7f1d1d'
      ctx.lineWidth = 1.5
      ctx.stroke()
      // Ommatidia facet pattern
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)'
      ctx.lineWidth = 1
      ctx.strokeRect(-3, -5, 6, 10)
      ctx.restore()

      // Right Eye
      ctx.save()
      ctx.translate(cx + 15, cy - 32)
      ctx.rotate(0.25)
      ctx.beginPath()
      ctx.ellipse(0, 0, 8, 12, 0, 0, Math.PI * 2)
      ctx.fillStyle = eyeColor
      ctx.shadowColor = eyeColor
      ctx.shadowBlur = decision !== 'HOLD' ? 12 : 4
      ctx.fill()
      ctx.strokeStyle = '#7f1d1d'
      ctx.lineWidth = 1.5
      ctx.stroke()
      // Ommatidia facet pattern
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)'
      ctx.lineWidth = 1
      ctx.strokeRect(-3, -5, 6, 10)
      ctx.restore()
      ctx.shadowBlur = 0

      // --- 7. ANTENNAE & FEATHERY ARISTAE ---
      ctx.strokeStyle = '#94a3b8'
      ctx.lineWidth = 1.5
      // Left Antenna
      ctx.beginPath()
      ctx.moveTo(cx - 4, cy - 42)
      ctx.lineTo(cx - 10 + antTwitch, cy - 54)
      ctx.lineTo(cx - 18 + antTwitch, cy - 64)
      ctx.stroke()
      // Arista branches
      ctx.lineWidth = 1
      ctx.beginPath()
      ctx.moveTo(cx - 10 + antTwitch, cy - 54)
      ctx.lineTo(cx - 16, cy - 56)
      ctx.moveTo(cx - 14 + antTwitch, cy - 59)
      ctx.lineTo(cx - 20, cy - 61)
      ctx.stroke()

      // Right Antenna
      ctx.lineWidth = 1.5
      ctx.beginPath()
      ctx.moveTo(cx + 4, cy - 42)
      ctx.lineTo(cx + 10 - antTwitch, cy - 54)
      ctx.lineTo(cx + 18 - antTwitch, cy - 64)
      ctx.stroke()
      // Arista branches
      ctx.lineWidth = 1
      ctx.beginPath()
      ctx.moveTo(cx + 10 - antTwitch, cy - 54)
      ctx.lineTo(cx + 16, cy - 56)
      ctx.moveTo(cx + 14 - antTwitch, cy - 59)
      ctx.lineTo(cx + 20, cy - 61)
      ctx.stroke()

      animId = requestAnimationFrame(render)
    }

    animId = requestAnimationFrame(render)
    return () => cancelAnimationFrame(animId)
  }, [decision, confidence, neurotransmitters, minimized])

  return (
    <div className={`fly-2d-corner-card ${minimized ? 'minimized' : ''}`}>
      {/* Header bar */}
      <div className="fly-card-header">
        <div className="fly-title-badge">
          <span className="fly-pulse-dot" style={{ background: stateColor }} />
          <span className="fly-label">Drosophila Melanogaster</span>
        </div>
        <button
          className="fly-toggle-btn"
          onClick={() => setMinimized(!minimized)}
          title={minimized ? 'Expand Model' : 'Minimize Model'}
        >
          {minimized ? '▲ Expand' : '▼'}
        </button>
      </div>

      {!minimized ? (
        <>
          {/* Main Visualizer */}
          <div className="fly-visualizer-container">
            <canvas ref={canvasRef} className="fly-canvas" />
            <div className="fly-state-overlay" style={{ borderColor: stateColor }}>
              <span className="state-name" style={{ color: stateColor }}>{flyState}</span>
              <span className="state-action">
                Action: <strong>{decision}</strong> ({((confidence[decision] || 0.33) * 100).toFixed(0)}%)
              </span>
            </div>
          </div>

          {/* Neurotransmitters Telemetry */}
          <div className="fly-neuro-meters">
            <div className="neuro-meter">
              <div className="neuro-meta">
                <span>Dopamine (DA)</span>
                <span className="neuro-val green">{((neurotransmitters.dopamine || 0.5) * 100).toFixed(0)}%</span>
              </div>
              <div className="meter-track">
                <div
                  className="meter-fill green"
                  style={{ width: `${Math.min(100, (neurotransmitters.dopamine || 0.5) * 100)}%` }}
                />
              </div>
            </div>

            <div className="neuro-meter">
              <div className="neuro-meta">
                <span>Octopamine (OA)</span>
                <span className="neuro-val gold">{((neurotransmitters.octopamine || 0.3) * 100).toFixed(0)}%</span>
              </div>
              <div className="meter-track">
                <div
                  className="meter-fill gold"
                  style={{ width: `${Math.min(100, (neurotransmitters.octopamine || 0.3) * 100)}%` }}
                />
              </div>
            </div>
          </div>

          {/* Bio vs Inference Latency Bar */}
          <div className="fly-stats-grid">
            <div className="fly-stat-pill">
              <span className="stat-k">Bio Reflex</span>
              <span className="stat-v cyan">{bioLatencyMs} ms</span>
            </div>
            <div className="fly-stat-pill">
              <span className="stat-k">Inference</span>
              <span className="stat-v">{inferenceMs} ms</span>
            </div>
            <div className="fly-stat-pill">
              <span className="stat-k">Spike Rate</span>
              <span className="stat-v">{firingRateHz} Hz</span>
            </div>
            <div className="fly-stat-pill">
              <span className="stat-k">Active Spikes</span>
              <span className="stat-v purple">{activeNeurons}</span>
            </div>
          </div>
        </>
      ) : (
        <div className="fly-mini-badge" onClick={() => setMinimized(false)}>
          <span className="mini-icon">🪰</span>
          <span className="mini-state" style={{ color: stateColor }}>{decision}</span>
          <span className="mini-bio">{bioLatencyMs}ms</span>
        </div>
      )}
    </div>
  )
}
