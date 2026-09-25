import React, { useEffect, useRef, useState } from 'react'

/**
 * Panel 05: Cumulative Profit / Loss (PnL) & Equity Single Line Chart.
 * 
 * Replaces duplicate candlestick chart with a clean, high-precision single-line
 * performance curve showing real cumulative INR profit/loss across executed trades.
 */
export default function PnLChart({
  wallet = {},
  trades = [],
  candles = [],
  currencySymbol = '₹',
  isPaused = false,
}) {
  const canvasRef = useRef(null)
  const [hoverData, setHoverData] = useState(null)
  const [autoFollow, setAutoFollow] = useState(true)

  const sym = currencySymbol || '₹'
  const initialCap = wallet.initial_capital_inr || 500000
  const currentEquity = wallet.equity_inr || initialCap
  const currentPnl = wallet.total_pnl_inr || (currentEquity - initialCap)
  const roiPct = wallet.roi_pct || ((currentPnl / initialCap) * 100)
  const isPos = currentPnl >= 0

  // Build cumulative PnL time series points from real trades & ticks
  const pnlPoints = React.useMemo(() => {
    // Start at tick 0 with 0 PnL
    const points = [{ tick: 0, pnl: 0, equity: initialCap, tradeId: null }]
    let runningPnl = 0

    // Chronological executed trades
    const sortedTrades = [...trades].sort((a, b) => (a.exit_ts || a.id) - (b.exit_ts || b.id))
    for (let i = 0; i < sortedTrades.length; i++) {
      const t = sortedTrades[i]
      runningPnl += (t.pnl_inr || 0)
      points.push({
        tick: t.exit_tick || (i + 1),
        pnl: runningPnl,
        equity: initialCap + runningPnl,
        tradeId: t.id,
        side: t.side,
        exitPrice: t.exit_price,
        singlePnl: t.pnl_inr,
      })
    }

    // Add current live tick if active
    if (points.length === 1 && candles.length > 0) {
      points.push({ tick: candles.length, pnl: currentPnl, equity: currentEquity, tradeId: null })
    }

    return points
  }, [trades, candles.length, currentPnl, currentEquity, initialCap])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    const render = () => {
      const dpr = window.devicePixelRatio || 1
      const w = canvas.clientWidth || 320
      const h = canvas.clientHeight || 180
      if (canvas.width !== w * dpr) {
        canvas.width = w * dpr
        canvas.height = h * dpr
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

      // Solid minimalist dark background
      ctx.fillStyle = '#080a0f'
      ctx.fillRect(0, 0, w, h)

      const paddingLeft = 14
      const paddingRight = 65
      const paddingTop = 20
      const paddingBottom = 22
      const chartW = Math.max(50, w - paddingLeft - paddingRight)
      const chartH = Math.max(40, h - paddingTop - paddingBottom)

      if (pnlPoints.length === 0) {
        ctx.fillStyle = '#64748b'
        ctx.font = '10px JetBrains Mono, monospace'
        ctx.textAlign = 'center'
        ctx.fillText('Awaiting trade execution...', w / 2, h / 2)
        return
      }

      // Visible points window
      const maxPts = 60
      const visible = autoFollow ? pnlPoints.slice(-maxPts) : pnlPoints.slice(-maxPts)
      if (visible.length === 0) return

      // PnL range
      let minPnl = 0
      let maxPnl = 0
      for (const pt of visible) {
        if (pt.pnl < minPnl) minPnl = pt.pnl
        if (pt.pnl > maxPnl) maxPnl = pt.pnl
      }

      // Add comfortable headroom
      const pad = Math.max(500, (maxPnl - minPnl) * 0.15)
      minPnl -= pad
      maxPnl += pad
      const pnlRange = Math.max(1, maxPnl - minPnl)

      const getY = (val) => paddingTop + chartH - ((val - minPnl) / pnlRange) * chartH
      const getX = (idx) => paddingLeft + (idx / Math.max(1, visible.length - 1)) * chartW

      // 1. Zero Baseline Line (₹0 PnL)
      const zeroY = getY(0)
      if (zeroY >= paddingTop && zeroY <= paddingTop + chartH) {
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)'
        ctx.lineWidth = 1
        ctx.setLineDash([3, 3])
        ctx.beginPath()
        ctx.moveTo(paddingLeft, zeroY)
        ctx.lineTo(paddingLeft + chartW, zeroY)
        ctx.stroke()
        ctx.setLineDash([])

        ctx.fillStyle = '#64748b'
        ctx.font = '8.5px JetBrains Mono, monospace'
        ctx.textAlign = 'left'
        ctx.fillText('₹0.00', paddingLeft + chartW + 5, zeroY + 3)
      }

      // 2. Gradient Fill Under Line
      const lineColor = isPos ? '#10b981' : '#ef4444'
      const grad = ctx.createLinearGradient(0, paddingTop, 0, paddingTop + chartH)
      if (isPos) {
        grad.addColorStop(0, 'rgba(16, 185, 129, 0.22)')
        grad.addColorStop(1, 'rgba(16, 185, 129, 0.0)')
      } else {
        grad.addColorStop(0, 'rgba(239, 68, 68, 0.22)')
        grad.addColorStop(1, 'rgba(239, 68, 68, 0.0)')
      }

      ctx.beginPath()
      ctx.moveTo(getX(0), zeroY)
      for (let i = 0; i < visible.length; i++) {
        ctx.lineTo(getX(i), getY(visible[i].pnl))
      }
      ctx.lineTo(getX(visible.length - 1), zeroY)
      ctx.closePath()
      ctx.fillStyle = grad
      ctx.fill()

      // 3. Single Profit/Loss Line
      ctx.strokeStyle = lineColor
      ctx.lineWidth = 2.0
      ctx.beginPath()
      for (let i = 0; i < visible.length; i++) {
        const px = getX(i)
        const py = getY(visible[i].pnl)
        if (i === 0) ctx.moveTo(px, py)
        else ctx.lineTo(px, py)
      }
      ctx.stroke()

      // 4. Trade Execution Dots along the line
      for (let i = 0; i < visible.length; i++) {
        const pt = visible[i]
        if (pt.tradeId != null) {
          const px = getX(i)
          const py = getY(pt.pnl)
          const ptWin = (pt.singlePnl || 0) >= 0

          ctx.beginPath()
          ctx.arc(px, py, 3.5, 0, Math.PI * 2)
          ctx.fillStyle = ptWin ? '#10b981' : '#ef4444'
          ctx.fill()
          ctx.strokeStyle = '#ffffff'
          ctx.lineWidth = 1
          ctx.stroke()
        }
      }

      // 5. Current Latest PnL Tag & Pulsing End Node
      const lastPt = visible[visible.length - 1]
      if (lastPt) {
        const lx = getX(visible.length - 1)
        const ly = getY(lastPt.pnl)

        // Pulsing end circle
        ctx.beginPath()
        ctx.arc(lx, ly, 4.5, 0, Math.PI * 2)
        ctx.fillStyle = lineColor
        ctx.shadowColor = lineColor
        ctx.shadowBlur = 8
        ctx.fill()
        ctx.shadowBlur = 0

        // Right side value badge
        ctx.fillStyle = isPos ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)'
        ctx.strokeStyle = lineColor
        ctx.lineWidth = 1
        ctx.fillRect(paddingLeft + chartW + 3, ly - 9, paddingRight - 6, 18)
        ctx.strokeRect(paddingLeft + chartW + 3, ly - 9, paddingRight - 6, 18)

        ctx.fillStyle = lineColor
        ctx.font = 'bold 9px JetBrains Mono, monospace'
        ctx.textAlign = 'left'
        const sign = lastPt.pnl >= 0 ? '+' : ''
        ctx.fillText(`${sign}${Math.round(lastPt.pnl)}`, paddingLeft + chartW + 6, ly + 4)
      }
    }

    render()
  }, [pnlPoints, currentPnl, isPos, autoFollow, isPaused])

  return (
    <div className="panel-chart-wrapper">
      {/* Top Header Bar */}
      <div className="panel-topbar chart-subtopbar">
        <div className="title-left">
          <span className="panel-number">05</span>
          <span className="panel-title">Cumulative profit / loss</span>
          <span className="sub-tag">fly performance curve</span>
        </div>
        <div className="chart-price-display">
          <span className={`chart-px ${isPos ? 'pos' : 'neg'}`}>
            {isPos ? '+' : ''}{sym} {currentPnl.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
          <span className={`mult-chip ${isPos ? 'green' : 'red'}`} style={{ marginLeft: 6, fontSize: '9px' }}>
            {isPos ? '▲' : '▼'} {roiPct.toFixed(2)}% ROI
          </span>
        </div>
      </div>

      {/* Canvas */}
      <div className="tv-canvas-wrap">
        <canvas ref={canvasRef} className="tv-canvas" />
      </div>
    </div>
  )
}
