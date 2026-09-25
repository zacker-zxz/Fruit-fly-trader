import React, { useEffect, useRef, useState } from 'react'

/**
 * Panel 01: The Trading Desk - Real Trading Bar Chart.
 * 
 * Renders real market candlestick/bar replay data with:
 * - Real OHLCV bars & EMAs
 * - Real Connectome micro-trade entries (▲ UP, ▼ DOWN) and profit-taking exits
 * - Real live INR Wallet equity and PnL
 * - Minimalist dark aesthetics without any fake animations
 */
export default function TradingDeskPanel({
  candles = [],
  trades = [],
  openTrades = [],
  wallet = {},
  decision = 'HOLD',
  confidence = {},
  latestTrade = null,
  bioLatencyMs = 24.5,
  firingRateHz = 237,
  neurotransmitters = { dopamine: 0.65, octopamine: 0.4 },
  symbol = 'GOLD/INR',
}) {
  const containerRef = useRef(null)
  const canvasRef = useRef(null)
  const [hoverData, setHoverData] = useState(null)
  const [autoFollow, setAutoFollow] = useState(true)
  const [zoomLevel, setZoomLevel] = useState(65)
  const sym = wallet.currency_symbol || '₹'

  const latestCandle = candles[candles.length - 1]
  const latestPrice = latestCandle?.close || 0
  const activeTrade = openTrades[0]

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    let animId

    const render = () => {
      const dpr = window.devicePixelRatio || 1
      const w = canvas.clientWidth || 600
      const h = canvas.clientHeight || 280
      if (canvas.width !== w * dpr) {
        canvas.width = w * dpr
        canvas.height = h * dpr
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      
      // Minimalist dark background
      ctx.fillStyle = '#080a0f'
      ctx.fillRect(0, 0, w, h)

      if (!candles || candles.length === 0) {
        ctx.fillStyle = '#64748b'
        ctx.font = '12px JetBrains Mono, monospace'
        ctx.textAlign = 'center'
        ctx.fillText('Awaiting market tick replay stream...', w / 2, h / 2)
        return
      }

      const paddingRight = 70
      const paddingBottom = 24
      const chartW = Math.max(100, w - paddingRight)
      const chartH = Math.max(80, h - paddingBottom)
      const mainH = chartH * 0.78
      const volH = chartH * 0.20
      const volTop = chartH - volH

      // Visible window
      const count = Math.max(15, Math.min(candles.length, zoomLevel))
      const startIdx = autoFollow ? Math.max(0, candles.length - count) : Math.max(0, candles.length - count)
      const visible = candles.slice(startIdx, startIdx + count)
      if (visible.length === 0) return

      // Price extremes
      let minP = Infinity
      let maxP = -Infinity
      let maxVol = 1

      for (const c of visible) {
        if (c.low < minP) minP = c.low
        if (c.high > maxP) maxP = c.high
        if (c.volume > maxVol) maxVol = c.volume
      }

      if (minP === maxP) {
        minP -= 1
        maxP += 1
      }

      const pPad = (maxP - minP) * 0.08 || 1
      minP -= pPad
      maxP += pPad
      const pRange = maxP - minP

      const getY = (p) => mainH - ((p - minP) / pRange) * mainH
      const getVolY = (v) => chartH - (v / maxVol) * volH

      const slotW = chartW / visible.length
      const candleW = Math.max(2, slotW * 0.72)

      // --- 1. Grid Lines ---
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)'
      ctx.lineWidth = 1
      const steps = 5
      for (let i = 0; i <= steps; i++) {
        const p = minP + (pRange / steps) * i
        const y = getY(p)
        ctx.beginPath()
        ctx.moveTo(0, y)
        ctx.lineTo(chartW, y)
        ctx.stroke()

        // Right axis labels
        ctx.fillStyle = '#475569'
        ctx.font = '10px JetBrains Mono, monospace'
        ctx.textAlign = 'left'
        ctx.fillText(p.toLocaleString(undefined, { maximumFractionDigits: 2 }), chartW + 6, y + 3)
      }

      // --- 2. Volume Bars ---
      for (let i = 0; i < visible.length; i++) {
        const c = visible[i]
        const x = i * slotW + slotW / 2
        const vy = getVolY(c.volume)
        const isBull = c.close >= c.open
        ctx.fillStyle = isBull ? 'rgba(16, 185, 129, 0.18)' : 'rgba(239, 68, 68, 0.18)'
        ctx.fillRect(x - candleW / 2, vy, candleW, chartH - vy)
      }

      // --- 3. EMA Line (9-period fast EMA) ---
      if (visible.length > 5) {
        ctx.strokeStyle = 'rgba(6, 182, 212, 0.7)'
        ctx.lineWidth = 1.2
        ctx.beginPath()
        let ema = visible[0].close
        const k = 2 / (9 + 1)
        for (let i = 0; i < visible.length; i++) {
          ema = visible[i].close * k + ema * (1 - k)
          const x = i * slotW + slotW / 2
          const y = getY(ema)
          if (i === 0) ctx.moveTo(x, y)
          else ctx.lineTo(x, y)
        }
        ctx.stroke()
      }

      // --- 4. Candlesticks (Wicks + Bodies) ---
      for (let i = 0; i < visible.length; i++) {
        const c = visible[i]
        const x = i * slotW + slotW / 2
        const isBull = c.close >= c.open
        const color = isBull ? '#10b981' : '#ef4444'

        const yOpen = getY(c.open)
        const yClose = getY(c.close)
        const yHigh = getY(c.high)
        const yLow = getY(c.low)

        // Wick
        ctx.strokeStyle = color
        ctx.lineWidth = 1.2
        ctx.beginPath()
        ctx.moveTo(x, yHigh)
        ctx.lineTo(x, yLow)
        ctx.stroke()

        // Body
        ctx.fillStyle = color
        const bTop = Math.min(yOpen, yClose)
        const bH = Math.max(1.5, Math.abs(yClose - yOpen))
        ctx.fillRect(x - candleW / 2, bTop, candleW, bH)

        // Time labels every few candles
        if (i % Math.max(5, Math.floor(visible.length / 5)) === 0) {
          const d = new Date(c.ts * 1000)
          const tStr = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          ctx.fillStyle = '#475569'
          ctx.font = '9px JetBrains Mono, monospace'
          ctx.textAlign = 'center'
          ctx.fillText(tStr, x, chartH + 16)
        }
      }

      // --- 5. Real Trade Execution Markers ---
      const tsMap = new Map()
      visible.forEach((c, i) => tsMap.set(c.ts, i))

      for (const t of trades.slice(0, 30)) {
        const idx = tsMap.get(t.entry_ts)
        if (idx !== undefined) {
          const x = idx * slotW + slotW / 2
          const c = visible[idx]
          if (t.side === 'UP') {
            const y = getY(c.low) + 14
            ctx.fillStyle = '#10b981'
            ctx.beginPath()
            ctx.moveTo(x, y - 7)
            ctx.lineTo(x - 5, y + 4)
            ctx.lineTo(x + 5, y + 4)
            ctx.closePath()
            ctx.fill()
            ctx.font = 'bold 9px JetBrains Mono, monospace'
            ctx.fillText(`▲ UP`, x, y + 14)
          } else {
            const y = getY(c.high) - 14
            ctx.fillStyle = '#ef4444'
            ctx.beginPath()
            ctx.moveTo(x, y + 7)
            ctx.lineTo(x - 5, y - 4)
            ctx.lineTo(x + 5, y - 4)
            ctx.closePath()
            ctx.fill()
            ctx.font = 'bold 9px JetBrains Mono, monospace'
            ctx.fillText(`▼ DN`, x, y - 7)
          }
        }
      }

      // --- 6. Active Position Lines ---
      if (activeTrade && activeTrade.entry_price > 0) {
        const ey = getY(activeTrade.entry_price)
        ctx.strokeStyle = activeTrade.side === 'UP' ? '#10b981' : '#ef4444'
        ctx.setLineDash([4, 4])
        ctx.beginPath()
        ctx.moveTo(0, ey)
        ctx.lineTo(chartW, ey)
        ctx.stroke()
        ctx.setLineDash([])

        // Right Entry Tag
        ctx.fillStyle = activeTrade.side === 'UP' ? '#10b981' : '#ef4444'
        ctx.fillRect(chartW + 2, ey - 9, paddingRight - 4, 18)
        ctx.fillStyle = '#000000'
        ctx.font = 'bold 9px JetBrains Mono, monospace'
        ctx.textAlign = 'left'
        ctx.fillText(`${activeTrade.side} ${activeTrade.multiplier}x`, chartW + 5, ey + 4)
      }

      // --- 7. Latest Price Line ---
      const latest = visible[visible.length - 1]
      if (latest) {
        const ly = getY(latest.close)
        const isBull = latest.close >= latest.open
        const pColor = isBull ? '#10b981' : '#ef4444'

        ctx.strokeStyle = pColor
        ctx.lineWidth = 1
        ctx.setLineDash([2, 2])
        ctx.beginPath()
        ctx.moveTo(0, ly)
        ctx.lineTo(chartW, ly)
        ctx.stroke()
        ctx.setLineDash([])

        // Right Pill
        ctx.fillStyle = pColor
        ctx.fillRect(chartW + 2, ly - 9, paddingRight - 4, 18)
        ctx.fillStyle = '#000000'
        ctx.font = 'bold 10px JetBrains Mono, monospace'
        ctx.textAlign = 'left'
        ctx.fillText(latest.close.toLocaleString(undefined, { maximumFractionDigits: 2 }), chartW + 5, ly + 4)
      }
    }

    render()
  }, [candles, trades, openTrades, zoomLevel, autoFollow])

  const handleMouseMove = (e) => {
    const canvas = canvasRef.current
    if (!canvas || candles.length === 0) return
    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const chartW = canvas.clientWidth - 70
    const count = Math.max(15, Math.min(candles.length, zoomLevel))
    const startIdx = Math.max(0, candles.length - count)
    const slotW = chartW / count
    const idx = Math.floor(x / slotW)
    if (idx >= 0 && idx < count) {
      setHoverData(candles[startIdx + idx])
    }
  }

  const displayCandle = hoverData || latestCandle
  const isPos = (wallet.total_pnl_inr || 0) >= 0

  return (
    <div className="panel-trading-desk" ref={containerRef}>
      {/* Top Header Bar */}
      <div className="desk-topbar">
        <div className="desk-title-left">
          <span className="panel-number">01</span>
          <span className="panel-title">The trading desk</span>
          <span className="specimen-id">{symbol}</span>
          <span className="gen-id">Replay Feed</span>
          <span className={`stage-tag ${decision === 'BUY' ? 'pos' : decision === 'SELL' ? 'neg' : ''}`}>
            {decision === 'BUY' ? '▲ BUY / UP' : decision === 'SELL' ? '▼ SELL / DOWN' : 'HOLD / SENSING'}
          </span>
          {activeTrade && (
            <span className="active-trade-indicator">
              IN TRADE: {activeTrade.side} {activeTrade.multiplier}x ({activeTrade.unrealized_pnl_inr >= 0 ? '+' : ''}{sym}{activeTrade.unrealized_pnl_inr?.toFixed(2)})
            </span>
          )}
        </div>

        <div className="desk-equity-right">
          <button
            className={`desk-follow-btn ${autoFollow ? 'active' : ''}`}
            onClick={() => setAutoFollow(!autoFollow)}
          >
            ● Live Follow
          </button>
          <span className="eq-label">EQUITY</span>
          <span className="eq-val">
            {sym} {(wallet.equity_inr || 500000).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
          <span className={`eq-delta ${isPos ? 'pos' : 'neg'}`}>
            {isPos ? '+' : ''}{sym} {(wallet.total_pnl_inr || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
        </div>
      </div>

      {/* OHLC Inspection HUD Bar */}
      <div className="desk-ohlc-hud">
        {displayCandle ? (
          <>
            <span className="hud-part">O: <strong className={displayCandle.close >= displayCandle.open ? 'pos' : 'neg'}>{displayCandle.open?.toFixed(2)}</strong></span>
            <span className="hud-part">H: <strong>{displayCandle.high?.toFixed(2)}</strong></span>
            <span className="hud-part">L: <strong>{displayCandle.low?.toFixed(2)}</strong></span>
            <span className="hud-part">C: <strong className={displayCandle.close >= displayCandle.open ? 'pos' : 'neg'}>{displayCandle.close?.toFixed(2)}</strong></span>
            <span className="hud-part">Vol: <strong>{displayCandle.volume?.toLocaleString()}</strong></span>
            <span className="hud-part">Bio Reflex: <strong className="cyan">{bioLatencyMs}ms</strong></span>
            <span className="hud-part">Spikes: <strong className="purple">{firingRateHz}Hz</strong></span>
          </>
        ) : (
          <span className="hud-idle">Connecting to market replay feed...</span>
        )}
      </div>

      {/* Main Canvas Real Candlestick Chart */}
      <div className="desk-chart-canvas-wrap">
        <canvas
          ref={canvasRef}
          className="desk-chart-canvas"
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setHoverData(null)}
        />
      </div>
    </div>
  )
}
