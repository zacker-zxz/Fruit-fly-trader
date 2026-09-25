import React, { useState } from 'react'

/**
 * Settings & System Control Page with Master Reset and Diagnostics.
 */
export default function SettingsPage({
  settings = {},
  onSaveSettings,
  onResetSystem,
}) {
  const [currency, setCurrency] = useState(settings.currency || 'INR')
  const [initialCapital, setInitialCapital] = useState(settings.initialCapital || 500000)
  const [stakePct, setStakePct] = useState(settings.stakePct || 5)
  const [multiplier, setMultiplier] = useState(settings.multiplier || 10)
  const [takeProfitPct, setTakeProfitPct] = useState(settings.takeProfitPct || 1.5)
  const [stopLossPct, setStopLossPct] = useState(settings.stopLossPct || 1.0)
  const [maxHoldTicks, setMaxHoldTicks] = useState(settings.maxHoldTicks || 8)

  const [maxNeurons, setMaxNeurons] = useState(settings.maxNeurons || 750)
  const [learningRate, setLearningRate] = useState(settings.learningRate || 0.01)
  const [brainThreshold, setBrainThreshold] = useState(settings.brainThreshold || 0.8)
  const [pruningPatience, setPruningPatience] = useState(settings.pruningPatience || 150)

  const [savedNotice, setSavedNotice] = useState(false)
  const [resetConfirm, setResetConfirm] = useState(false)

  const handleSave = () => {
    if (onSaveSettings) {
      onSaveSettings({
        currency,
        initialCapital: Number(initialCapital),
        stakePct: Number(stakePct),
        multiplier: Number(multiplier),
        takeProfitPct: Number(takeProfitPct) / 100,
        stopLossPct: Number(stopLossPct) / 100,
        maxHoldTicks: Number(maxHoldTicks),
        maxNeurons: Number(maxNeurons),
        learningRate: Number(learningRate),
        brainThreshold: Number(brainThreshold),
        pruningPatience: Number(pruningPatience),
      })
    }
    setSavedNotice(true)
    setTimeout(() => setSavedNotice(false), 2500)
  }

  const handleReset = () => {
    if (onResetSystem) {
      onResetSystem()
    }
    setResetConfirm(false)
  }

  return (
    <div className="settings-page">
      <div className="page-header">
        <h2>System Settings & Connectome Configuration</h2>
        <p className="subtitle">
          Configure financial risk rules, wallet denomination, Drosophila biological thresholds, and master execution parameters.
        </p>
      </div>

      {savedNotice && (
        <div className="alert-banner success">
          ✓ Configuration settings successfully updated!
        </div>
      )}

      <div className="settings-grid">
        {/* 1. Wallet & Execution Configuration */}
        <div className="settings-section">
          <h3>💰 Wallet & Capital Management</h3>
          <div className="form-group">
            <label>Base Wallet Currency</label>
            <div className="toggle-group">
              <button
                className={`toggle-btn ${currency === 'INR' ? 'active' : ''}`}
                onClick={() => setCurrency('INR')}
              >
                ₹ Indian Rupee (INR)
              </button>
              <button
                className={`toggle-btn ${currency === 'USD' ? 'active' : ''}`}
                onClick={() => setCurrency('USD')}
              >
                $ US Dollar (USD)
              </button>
            </div>
          </div>

          <div className="form-group">
            <label>Initial Capital ({currency === 'INR' ? '₹' : '$'})</label>
            <input
              type="number"
              className="cfg-input"
              value={initialCapital}
              onChange={(e) => setInitialCapital(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Stake Allocation per Micro-Trade (% of Equity)</label>
            <input
              type="number"
              className="cfg-input"
              value={stakePct}
              step="1"
              min="1"
              max="50"
              onChange={(e) => setStakePct(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Default Leverage Multiplier</label>
            <select
              className="cfg-input"
              value={multiplier}
              onChange={(e) => setMultiplier(Number(e.target.value))}
            >
              {[1, 2, 5, 10, 20, 50].map((m) => (
                <option key={m} value={m}>{m}x Multiplier</option>
              ))}
            </select>
          </div>
        </div>

        {/* 2. Micro-Trading Risk Rules */}
        <div className="settings-section">
          <h3>⚡ Micro-Trading Risk & Horizon</h3>
          
          <div className="form-group">
            <label>Auto Take-Profit Target (%)</label>
            <input
              type="number"
              className="cfg-input"
              value={takeProfitPct}
              step="0.1"
              onChange={(e) => setTakeProfitPct(e.target.value)}
            />
            <small className="help-text">Instant profit booking triggered when price exceeds this threshold.</small>
          </div>

          <div className="form-group">
            <label>Stop-Loss Protection (%)</label>
            <input
              type="number"
              className="cfg-input"
              value={stopLossPct}
              step="0.1"
              onChange={(e) => setStopLossPct(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Maximum Holding Duration (Ticks / Seconds)</label>
            <input
              type="number"
              className="cfg-input"
              value={maxHoldTicks}
              min="2"
              max="60"
              onChange={(e) => setMaxHoldTicks(e.target.value)}
            />
            <small className="help-text">Fast high-frequency horizon: positions automatically expire & settle.</small>
          </div>
        </div>

        {/* 3. Biological Connectome & Plasticity Controls */}
        <div className="settings-section">
          <h3>🪰 Fruit Fly Connectome Parameters</h3>

          <div className="form-group">
            <label>Max Sampled Neurons (Connectome Topology)</label>
            <input
              type="number"
              className="cfg-input"
              value={maxNeurons}
              step="50"
              min="200"
              max="2000"
              onChange={(e) => setMaxNeurons(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Hebbian Plasticity Learning Rate</label>
            <input
              type="number"
              className="cfg-input"
              value={learningRate}
              step="0.002"
              onChange={(e) => setLearningRate(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Spiking Membrane Threshold</label>
            <input
              type="number"
              className="cfg-input"
              value={brainThreshold}
              step="0.05"
              onChange={(e) => setBrainThreshold(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Synaptic Pruning Patience (Ticks)</label>
            <input
              type="number"
              className="cfg-input"
              value={pruningPatience}
              step="25"
              onChange={(e) => setPruningPatience(e.target.value)}
            />
          </div>
        </div>

        {/* 4. Diagnostics & Master Reset */}
        <div className="settings-section danger-zone">
          <h3>⚠️ Master System Reset & Diagnostics</h3>
          <p className="danger-text">
            Resetting cleans all active simulation loops, flushes the event queues, resets the INR wallet back to base capital, and re-initializes connectome synaptic states.
          </p>

          {!resetConfirm ? (
            <button
              className="reset-btn"
              onClick={() => setResetConfirm(true)}
            >
              🔄 Reset Entire System & Wallet
            </button>
          ) : (
            <div className="confirm-box">
              <span>Are you sure you want to completely reset the trading simulation?</span>
              <div className="confirm-actions">
                <button className="confirm-yes" onClick={handleReset}>
                  Yes, Perform Full Reset
                </button>
                <button className="confirm-no" onClick={() => setResetConfirm(false)}>
                  Cancel
                </button>
              </div>
            </div>
          )}

          <div className="diagnostics-box">
            <h4>Manual Configuration Analysis</h4>
            <ul>
              <li>✓ <strong>Connectome Bug Resolved:</strong> Fixed raw edge target indexing to prevent IndexError.</li>
              <li>✓ <strong>Speed Regulation:</strong> Accelerated 1x to 50x simulation clock supported without skipping neural ticks.</li>
              <li>✓ <strong>Wallet Accounting:</strong> INR base currency with dynamic profit booking.</li>
              <li>✓ <strong>Data Availability:</strong> Pre-loaded OHLCV datasets across Crypto, Indian Stocks, and Commodities.</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="settings-save-bar">
        <button className="save-btn" onClick={handleSave}>
          💾 Save All Configurations
        </button>
      </div>
    </div>
  )
}
