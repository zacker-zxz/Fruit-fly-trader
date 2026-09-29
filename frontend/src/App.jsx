import React, { useEffect, useState } from 'react'
import TradingDeskPanel from './components/TradingDeskPanel.jsx'
import NeuralActivityPanel from './components/NeuralActivityPanel.jsx'
import OrderFlowPanel from './components/OrderFlowPanel.jsx'
import OrderBookPanel from './components/OrderBookPanel.jsx'
import PnLChart from './components/PnLChart.jsx'
import WaveformsNewswirePanel from './components/WaveformsNewswirePanel.jsx'
import WalletCard from './components/WalletCard.jsx'
import SettingsPage from './components/SettingsPage.jsx'
import MarketReplayModal from './components/MarketReplayModal.jsx'
import TradeHistoryPage from './components/TradeHistoryPage.jsx'
import MarqueeTicker from './components/MarqueeTicker.jsx'
import { useEventStream } from './useEventStream.js'

export default function App() {
  const [markets, setMarkets] = useState([])
  const [selectedMarketId, setSelectedMarketId] = useState('GOLD_INR_1h.csv')
  const [running, setRunning] = useState(false)
  const [currentSpeed, setCurrentSpeed] = useState(1)
  const [currentMultiplier, setCurrentMultiplier] = useState(10)

  // Modals & Drawers
  const [showMarketModal, setShowMarketModal] = useState(false)
  const [showSettingsModal, setShowSettingsModal] = useState(false)
  const [showWalletDrawer, setShowWalletDrawer] = useState(false)
  const [showHistoryModal, setShowHistoryModal] = useState(false)

  const stream = useEventStream(true)

  // Fetch available market metadata & current simulation status
  useEffect(() => {
    fetch('/api/datasets/info')
      .then((r) => r.json())
      .then((d) => {
        if (d.markets && d.markets.length > 0) {
          setMarkets(d.markets)
          if (!selectedMarketId) {
            setSelectedMarketId(d.markets[0].id)
          }
        }
      })
      .catch(() => {})

    fetch('/api/simulation/status')
      .then((r) => r.json())
      .then((s) => {
        if (s.status === 'running' || s.status === 'paused') {
          setRunning(true)
          if (s.dataset) setSelectedMarketId(s.dataset)
          if (s.speed) setCurrentSpeed(s.speed)
          if (s.multiplier) setCurrentMultiplier(s.multiplier)
        }
      })
      .catch(() => {})
  }, [])

  const handleStopSimulation = async () => {
    setRunning(false)
    stream.resetLocalState()
    await fetch('/api/simulation/stop', { method: 'POST' }).catch(() => {})
  }

  const handleSpeedChange = async (speed) => {
    setCurrentSpeed(speed)
    await fetch('/api/simulation/speed', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ speed }),
    }).catch(() => {})
  }

  const handleMultiplierChange = async (multiplier) => {
    setCurrentMultiplier(multiplier)
    await fetch('/api/simulation/multiplier', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ multiplier }),
    }).catch(() => {})
  }

  const handleTogglePause = async () => {
    const nextPaused = !stream.isPaused
    stream.setPaused(nextPaused)
    try {
      const res = await fetch('/api/simulation/pause', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ paused: nextPaused }),
      })
      const data = await res.json()
      if (data && data.paused !== undefined) {
        stream.setPaused(data.paused)
      }
    } catch (err) {}
  }

  const handleStartSimulation = async (params) => {
    setRunning(true)
    stream.resetLocalState()
    if (params.dataset) setSelectedMarketId(params.dataset)
    if (params.speed) setCurrentSpeed(params.speed)
    if (params.multiplier) setCurrentMultiplier(params.multiplier)

    await fetch('/api/simulation/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dataset: params.dataset || selectedMarketId,
        start_time: params.start_time,
        speed: params.speed || currentSpeed,
        multiplier: params.multiplier || currentMultiplier,
        initial_capital_inr: params.initial_capital_inr || 500000,
        currency: 'INR',
      }),
    }).catch(() => {})
  }

  const handleResetSystem = async () => {
    setRunning(false)
    stream.resetLocalState()
    await fetch('/api/simulation/reset', { method: 'POST' }).catch(() => {})
  }

  const handleManualClose = async () => {
    await fetch('/api/simulation/manual_close', { method: 'POST' }).catch(() => {})
  }

  const currentMarket = markets.find((m) => m.id === selectedMarketId) || {
    symbol: 'GOLD PERP',
    name: 'Gold Perpetual',
    latest_price: 4298.23,
    currency: 'INR',
  }

  const latestCandle = stream.candles[stream.candles.length - 1]
  const latestPrice = latestCandle?.close || currentMarket.latest_price || 4298.23
  const sym = stream.wallet?.currency_symbol || '₹'

  return (
    <div className="terminal-dashboard-root">
      {/* =========================================================================
          TOP COMMAND TICKER BAR
          ========================================================================= */}
      <header className="desk-main-header">
        <div className="header-left-cluster">
          {/* Asset Dropdown Pill */}
          <button
            className="market-selector-pill"
            onClick={() => setShowMarketModal(true)}
            title="Switch Market or Replay Date"
          >
            <span className="coin-icon">🪙</span>
            <span className="market-sym-name">{currentMarket.symbol || 'GOLD PERP'}</span>
            <span className="mult-chip">{currentMultiplier}x</span>
            <span className="down-arrow">▼</span>
          </button>

          {/* Key Ticker & Live INR Wallet Metrics */}
          <div className="topbar-metric-item">
            <span className="tk-label">Mark price</span>
            <span className="tk-value">{sym}{latestPrice.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 2 })}</span>
          </div>

          <div className="topbar-metric-item">
            <span className="tk-label">Wallet Equity</span>
            <span className="tk-value green bold">
              {sym}{(stream.wallet?.equity_inr || 500000).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>

          <div className="topbar-metric-item">
            <span className="tk-label">Cash Balance</span>
            <span className="tk-value bold">
              {sym}{(stream.wallet?.balance_inr || 500000).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>

          <div className="topbar-metric-item">
            <span className="tk-label">Realized PnL</span>
            <span className={`tk-value bold ${(stream.wallet?.realized_pnl_inr || 0) >= 0 ? 'pos' : 'neg'}`}>
              {(stream.wallet?.realized_pnl_inr || 0) >= 0 ? '+' : ''}{sym}
              {(stream.wallet?.realized_pnl_inr || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>

          <div
            className="topbar-metric-item clickable"
            onClick={() => setShowHistoryModal(true)}
            title="Click to view full Trade History & Ledger"
            style={{ cursor: 'pointer' }}
          >
            <span className="tk-label">Trades Closed</span>
            <span className="tk-value cyan">{stream.trades.length} ↗</span>
          </div>

          <div className="topbar-metric-item">
            <span className="tk-label">Status</span>
            <span className={`tk-value ${stream.isPaused ? 'gold' : running ? 'green' : ''}`}>
              {stream.isPaused ? '⏸ PAUSED' : running ? `● LIVE (${currentSpeed}x)` : 'STANDBY'}
            </span>
          </div>
        </div>

        {/* Global Controls: Speed, Play/Pause, Reset, Settings, Wallet */}
        <div className="header-right-cluster">
          {/* Simulation Speed Switcher */}
          <div className="speed-pills-bar">
            {[1, 5, 10, 20].map((s) => (
              <button
                key={s}
                className={`speed-tag ${currentSpeed === s ? 'active' : ''}`}
                onClick={() => handleSpeedChange(s)}
                title={`Run at ${s}x biological speed`}
              >
                {s}x
              </button>
            ))}
          </div>

          {/* Main Simulation Control: START / (PAUSE/RESUME + STOP) */}
          {!running ? (
            <button
              className="action-btn-ctrl start-btn"
              onClick={() => handleStartSimulation({ dataset: selectedMarketId, speed: currentSpeed, multiplier: currentMultiplier })}
              title="Launch Neural Connectome Trading Simulation"
            >
              ▶ START
            </button>
          ) : (
            <>
              <button
                className={`action-btn-ctrl ${stream.isPaused ? 'paused' : ''}`}
                onClick={handleTogglePause}
                title={stream.isPaused ? 'Resume Whole Simulation' : 'Halt / Pause Whole Simulation'}
              >
                {stream.isPaused ? '▶ RESUME' : '⏸ PAUSE'}
              </button>

              <button
                className="action-btn-ctrl stop-btn"
                onClick={handleStopSimulation}
                title="Stop Simulation and Return to Standby"
              >
                ⏹ STOP
              </button>
            </>
          )}

          {/* Reset */}
          <button
            className="action-btn-ctrl reset"
            onClick={handleResetSystem}
            title="Clean Master Reset"
          >
            🔄 RESET
          </button>

          {/* Trade History Ledger Trigger */}
          <button
            className="action-btn-ctrl"
            onClick={() => setShowHistoryModal(true)}
            title="Open Trade Ledger & Performance Analysis"
          >
            📜 LEDGER ({stream.trades.length})
          </button>

          {/* Wallet Drawer Trigger */}
          <button
            className="action-btn-ctrl wallet-btn"
            onClick={() => setShowWalletDrawer(true)}
            title="Open INR Wallet & Leverage Controls"
          >
            💼 {sym} {(stream.wallet?.equity_inr || 500000).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
          </button>

          {/* Settings Trigger */}
          <button
            className="action-btn-ctrl settings-btn"
            onClick={() => setShowSettingsModal(true)}
            title="Open Settings & Diagnostics"
          >
            ⚙️ SETTINGS
          </button>
        </div>
      </header>

      {/* =========================================================================
          MAIN WORKBENCH GRID (2-ROW PROFESSIONAL LAYOUT)
          ========================================================================= */}
      <main className="dashboard-grid-workspace">
        {/* ROW 1: Real Trading Bar Chart (Left) + Real Connectome Brain (Right) */}
        <section className="desk-grid-row top-row">
          <div className="grid-cell cell-trading-desk">
            <TradingDeskPanel
              candles={stream.candles}
              trades={stream.trades}
              openTrades={stream.openTrades}
              wallet={stream.wallet}
              decision={stream.stats.decision || 'HOLD'}
              confidence={stream.stats.confidence || {}}
              latestTrade={stream.trades[0]}
              bioLatencyMs={stream.bioLatencyMs}
              firingRateHz={stream.firingRateHz}
              neurotransmitters={stream.neurotransmitters}
              symbol={currentMarket.symbol || 'GOLD/INR'}
              isPaused={stream.isPaused}
              isRunning={running}
              onManualClose={handleManualClose}
            />
          </div>

          <div className="grid-cell cell-neural-activity">
            <NeuralActivityPanel
              activeNeurons={stream.activeNeurons}
              firedIds={stream.stats.firedIds || []}
              totalSpikes={stream.stats.totalSpikes || 0}
              totalNeurons={stream.stats.totalNeurons || 750}
              bioLatencyMs={stream.bioLatencyMs}
              firingRateHz={stream.firingRateHz}
              isPaused={stream.isPaused}
              decision={stream.stats.decision || 'HOLD'}
            />
          </div>
        </section>

        {/* ROW 2: Order Flow (03) + Order Book (02) + Candlestick Chart (05) + Waveforms/Newswire (06 & 07) */}
        <section className="desk-grid-row bottom-row">
          {/* 03 Order Flow */}
          <div className="grid-cell cell-order-flow">
            <OrderFlowPanel
              candles={stream.candles}
              trades={stream.trades}
              openTrades={stream.openTrades}
              isPaused={stream.isPaused}
            />
          </div>

          {/* 02 Order Book */}
          <div className="grid-cell cell-order-book">
            <OrderBookPanel
              candles={stream.candles}
              openTrades={stream.openTrades}
              currencySymbol={sym}
              isPaused={stream.isPaused}
            />
          </div>

          {/* 05 Single Line Profit / Loss (PnL) & Equity Chart */}
          <div className="grid-cell cell-candlestick-chart">
            <PnLChart
              wallet={stream.wallet}
              trades={stream.trades}
              candles={stream.candles}
              currencySymbol={sym}
              isPaused={stream.isPaused}
            />
          </div>

          {/* 06 & 07 Biological Hormone & Spike Telemetry */}
          <div className="grid-cell cell-waveforms-newswire">
            <WaveformsNewswirePanel
              neurotransmitters={stream.neurotransmitters}
              firingRateHz={stream.firingRateHz}
              activeNeurons={stream.activeNeurons}
              multiplier={currentMultiplier}
              decision={stream.stats.decision}
              latestTrade={stream.trades[0]}
              marketName={currentMarket.name || 'Market Desk'}
              isPaused={stream.isPaused}
            />
          </div>
        </section>
      </main>

      {/* Real Continuous Bottom Marquee Ticker */}
      <MarqueeTicker />

      {/* =========================================================================
          MODALS & DRAWERS (Zero Floating Corner Artifacts)
          ========================================================================= */}

      {/* 1. Market Selection & Replay Date/Timer Modal */}
      {showMarketModal && (
        <div className="modal-backdrop" onClick={() => setShowMarketModal(false)}>
          <div className="modal-inner" onClick={(e) => e.stopPropagation()}>
            <div className="modal-close-bar">
              <button className="modal-close-btn" onClick={() => setShowMarketModal(false)}>✕ Close</button>
            </div>
            <MarketReplayModal
              markets={markets}
              selectedDataset={selectedMarketId}
              onSelectDataset={setSelectedMarketId}
              onStartSimulation={(params) => {
                handleStartSimulation(params)
                setShowMarketModal(false)
              }}
              onClose={() => setShowMarketModal(false)}
              initialSpeed={currentSpeed}
              initialMultiplier={currentMultiplier}
            />
          </div>
        </div>
      )}

      {/* 2. Settings & System Control Modal */}
      {showSettingsModal && (
        <div className="modal-backdrop" onClick={() => setShowSettingsModal(false)}>
          <div className="modal-inner" onClick={(e) => e.stopPropagation()}>
            <div className="modal-close-bar">
              <button className="modal-close-btn" onClick={() => setShowSettingsModal(false)}>✕ Close</button>
            </div>
            <SettingsPage
              settings={{
                currency: stream.wallet?.currency || 'INR',
                initialCapital: stream.wallet?.initial_capital_inr || 500000,
                multiplier: currentMultiplier,
              }}
              onSaveSettings={(cfg) => {
                if (cfg.multiplier) handleMultiplierChange(cfg.multiplier)
                setShowSettingsModal(false)
              }}
              onResetSystem={() => {
                handleResetSystem()
                setShowSettingsModal(false)
              }}
            />
          </div>
        </div>
      )}

      {/* 3. INR Wallet & Fast Multiplier Drawer */}
      {showWalletDrawer && (
        <div className="drawer-backdrop" onClick={() => setShowWalletDrawer(false)}>
          <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <h3>INR Trading Wallet & Leveraged Micro-Trades</h3>
              <button className="modal-close-btn" onClick={() => setShowWalletDrawer(false)}>✕</button>
            </div>
            <WalletCard
              wallet={stream.wallet}
              currentMultiplier={currentMultiplier}
              onMultiplierChange={handleMultiplierChange}
              onManualClose={handleManualClose}
            />
          </div>
        </div>
      )}

      {/* 4. Connectome Trade History & Performance Ledger Modal */}
      {showHistoryModal && (
        <div className="modal-backdrop" onClick={() => setShowHistoryModal(false)}>
          <div className="modal-inner ledger-modal-inner" onClick={(e) => e.stopPropagation()}>
            <div className="modal-close-bar">
              <button className="modal-close-btn" onClick={() => setShowHistoryModal(false)}>✕ Close</button>
            </div>
            <TradeHistoryPage
              trades={stream.trades}
              wallet={stream.wallet}
              equityPoints={stream.equity}
            />
          </div>
        </div>
      )}
    </div>
  )
}
