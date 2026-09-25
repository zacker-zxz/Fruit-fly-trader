import React from 'react'

/**
 * Trade History and Performance Analytics Page.
 */
export default function TradeHistoryPage({
  trades = [],
  wallet = {},
  equityPoints = [],
}) {
  const sym = wallet.currency_symbol || '₹'

  return (
    <div className="trade-history-page">
      <div className="page-header">
        <h2>Connectome Trade Ledger & Performance</h2>
        <p className="subtitle">
          Comprehensive ledger of high-frequency directional micro-trades executed by the fruit fly brain.
        </p>
      </div>

      {/* Overview Metric Cards */}
      <div className="metrics-row">
        <div className="metric-box">
          <span className="m-label">Total Realized P&L</span>
          <span className={`m-val ${wallet.realized_pnl_inr >= 0 ? 'pos' : 'neg'}`}>
            {wallet.realized_pnl_inr >= 0 ? '+' : ''}{sym} {(wallet.realized_pnl_inr || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
        </div>
        <div className="metric-box">
          <span className="m-label">Win Rate</span>
          <span className="m-val green">{wallet.win_rate_pct != null ? `${wallet.win_rate_pct}%` : '0%'}</span>
        </div>
        <div className="metric-box">
          <span className="m-label">Profit Factor</span>
          <span className="m-val cyan">{wallet.profit_factor || '1.0'}</span>
        </div>
        <div className="metric-box">
          <span className="m-label">Max Drawdown</span>
          <span className="m-val red">{wallet.max_drawdown_pct || '0'}%</span>
        </div>
        <div className="metric-box">
          <span className="m-label">Total Executions</span>
          <span className="m-val">{wallet.total_trades || trades.length}</span>
        </div>
      </div>

      {/* Trade Ledger Table */}
      <div className="ledger-card">
        <div className="ledger-header">
          <h3>Execution History</h3>
          <span className="count-tag">{trades.length} trades recorded</span>
        </div>

        <div className="table-wrapper">
          <table className="trades-table">
            <thead>
              <tr>
                <th>Trade #</th>
                <th>Direction</th>
                <th>Multiplier</th>
                <th>Entry Price</th>
                <th>Exit Price</th>
                <th>Stake ({sym})</th>
                <th>P&L ({sym})</th>
                <th>Return %</th>
                <th>Exit Reason</th>
              </tr>
            </thead>
            <tbody>
              {trades.length > 0 ? (
                trades.map((t, idx) => {
                  const isProfit = (t.pnl_inr ?? 0) >= 0
                  return (
                    <tr key={idx} className={isProfit ? 'row-profit' : 'row-loss'}>
                      <td>#{t.trade_id || t.id || trades.length - idx}</td>
                      <td>
                        <span className={`side-badge ${t.side === 'UP' ? 'up' : 'down'}`}>
                          {t.side === 'UP' ? '▲ UP (CALL)' : '▼ DOWN (PUT)'}
                        </span>
                      </td>
                      <td>
                        <strong className="mult-text">{t.multiplier || 10}x</strong>
                      </td>
                      <td>{t.entry_price?.toFixed(2)}</td>
                      <td>{t.exit_price ? t.exit_price.toFixed(2) : '—'}</td>
                      <td>{sym} {(t.stake_inr || 0).toLocaleString()}</td>
                      <td className={isProfit ? 'pos bold' : 'neg bold'}>
                        {isProfit ? '+' : ''}{sym} {(t.pnl_inr ?? 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td className={isProfit ? 'pos' : 'neg'}>
                        {t.pnl_pct != null ? `${t.pnl_pct >= 0 ? '+' : ''}${t.pnl_pct.toFixed(2)}%` : '—'}
                      </td>
                      <td>
                        <span className="reason-pill">{t.exit_reason || t.reason || 'PROFIT_BOOKED'}</span>
                      </td>
                    </tr>
                  )
                })
              ) : (
                <tr>
                  <td colSpan="9" className="no-trades-cell">
                    No closed micro-trades yet. Launch the simulation to watch the fruit fly execute trades.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
