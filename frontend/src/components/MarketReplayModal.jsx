import React, { useState, useEffect } from 'react'

/**
 * Market Selection & Replay Date/Timer Configuration Modal / Page.
 */
export default function MarketReplayModal({
  markets = [],
  selectedDataset = '',
  onSelectDataset,
  onStartSimulation,
  onClose,
  initialSpeed = 5,
  initialMultiplier = 10,
}) {
  const [selectedMarketId, setSelectedMarketId] = useState(selectedDataset || '')
  const [assetFilter, setAssetFilter] = useState('all')
  const [startDate, setStartDate] = useState('2024-06-01')
  const [startTime, setStartTime] = useState('09:30')
  const [speed, setSpeed] = useState(initialSpeed)
  const [multiplier, setMultiplier] = useState(initialMultiplier)
  const [capitalInr, setCapitalInr] = useState(500000)

  useEffect(() => {
    if (!selectedMarketId && markets.length > 0) {
      setSelectedMarketId(markets[0].id)
    }
  }, [markets])

  const selectedMarket = markets.find((m) => m.id === selectedMarketId) || markets[0]

  const filteredMarkets = markets.filter((m) => {
    if (assetFilter === 'all') return true
    return m.asset_class === assetFilter
  })

  const handleLaunch = () => {
    // Convert chosen date and time to unix timestamp
    let startTimestamp = null
    try {
      const dt = new Date(`${startDate}T${startTime}:00Z`)
      if (!isNaN(dt.getTime())) {
        startTimestamp = dt.getTime() / 1000
      }
    } catch (e) {}

    onStartSimulation({
      dataset: selectedMarketId || markets[0]?.id,
      start_time: startTimestamp,
      speed: Number(speed),
      multiplier: Number(multiplier),
      initial_capital_inr: Number(capitalInr),
    })
    if (onClose) onClose()
  }

  return (
    <div className="market-replay-page">
      <div className="replay-page-header">
        <div>
          <h2>Market Hub & Replay Selector</h2>
          <p className="subtitle">
            Select market instruments, specify exact replay date & time, set biological simulation speed, and deploy the fruit fly connectome.
          </p>
        </div>
      </div>

      <div className="replay-layout">
        {/* Left Column: Market Catalog */}
        <div className="markets-column">
          <div className="asset-filter-bar">
            {['all', 'crypto', 'indian_equity', 'commodity', 'forex'].map((f) => (
              <button
                key={f}
                className={`filter-btn ${assetFilter === f ? 'active' : ''}`}
                onClick={() => setAssetFilter(f)}
              >
                {f === 'all' ? 'All Markets' : f.replace('_', ' ').toUpperCase()}
              </button>
            ))}
          </div>

          <div className="market-cards-list">
            {filteredMarkets.map((m) => {
              const isSelected = m.id === selectedMarketId
              return (
                <div
                  key={m.id}
                  className={`market-card ${isSelected ? 'selected' : ''}`}
                  onClick={() => setSelectedMarketId(m.id)}
                >
                  <div className="m-card-top">
                    <span className="m-symbol">{m.symbol}</span>
                    <span className="m-badge timeframe">{m.timeframe}</span>
                    <span className={`m-badge asset ${m.asset_class}`}>{m.asset_class.replace('_', ' ')}</span>
                  </div>
                  <div className="m-card-name">{m.name}</div>
                  <div className="m-card-dates">
                    <span>Available: {m.start_dt?.slice(0, 10)} to {m.end_dt?.slice(0, 10)}</span>
                    <span className="m-candles">{m.candle_count} candles</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Right Column: Replay & Execution Setup */}
        <div className="config-column">
          <div className="config-card">
            <h3>Simulation & Replay Parameters</h3>

            {/* Selected Summary */}
            {selectedMarket && (
              <div className="selected-summary-box">
                <div className="sum-title">Selected Instrument</div>
                <div className="sum-val">{selectedMarket.name} ({selectedMarket.symbol})</div>
                <div className="sum-meta">
                  Currency: <strong>{selectedMarket.currency}</strong> · Timeframe: <strong>{selectedMarket.timeframe}</strong>
                </div>
              </div>
            )}

            {/* Date & Time Picker */}
            <div className="form-group">
              <label>Replay Start Date & Time</label>
              <div className="datetime-row">
                <input
                  type="date"
                  className="cfg-input"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
                <input
                  type="time"
                  className="cfg-input"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                />
              </div>
              <small className="help-text">Choose the historical point where the fruit fly starts trading.</small>
            </div>

            {/* Speed Multiplier */}
            <div className="form-group">
              <label>Simulation Playback Speed</label>
              <div className="speed-pills">
                {[1, 2, 5, 10, 20, 50].map((s) => (
                  <button
                    key={s}
                    className={`speed-pill ${speed === s ? 'active' : ''}`}
                    onClick={() => setSpeed(s)}
                  >
                    {s}x {s === 1 ? '(Real)' : ''}
                  </button>
                ))}
              </div>
              <small className="help-text">5x / 10x accelerates historical replay while preserving biological synaptic updates.</small>
            </div>

            {/* Leverage Multiplier */}
            <div className="form-group">
              <label>Micro-Trading Leverage Multiplier</label>
              <div className="multiplier-pills">
                {[1, 2, 5, 10, 20, 50].map((m) => (
                  <button
                    key={m}
                    className={`mult-pill ${multiplier === m ? 'active' : ''}`}
                    onClick={() => setMultiplier(m)}
                  >
                    {m}x
                  </button>
                ))}
              </div>
            </div>

            {/* Initial Capital in INR */}
            <div className="form-group">
              <label>Starting Wallet Capital (₹ INR)</label>
              <input
                type="number"
                className="cfg-input"
                value={capitalInr}
                step="50000"
                onChange={(e) => setCapitalInr(e.target.value)}
              />
            </div>

            {/* Launch Button */}
            <button className="launch-simulation-btn" onClick={handleLaunch}>
              🚀 Launch Connectome Replay
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
