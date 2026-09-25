import React from 'react'

/**
 * Panel 03: Fruit Fly Trade Execution Blotter.
 * 
 * 100% Real Live Trades executed by the connectome engine.
 * Displays active position in flight and historical executed trades with genuine PnL.
 */
export default function OrderFlowPanel({
  candles = [],
  trades = [],
  openTrades = [],
  currencySymbol = '₹',
}) {
  const sym = currencySymbol || '₹'
  const activeTrade = openTrades[0]
  const latestCandle = candles[candles.length - 1]
  const currentPrice = latestCandle?.close || 0

  return (
    <div className="panel-order-flow">
      {/* Top Header */}
      <div className="panel-topbar">
        <div className="title-left">
          <span className="panel-number">03</span>
          <span className="panel-title">Fly Executed Trades</span>
          <span className="sub-tag">{trades.length} closed • {openTrades.length} active</span>
        </div>
      </div>

      <div className="order-flow-table-wrap">
        {/* 1. Active In-Flight Position Card (if open) */}
        {activeTrade && (
          <div className={`active-position-card ${activeTrade.side === 'UP' ? 'up' : 'down'}`}>
            <div className="card-top-row">
              <span className="status-pulse-badge">● ACTIVE IN FLIGHT</span>
              <span className="card-side-tag">
                {activeTrade.side === 'UP' ? '▲ BUY / UP' : '▼ SELL / DOWN'} ({activeTrade.multiplier}x)
              </span>
              <span className={`card-pnl-val ${(activeTrade.unrealized_pnl_inr || 0) >= 0 ? 'pos' : 'neg'}`}>
                {(activeTrade.unrealized_pnl_inr || 0) >= 0 ? '+' : ''}{sym}
                {(activeTrade.unrealized_pnl_inr || 0).toFixed(2)}
              </span>
            </div>
            <div className="card-detail-grid">
              <div>Entry: <strong>{sym}{activeTrade.entry_price?.toFixed(2)}</strong></div>
              <div>Mark: <strong>{sym}{currentPrice?.toFixed(2)}</strong></div>
              <div>Stake: <strong>{sym}{activeTrade.stake_inr?.toLocaleString()}</strong></div>
              <div>Hold: <strong>Tick #{activeTrade.entry_tick}</strong></div>
            </div>
          </div>
        )}

        {/* 2. Executed Closed Trades Table */}
        <table className="flow-table">
          <thead>
            <tr>
              <th>#</th>
              <th>SIDE</th>
              <th>ENTRY</th>
              <th>EXIT</th>
              <th>HOLD</th>
              <th>PnL (₹)</th>
              <th>REASON</th>
            </tr>
          </thead>
          <tbody>
            {trades.length === 0 && !activeTrade ? (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '24px 8px', color: '#64748b' }}>
                  Fly Brain analyzing momentum & trend... Awaiting first trade signal.
                </td>
              </tr>
            ) : (
              trades.slice(0, 30).map((t, idx) => {
                const isWin = (t.pnl_inr || 0) >= 0
                return (
                  <tr key={`t-${t.id || idx}`} className={idx === 0 ? 'recent-trade-row' : ''}>
                    <td className="time-col">#{t.id || (trades.length - idx)}</td>
                    <td className={t.side === 'UP' ? 'event-col lift' : 'event-col hit'}>
                      {t.side === 'UP' ? '▲ UP' : '▼ DN'} {t.multiplier}x
                    </td>
                    <td className="size-col">{sym}{t.entry_price?.toFixed(1)}</td>
                    <td className="size-col">{sym}{t.exit_price?.toFixed(1)}</td>
                    <td className="time-col">{t.hold_duration || 4}t</td>
                    <td className={isWin ? 'pos bold' : 'neg bold'}>
                      {isWin ? '+' : ''}{sym}{(t.pnl_inr || 0).toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
                    </td>
                    <td className="who-col">
                      <span className={`reason-pill ${isWin ? 'win' : 'loss'}`}>
                        {t.reason || (isWin ? 'PROFIT' : 'LOSS')}
                      </span>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
