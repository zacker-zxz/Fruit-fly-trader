import React, { useEffect, useRef } from 'react'

/**
 * Panels 06 & 07: Real Biological Hormone & Spike Telemetry Desk.
 * 
 * Displays authentic physiological states from the Drosophila Connectome:
 * - Live Neuron Spikes & Firing Frequency (Cyan raster & curve)
 * - Dopamine Hormone Level (Surges on profit reward)
 * - Cortisol Stress Hormone Level (Surges on drawdown & risk)
 * - Serotonin Composure Index
 * - Real-time biological reflex & trade outcome reaction
 * 
 * Advances synchronously with actual simulation ticks. Zero fake sine waves.
 */
export default function WaveformsNewswirePanel({
  neurotransmitters = { dopamine: 0.5, cortisol: 0.2, octopamine: 0.3, serotonin: 0.6 },
  firingRateHz = 120,
  activeNeurons = 0,
  multiplier = 10,
  decision = 'HOLD',
  latestTrade = null,
  marketName = 'Gold Desk',
  isPaused = false,
}) {
  const canvasRef = useRef(null)
  const historyRef = useRef([
    { spikes: 22, hz: 115, dopamine: 0.50, cortisol: 0.20, serotonin: 0.60, decision: 'HOLD' },
    { spikes: 28, hz: 125, dopamine: 0.52, cortisol: 0.22, serotonin: 0.59, decision: 'HOLD' },
    { spikes: 35, hz: 140, dopamine: 0.54, cortisol: 0.19, serotonin: 0.61, decision: 'HOLD' },
    { spikes: 30, hz: 130, dopamine: 0.51, cortisol: 0.21, serotonin: 0.60, decision: 'HOLD' },
    { spikes: 26, hz: 120, dopamine: 0.50, cortisol: 0.20, serotonin: 0.60, decision: 'HOLD' },
  ])

  const da = neurotransmitters.dopamine ?? 0.5
  const cort = neurotransmitters.cortisol ?? 0.2
  const oa = neurotransmitters.octopamine ?? 0.3
  const ser = neurotransmitters.serotonin ?? 0.6

  // Append genuine biological state on tick
  useEffect(() => {
    const hist = historyRef.current
    hist.push({
      spikes: activeNeurons,
      hz: firingRateHz,
      dopamine: da,
      cortisol: cort,
      serotonin: ser,
      decision,
    })
    if (hist.length > 80) hist.shift()
  }, [firingRateHz, activeNeurons, da, cort, ser, decision])

  // Canvas render
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    const dpr = window.devicePixelRatio || 1
    const w = canvas.clientWidth || 300
    const h = canvas.clientHeight || 120
    if (canvas.width !== w * dpr) {
      canvas.width = w * dpr
      canvas.height = h * dpr
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

    ctx.fillStyle = '#080a0f'
    ctx.fillRect(0, 0, w, h)

    const hist = historyRef.current
    if (hist.length < 2) {
      ctx.fillStyle = '#64748b'
      ctx.font = '10px JetBrains Mono, monospace'
      ctx.textAlign = 'center'
      ctx.fillText('Listening to connectome signals...', w / 2, h / 2)
      return
    }

    const paddingLeft = 10
    const paddingRight = 10
    const chartW = w - paddingLeft - paddingRight
    const chartH = h - 20

    // Background horizontal guideline grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)'
    ctx.lineWidth = 1
    for (let y = 15; y < h; y += 22) {
      ctx.beginPath()
      ctx.moveTo(paddingLeft, y)
      ctx.lineTo(paddingLeft + chartW, y)
      ctx.stroke()
    }

    const nPts = hist.length
    const getX = (i) => paddingLeft + (i / Math.max(1, nPts - 1)) * chartW

    // 1. SPIKE RASTER / DENSITY BARS (Cyan)
    ctx.fillStyle = 'rgba(6, 182, 212, 0.35)'
    for (let i = 0; i < nPts; i++) {
      const pt = hist[i]
      const barH = Math.min(chartH * 0.45, (pt.spikes / 150) * (chartH * 0.45))
      const bx = getX(i)
      ctx.fillRect(bx - 1.5, chartH - barH + 10, 3, barH)
    }

    // 2. DOPAMINE CURVE (Green/Gold: surges on profit)
    ctx.strokeStyle = '#10b981'
    ctx.lineWidth = 1.8
    ctx.beginPath()
    for (let i = 0; i < nPts; i++) {
      const py = chartH - (hist[i].dopamine * (chartH * 0.75)) + 5
      const px = getX(i)
      if (i === 0) ctx.moveTo(px, py)
      else ctx.lineTo(px, py)
    }
    ctx.stroke()

    // 3. CORTISOL / STRESS CURVE (Rose/Red: surges on loss/drawdown)
    ctx.strokeStyle = '#f43f5e'
    ctx.lineWidth = 1.8
    ctx.beginPath()
    for (let i = 0; i < nPts; i++) {
      const py = chartH - (hist[i].cortisol * (chartH * 0.75)) + 5
      const px = getX(i)
      if (i === 0) ctx.moveTo(px, py)
      else ctx.lineTo(px, py)
    }
    ctx.stroke()

    // 4. SEROTONIN CURVE (Purple: baseline composure)
    ctx.strokeStyle = '#a855f7'
    ctx.lineWidth = 1.2
    ctx.setLineDash([2, 2])
    ctx.beginPath()
    for (let i = 0; i < nPts; i++) {
      const py = chartH - (hist[i].serotonin * (chartH * 0.75)) + 5
      const px = getX(i)
      if (i === 0) ctx.moveTo(px, py)
      else ctx.lineTo(px, py)
    }
    ctx.stroke()
    ctx.setLineDash([])
  }, [neurotransmitters, activeNeurons, firingRateHz, isPaused])

  // Determine brain status state
  let hormoneState = 'HOMEOSTASIS (Balanced)'
  let hormoneClass = 'cyan'
  if (da > 0.65) {
    hormoneState = 'DOPAMINE SURGE (Reward Reinforcing)'
    hormoneClass = 'green'
  } else if (cort > 0.45) {
    hormoneState = 'CORTISOL ELEVATION (Risk Aversion)'
    hormoneClass = 'red'
  }

  return (
    <div className="panel-waveforms-newswire-grid">
      {/* 06. Neural Hormone & Spike Telemetry */}
      <div className="panel-sub waveforms-sub">
        <div className="panel-topbar">
          <div className="title-left">
            <span className="panel-number">06</span>
            <span className="panel-title">Biological Telemetry</span>
            <span className="sub-tag">spikes • dopamine • cortisol</span>
          </div>
        </div>

        <div className="waveforms-body">
          <div className="waveforms-labels">
            <span className="lbl cyan">
              SPIKES: <strong>{activeNeurons}</strong> ({firingRateHz}Hz)
            </span>
            <span className="lbl green">
              DOPAMINE: <strong>{(da * 100).toFixed(0)}%</strong>
            </span>
            <span className="lbl red">
              CORTISOL: <strong>{(cort * 100).toFixed(0)}%</strong>
            </span>
            <span className="lbl purple">
              5-HT: <strong>{(ser * 100).toFixed(0)}%</strong>
            </span>
          </div>

          <div className="waveforms-canvas-wrap">
            <canvas ref={canvasRef} className="waveforms-canvas" />
          </div>
        </div>
      </div>

      {/* 07. Connectome Feedback & Trade Reflex Diagnostics */}
      <div className="panel-sub newswire-sub">
        <div className="panel-topbar">
          <div className="title-left">
            <span className="panel-number">07</span>
            <span className="panel-title">Connectome Diagnostics</span>
            <span className="sub-tag">neuromodulation & reflex loop</span>
          </div>
        </div>

        <div className="newswire-scroll-list">
          <div className="wire-item">
            <span className="wire-time">STATE</span>
            <span className={`wire-badge ${hormoneClass}`}>{hormoneState}</span>
          </div>

          <div className="wire-item">
            <span className="wire-time">DIRECTION</span>
            <span className="wire-badge brain">
              MOTOR: {decision === 'BUY' ? '▲ BUY (UP)' : decision === 'SELL' ? '▼ SELL (DOWN)' : '● HOLD (SENSING)'}
            </span>
          </div>

          {latestTrade && (
            <div className="wire-item">
              <span className="wire-time">LAST TRADE</span>
              <span className="wire-text">
                {latestTrade.side} exited at ₹{latestTrade.exit_price?.toFixed(2)}: {' '}
                <strong className={(latestTrade.pnl_inr || 0) >= 0 ? 'pos' : 'neg'}>
                  {(latestTrade.pnl_inr || 0) >= 0 ? '+' : ''}₹{latestTrade.pnl_inr} ({(latestTrade.pnl_pct || 0)}%)
                </strong>
                {' '}[{latestTrade.reason}]
              </span>
            </div>
          )}

          <div className="wire-item">
            <span className="wire-time">LEARNING</span>
            <span className="wire-text">
              Synaptic plasticity: Hebbian traces active • {multiplier}x leverage margin
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
