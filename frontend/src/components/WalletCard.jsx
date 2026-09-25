import React from 'react'

/**
 * High-Frequency Trading Wallet in INR (₹) with Multiplier Control and Active Micro-Position Tracker.
 */
export default function WalletCard({
  wallet = {},
  currentMultiplier = 10,
  onMultiplierChange,
  onManualClose,
}) {
  const sym = wallet.currency_symbol || '₹'
  const equity = wallet.equity_inr ?? 500000
  const balance = wallet.balance_inr ?? 500000
  const realizedPnl = wallet.realized_pnl_inr ?? 0
  const unrealizedPnl = wallet.unrealized_pnl_inr ?? 0
  const totalPnl = wallet.total_pnl_inr ?? 0
  const roiPct = wallet.roi_pct ?? 0
  const openTrades = wallet.open_trades || []

  const multipliers = [1, 2, 5, 10, 20, 50]

  return (
    <div className="wallet-card-container">
      {/* 1. Header & Main Balance */}
      <div className="wallet-header">
        <div className="wallet-title">
          <span className="wallet-icon">💼</span>
          <span>INR Trading Wallet</span>
        </div>
        <span className="wallet-currency-badge">{wallet.currency || 'INR'}</span>
      </div>

      <div className="wallet-main-balance">
        <div className="balance-label">Total Equity</div>
        <div className="balance-amount">
          {sym} {equity.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
        <div className={`balance-pnl ${totalPnl >= 0 ? 'pos' : 'neg'}`}>
          {totalPnl >= 0 ? '+' : ''}{sym} {totalPnl.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ({roiPct >= 0 ? '+' : ''}{roiPct.toFixed(2)}%)
        </div>
      </div>

      {/* 2. Margin Breakdown */}
      <div className="wallet-margin-row">
        <div className="margin-col">
          <span className="m-label">Available Cash</span>
          <span className="m-val">{sym} {Math.max(0, wallet.available_margin_inr || balance).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
        </div>
        <div className="margin-col">
          <span className="m-label">Margin In Trade</span>
          <span className="m-val">{sym} {(wallet.used_margin_inr || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
        </div>
      </div>

      {/* 3. Multiplier / Leverage Selector */}
      <div className="wallet-multiplier-section">
        <div className="section-label">
          <span>Connectome Leverage Multiplier</span>
          <strong className="multiplier-badge">{currentMultiplier}x</strong>
        </div>
        <div className="multiplier-pills">
          {multipliers.map((m) => (
            <button
              key={m}
              className={`mult-pill ${currentMultiplier === m ? 'active' : ''}`}
              onClick={() => onMultiplierChange && onMultiplierChange(m)}
            >
              {m}x
            </button>
          ))}
        </div>
      </div>

      {/* 4. Active Micro-Position Card */}
      <div className="wallet-active-positions">
        <div className="positions-title">
          <span>Active Micro-Trade</span>
          <span className="pos-count">{openTrades.length} / 2</span>
        </div>

        {openTrades.length > 0 ? (
          openTrades.map((t) => {
            const isProfit = t.unrealized_pnl_inr >= 0
            return (
              <div key={t.trade_id} className={`active-position-box ${isProfit ? 'pos-glow' : 'neg-glow'}`}>
                <div className="pos-top-row">
                  <div className="pos-side-badge">
                    <span className={`side-tag ${t.side === 'UP' ? 'up' : 'down'}`}>
                      {t.side === 'UP' ? '▲ UP (CALL)' : '▼ DOWN (PUT)'}
                    </span>
                    <span className="pos-mult">{t.multiplier}x</span>
                  </div>
                  <div className={`pos-live-pnl ${isProfit ? 'pos' : 'neg'}`}>
                    {isProfit ? '+' : ''}{sym} {t.unrealized_pnl_inr?.toFixed(2)} ({t.pnl_pct >= 0 ? '+' : ''}{t.pnl_pct?.toFixed(1)}%)
                  </div>
                </div>

                <div className="pos-details-grid">
                  <div>
                    <span className="k">Entry</span>
                    <span className="v">{t.entry_price?.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="k">Current</span>
                    <span className="v">{t.current_price?.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="k">Stake</span>
                    <span className="v">{sym} {t.stake_inr?.toLocaleString()}</span>
                  </div>
                </div>

                <div className="pos-actions-row">
                  <div className="pos-timer-bar">
                    <div className="timer-pulse" />
                    <span>Micro-holding: {t.max_hold_ticks}s Horizon</span>
                  </div>
                  <button
                    className="book-profit-btn"
                    onClick={() => onManualClose && onManualClose(t.trade_id)}
                  >
                    ⚡ Book Now
                  </button>
                </div>
              </div>
            )
          })
        ) : (
          <div className="no-positions-box">
            <span>Drosophila connectome scanning price signals...</span>
          </div>
        )}
      </div>

      {/* 5. Key Trading Statistics */}
      <div className="wallet-stats-footer">
        <div className="foot-stat">
          <span className="fk">Win Rate</span>
          <span className="fv green">{wallet.win_rate_pct != null ? `${wallet.win_rate_pct}%` : '—'}</span>
        </div>
        <div className="foot-stat">
          <span className="fk">Total Trades</span>
          <span className="fv">{wallet.total_trades || 0}</span>
        </div>
        <div className="foot-stat">
          <span className="fk">Max DD</span>
          <span className="fv red">{wallet.max_drawdown_pct != null ? `${wallet.max_drawdown_pct}%` : '0%'}</span>
        </div>
      </div>
    </div>
  )
}
