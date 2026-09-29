import { useEffect, useRef, useState } from 'react'

export function useEventStream(enabled, onResetTrigger) {
  const [state, setState] = useState({
    stats: {},
    candles: [],
    wallet: {
      currency: 'INR',
      currency_symbol: '₹',
      equity_inr: 500000,
      balance_inr: 500000,
      used_margin_inr: 0,
      available_margin_inr: 500000,
      realized_pnl_inr: 0,
      unrealized_pnl_inr: 0,
      total_pnl_inr: 0,
      roi_pct: 0,
      open_trades: [],
      recent_trades: [],
    },
    equity: [],
    trades: [],
    openTrades: [],
    neurotransmitters: { dopamine: 0.5, octopamine: 0.3, serotonin: 0.6 },
    clusters: {},
    bioLatencyMs: 25.5,
    inferenceMs: 1.1,
    firingRateHz: 120,
    activeNeurons: 0,
    prunedNeurons: 0,
    prunedSynapses: 0,
    speed: 5,
    multiplier: 10,
    isPaused: false,
    done: false,
    error: null,
  })

  const buf = useRef([])

  useEffect(() => {
    if (!enabled) return
    const es = new EventSource('/api/events')

    const handler = (type) => (e) => {
      try {
        const data = JSON.parse(e.data)
        buf.current.push({ type, data })
      } catch (err) {}
    }

    es.addEventListener('init_history', handler('init_history'))
    es.addEventListener('tick', handler('tick'))
    es.addEventListener('trade_opened', handler('trade_opened'))
    es.addEventListener('trade_closed', handler('trade_closed'))
    es.addEventListener('speed_changed', handler('speed_changed'))
    es.addEventListener('multiplier_changed', handler('multiplier_changed'))
    es.addEventListener('pause_toggled', handler('pause_toggled'))
    es.addEventListener('reset', handler('reset'))
    es.addEventListener('neuron_pruned', handler('prune'))
    es.addEventListener('synapse_pruned', handler('prune'))
    es.addEventListener('done', handler('done'))
    es.addEventListener('error', handler('error'))

    const flush = () => {
      if (!buf.current.length) return
      const batch = buf.current
      buf.current = []

      setState((prev) => {
        // If paused, only process unpause or reset events
        const hasUnpause = batch.some((b) => (b.type === 'pause_toggled' && b.data.paused === false) || b.type === 'reset')
        if (prev.isPaused && !hasUnpause) {
          return prev
        }

        let s = { ...prev.stats }
        let candles = [...prev.candles]
        let wallet = { ...prev.wallet }
        let equity = [...prev.equity]
        let trades = [...prev.trades]
        let openTrades = [...prev.openTrades]
        let neuro = { ...prev.neurotransmitters }
        let clusters = { ...prev.clusters }
        let bioLatency = prev.bioLatencyMs
        let infMs = prev.inferenceMs
        let firingHz = prev.firingRateHz
        let activeN = prev.activeNeurons
        let prunedN = prev.prunedNeurons || 0
        let prunedS = prev.prunedSynapses || 0
        let spd = prev.speed
        let mult = prev.multiplier
        let paused = prev.isPaused
        let isDone = prev.done

        for (const { type, data } of batch) {
          if (type === 'init_history') {
            if (data.candles && data.candles.length) {
              candles = [...data.candles]
            }
          } else if (type === 'tick') {
            s = {
              tick: data.tick,
              ts: data.ts,
              decision: data.decision,
              confidence: data.confidence,
              price: data.candle?.close,
            }

            if (data.candle) {
              candles.push(data.candle)
              if (candles.length > 500) candles = candles.slice(-500)
            }

            if (data.wallet) {
              wallet = data.wallet
              openTrades = data.wallet.open_trades || []
              equity.push({ t: data.tick, v: data.wallet.equity_inr })
              if (equity.length > 1000) equity = equity.slice(-1000)
            }

            if (data.neurotransmitters) neuro = data.neurotransmitters
            if (data.clusters) clusters = data.clusters
            if (data.bio_latency_ms != null) bioLatency = data.bio_latency_ms
            if (data.inference_ms != null) infMs = data.inference_ms
            if (data.firing_rate_hz != null) firingHz = data.firing_rate_hz
            if (data.active_neurons != null) activeN = data.active_neurons
            if (data.speed != null) spd = data.speed
            s.firedIds = data.fired_ids || []
            s.totalSpikes = data.total_spikes || 0
            s.totalNeurons = data.total_neurons || 750
            s.mushroomBodyActive = data.mushroom_body_active || 0
            s.memoryStrength = data.memory_strength || 0
            s.marketFeatures = data.market_features || {}

          } else if (type === 'trade_opened') {
            if (data.trade) {
              // Append new trade (supports multiple concurrent positions)
              openTrades = [...openTrades.filter((t) => t.trade_id !== data.trade.id && t.id !== data.trade.id), data.trade]
            }
            if (data.wallet) {
              wallet = data.wallet
            }
          } else if (type === 'trade_closed') {
            if (data.trade) {
              trades = [data.trade, ...trades].slice(0, 200)
              openTrades = openTrades.filter((t) => t.trade_id !== data.trade.id && t.id !== data.trade.id)
            }
            if (data.wallet) {
              wallet = data.wallet
              equity.push({ t: data.trade?.exit_tick || equity.length, v: data.wallet.equity_inr })
            }
          } else if (type === 'speed_changed') {
            spd = data.speed
          } else if (type === 'multiplier_changed') {
            mult = data.multiplier
          } else if (type === 'pause_toggled') {
            paused = data.paused
          } else if (type === 'prune') {
            if (data.type === 'neuron_pruned') {
              prunedN += 1
            } else if (data.type === 'synapse_pruned') {
              prunedS += 1
            }
          } else if (type === 'reset') {
            candles = []
            trades = []
            openTrades = []
            equity = []
            prunedN = 0
            prunedS = 0
            wallet = {
              currency: 'INR',
              currency_symbol: '₹',
              equity_inr: 500000,
              balance_inr: 500000,
              used_margin_inr: 0,
              available_margin_inr: 500000,
              realized_pnl_inr: 0,
              unrealized_pnl_inr: 0,
              total_pnl_inr: 0,
              roi_pct: 0,
              open_trades: [],
              recent_trades: [],
            }
            isDone = false
          } else if (type === 'done') {
            isDone = true
          }
        }

        return {
          ...prev,
          stats: s,
          candles,
          wallet,
          equity,
          trades,
          openTrades,
          neurotransmitters: neuro,
          clusters,
          bioLatencyMs: bioLatency,
          inferenceMs: infMs,
          firingRateHz: firingHz,
          activeNeurons: activeN,
          prunedNeurons: prunedN,
          prunedSynapses: prunedS,
          speed: spd,
          multiplier: mult,
          isPaused: paused,
          done: isDone,
        }
      })
    }

    const timer = setInterval(flush, 60)
    return () => {
      es.close()
      clearInterval(timer)
    }
  }, [enabled])

  const resetLocalState = () => {
    setState((prev) => ({
      ...prev,
      candles: [],
      trades: [],
      openTrades: [],
      equity: [],
      wallet: {
        currency: 'INR',
        currency_symbol: '₹',
        equity_inr: 500000,
        balance_inr: 500000,
        used_margin_inr: 0,
        available_margin_inr: 500000,
        realized_pnl_inr: 0,
        unrealized_pnl_inr: 0,
        total_pnl_inr: 0,
        roi_pct: 0,
        open_trades: [],
        recent_trades: [],
      },
      done: false,
    }))
  }

  const setPaused = (val) => {
    setState((prev) => ({ ...prev, isPaused: val }))
  }

  return { ...state, resetLocalState, setPaused }
}
