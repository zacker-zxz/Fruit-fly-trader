import React, { useEffect, useRef, useState } from 'react'

/**
 * High-Precision Minimalist TradingView-Style Candlestick & Volume Chart.
 */
export default function TradingViewChart({
  candles = [],
  trades = [],
  openTrades = [],
  currencySymbol = '₹',
}) {
  const containerRef = useRef(null)
  const canvasRef = useRef(null)

  const [hoverData, setHoverData] = useState(null)
  const [autoFollow, setAutoFollow] = useState(true)
  const [zoomLevel, setZoomLevel] = useState(60)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    let animId

    const render = () => {
      const dpr = window.devicePixelRatio || 1
      const w = canvas.clientWidth || 320
      const h = canvas.clientHeight || 180
      if (canvas.width !== w * dpr) {
        canvas.width = w * dpr
        canvas.height = h * dpr
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

      // Solid dark background - zero white flash
      ctx.fillStyle = '#080a0f'
      ctx.fillRect(0, 0, w, h)

      if (!candles || candles.length === 0) {
        ctx.fillStyle = '#64748b'
        ctx.font = '11px JetBrains Mono, monospace'
        ctx.textAlign = 'center'
        ctx.fillText('Waiting for market data...', w / 2, h / 2)
        return
      }

      const paddingRight = 65
      const paddingBottom = 22
      const chartW = Math.max(50, w - paddingRight)
      const chartH = Math.max(50, h - paddingBottom)
      const mainH = chartH * 0.78
      const volH = chartH * 0.20

      // Visible candles
      const visibleCount = Math.max(15, Math.min(candles.length, zoomLevel))
      const startIdx = Math.max(0, candles.length - visibleCount)
      const visible = candles.slice(startIdx, startIdx + visibleCount)
      if (visible.length === 0) return

      // Price range
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
      const candleW = Math.max(2, slotW * 0.7)

      // 1. Grid lines
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)'
      ctx.lineWidth = 1
      for (let i = 0; i <= 4; i++) {
        const p = minP + (pRange / 4) * i
        const y = getY(p)
        ctx.beginPath()
        ctx.moveTo(0, y)
        ctx.lineTo(chartW, y)
        ctx.stroke()

        // Right axis labels
        ctx.fillStyle = '#475569'
        ctx.font = '9px JetBrains Mono, monospace'
        ctx.textAlign = 'left'
        ctx.fillText(p.toLocaleString(undefined, { maximumFractionDigits: 2 }), chartW + 5, y + 3)
      }

      // 2. Volume Bars
      for (let i = 0; i < visible.length; i++) {
        const c = visible[i]
        const x = i * slotW + slotW / 2
        const vy = getVolY(c.volume)
        const isBull = c.close >= c.open
        ctx.fillStyle = isBull ? 'rgba(16, 185, 129, 0.16)' : 'rgba(239, 68, 68, 0.16)'
        ctx.fillRect(x - candleW / 2, vy, candleW, chartH - vy)
      }

      // 3. Candlesticks (Wicks + Bodies)
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

        // Time labels
        if (i % Math.max(5, Math.floor(visible.length / 4)) === 0) {
          const d = new Date(c.ts * 1000)
          const tStr = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          ctx.fillStyle = '#475569'
          ctx.font = '8px JetBrains Mono, monospace'
          ctx.textAlign = 'center'
          ctx.fillText(tStr, x, chartH + 15)
        }
      }

      // 4. Trade Execution Markers
      const tsMap = new Map()
      visible.forEach((c, i) => tsMap.set(c.ts, i))

      for (const t of trades.slice(0, 20)) {
        const idx = tsMap.get(t.entry_ts)
        if (idx !== undefined) {
          const x = idx * slotW + slotW / 2
          const c = visible[idx]
          if (t.side === 'UP') {
            const y = getY(c.low) + 12
            ctx.fillStyle = '#10b981'
            ctx.beginPath()
            ctx.moveTo(x, y - 6)
            ctx.lineTo(x - 4, y + 3)
            ctx.lineTo(x + 4, y + 3)
            ctx.closePath()
            ctx.fill()
          } else {
            const y = getY(c.high) - 12
            ctx.fillStyle = '#ef4444'
            ctx.beginPath()
            ctx.moveTo(x, y + 6)
            ctx.lineTo(x - 4, y - 3)
            ctx.lineTo(x + 4, y - 3)
            ctx.closePath()
            ctx.fill()
          }
        }
      }

      // 5. Latest Price Line
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

        // Right pill
        ctx.fillStyle = pColor
        ctx.fillRect(chartW + 2, ly - 8, paddingRight - 4, 16)
        ctx.fillStyle = '#000000'
        ctx.font = 'bold 9px JetBrains Mono, monospace'
        ctx.textAlign = 'left'
        ctx.fillText(latest.close.toLocaleString(undefined, { maximumFractionDigits: 2 }), chartW + 4, ly + 3)
      }
    }

    render()
  }, [candles, trades, openTrades, zoomLevel, autoFollow])

  const handleMouseMove = (e) => {
    const canvas = canvasRef.current
    if (!canvas || candles.length === 0) return
    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const chartW = (canvas.clientWidth || 300) - 65
    const count = Math.max(15, Math.min(candles.length, zoomLevel))
    const startIdx = Math.max(0, candles.length - count)
    const slotW = chartW / count
    const idx = Math.floor(x / slotW)
    if (idx >= 0 && idx < count) {
      setHoverData(candles[startIdx + idx])
    }
  }

  const latestCandle = candles[candles.length - 1]
  const displayCandle = hoverData || latestCandle

  return (
    <div className="tradingview-chart-container" ref={containerRef}>
      {/* Top Header HUD Bar */}
      <div className="tv-chart-topbar">
        <div className="tv-ohlcv-hud">
          {displayCandle ? (
            <>
              <span className="hud-metric">
                O: <strong className={displayCandle.close >= displayCandle.open ? 'pos' : 'neg'}>{displayCandle.open?.toFixed(2)}</strong>
              </span>
              <span className="hud-metric">
                H: <strong>{displayCandle.high?.toFixed(2)}</strong>
              </span>
              <span className="hud-metric">
                L: <strong>{displayCandle.low?.toFixed(2)}</strong>
              </span>
              <span className="hud-metric">
                C: <strong className={displayCandle.close >= displayCandle.open ? 'pos' : 'neg'}>{displayCandle.close?.toFixed(2)}</strong>
              </span>
              <span className="hud-metric">
                Vol: <strong>{displayCandle.volume?.toLocaleString()}</strong>
              </span>
            </>
          ) : (
            <span className="hud-idle">Replay streaming...</span>
          )}
        </div>

        {/* Minimalist Dark Actions */}
        <div className="tv-chart-actions">
          <button
            className={`tv-action-btn ${autoFollow ? 'active' : ''}`}
            onClick={() => setAutoFollow(!autoFollow)}
          >
            ● Live Follow
          </button>
          <button
            className="tv-action-btn"
            onClick={() => setZoomLevel((z) => Math.max(20, z - 15))}
          >
            +
          </button>
          <button
            className="tv-action-btn"
            onClick={() => setZoomLevel((z) => Math.min(150, z + 15))}
          >
            -
          </button>
        </div>
      </div>

      {/* Main Canvas */}
      <div className="tv-canvas-wrap">
        <canvas
          ref={canvasRef}
          className="tv-canvas"
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setHoverData(null)}
        />
      </div>
    </div>
  )
}
