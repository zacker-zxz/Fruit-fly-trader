"""Interactive simulation runner with biological Drosophila timing and micro-trading.

Supports:
- Speed multipliers: 1x, 2x, 5x, 10x, 20x, MAX.
- Dynamic pause, resume, stop, and parameter adjustments on the fly.
- INR wallet and fast micro-trading with multiplier leverage.
- Genuine Drosophila neural decision-making with:
  * Biological noise (no two runs are identical)
  * Mushroom Body associative memory (trade outcomes shape future decisions)
  * Rich market feature analysis (patterns, RSI, breakouts, reversals)
  * Neuromodulator-driven risk management (cortisol, dopamine, serotonin)
  * Multiple concurrent trades with stochastic hold durations
"""

import asyncio
import json
import os
import random
import time
from dataclasses import dataclass
from typing import Callable

from engine.activity import Brain
from engine.connectome import from_file
from engine.neuromodulation import compute_reward
from engine.neuron import reseed_neural_rng
from engine.plasticity import PlasticityEngine
from engine.pruning import PruningEngine
from market.data_loader import file_hash
from market.dataset_manager import load_candles_with_offset
from market.features import features
from trading.micro_trading import MicroTradingEngine


class SimulationRunner:
    def __init__(
        self,
        config: dict,
        dataset_name: str,
        start_time: float | None = None,
        on_event: Callable[[dict], None] | None = None,
    ):
        self.cfg = config
        self.dataset_name = dataset_name
        self.start_time = start_time
        self.on_event = on_event or (lambda e: None)
        
        self.is_running = False
        self.is_paused = False
        self.should_stop = False
        self.pending_manual_close = False
        
        # Speed control: 1x = 1 second per candle (intuitive 1:1 timing)
        self.speed_multiplier = config.get("speed_multiplier", 1)
        self.base_delay_sec = 1.0  # 1x = 1 second per candle
        
        # Multiplier
        self.multiplier = config.get("multiplier", 10)

        # Cached live state for seamless client catchup on connect/reconnect
        self.recent_candles: list[dict] = []
        self.current_tick: int = 0
        self.latest_decision: str = "HOLD"
        self.latest_confidence: dict = {"BUY": 0.33, "HOLD": 0.34, "SELL": 0.33}
        self.latest_active_count: int = 150
        self.latest_fired_ids: list = []
        self.total_spikes: int = 0
        self.latest_clusters: dict = {}
        self.latest_neurotransmitters: dict = {"dopamine": 0.5, "octopamine": 0.3, "serotonin": 0.6, "cortisol": 0.2}
        self.latest_bio_latency: float = 25.0
        self.latest_inference_ms: float = 1.0
        self.latest_firing_hz: float = 120.0
        self.latest_mb_active: int = 0
        self.latest_memory_strength: float = 0.0
        self.latest_market_features: dict = {}

    def request_manual_close(self) -> None:
        """Flag to book all open positions at market price."""
        self.pending_manual_close = True

    def set_speed(self, speed: int | float) -> None:
        """Dynamically update simulation playback speed."""
        self.speed_multiplier = max(1, min(100, int(speed)))

    def set_multiplier(self, mult: int) -> None:
        """Dynamically update leverage multiplier."""
        self.multiplier = max(1, min(50, mult))
        if hasattr(self, "trade_engine"):
            self.trade_engine.set_multiplier(self.multiplier)

    def pause(self) -> bool:
        self.is_paused = not self.is_paused
        return self.is_paused

    def stop(self) -> None:
        self.should_stop = True
        self.is_running = False

    def run_sync(self) -> dict:
        """Synchronous compatibility wrapper around run_async."""
        return asyncio.run(self.run_async())

    async def run_async(self) -> dict:
        """Asynchronous cooperative run loop with genuine neural decision-making."""
        self.is_running = True
        self.should_stop = False
        cfg = self.cfg

        # 1. Load data
        candles = load_candles_with_offset(self.dataset_name, self.start_time)
        if len(candles) < 25:
            raise ValueError(f"Insufficient candles ({len(candles)}) for simulation.")

        # 2. Build Fruit Fly Connectome Brain
        conn_path = cfg.get("connectome_path", "../data/connectome/flyconnectome_edges.csv")
        # Ensure path is absolute if relative
        if not os.path.isabs(conn_path):
            conn_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", conn_path))
        
        max_neurons = cfg.get("max_neurons", 800)
        seed = cfg.get("seed")
        # If seed is unspecified or default 42, generate biological noise seed so runs are unique & strategic
        actual_seed = seed if (seed is not None and seed != 42) else random.randint(1, 2147483647)
        reseed_neural_rng(actual_seed)
        conn = from_file(conn_path, max_neurons=max_neurons, seed=actual_seed)
        brain = Brain(conn, cfg.get("brain", {}))
        plasticity = PlasticityEngine(brain, cfg.get("plasticity", {}))
        pruning = PruningEngine(brain, cfg.get("pruning", {}))

        # 3. Initialize High-Frequency Micro-Trading Engine with INR Wallet
        wallet_cfg = cfg.get("wallet", {})
        initial_cap_inr = wallet_cfg.get("initial_capital_inr", 500000.0)
        currency = wallet_cfg.get("currency", "INR")
        self.trade_engine = MicroTradingEngine(
            initial_capital_inr=initial_cap_inr,
            currency=currency,
            default_multiplier=self.multiplier,
            stake_pct=wallet_cfg.get("stake_pct", 0.05),
            fee_bps=cfg.get("fee_bps", 3.0),
            slippage_bps=cfg.get("slippage_bps", 2.0),
            take_profit_pct=cfg.get("take_profit_pct", 0.012),
            stop_loss_pct=cfg.get("stop_loss_pct", 0.010),
            max_hold_ticks=cfg.get("max_hold_ticks", 8),
            usd_inr_rate=cfg.get("usd_inr_rate", wallet_cfg.get("usd_inr_rate", 83.75)),
            max_concurrent_trades=cfg.get("max_concurrent_trades", 3),
            hold_ticks_min=cfg.get("hold_ticks_min", 5),
            hold_ticks_max=cfg.get("hold_ticks_max", 60),
        )

        # 4. Emit initial historical snapshot so the candlestick chart opens immediately populated
        warmup_len = min(60, len(candles))
        history = list(candles[:warmup_len])
        self.recent_candles = [
            {
                "ts": c.ts,
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "volume": c.volume,
            }
            for c in history
        ]
        self.on_event({
            "type": "init_history",
            "dataset": self.dataset_name,
            "candles": list(self.recent_candles),
        })

        pending_reward = 0.0
        global_tick = warmup_len
        
        # Trade memory for Mushroom Body associative learning
        trade_memory: list[dict] = []

        while not self.should_stop:
            for candle in candles[warmup_len:]:
                if self.should_stop:
                    break
                global_tick += 1
                tick = global_tick

                # Handle pause
                while self.is_paused and not self.should_stop:
                    if self.pending_manual_close and hasattr(self, "trade_engine"):
                        self._handle_manual_close(candle, tick, brain, trade_memory)
                    await asyncio.sleep(0.05)

                # Process any manual close requested while running
                if self.pending_manual_close and hasattr(self, "trade_engine"):
                    self._handle_manual_close(candle, tick, brain, trade_memory)

                history.append(candle)
                if len(history) > 250:
                    history.pop(0)

                # 1. Reward-modulated synaptic plasticity from recent trade
                if pending_reward != 0.0:
                    plasticity.apply_modulation(pending_reward)
                    pending_reward = 0.0

                # 2. Sensory transduction into Drosophila compound eyes & antennae
                # Pass trade_memory for Mushroom Body memory bias computation
                market_feats = features(history, trade_memory=trade_memory)
                brain.modulate_transmitters(0.0, market_feats.get("volatility", 0.1))
                brain.set_sensory_input(market_feats)

                # 3. Neural propagation & decision
                fired = brain.active_neurons()
                plasticity.hebbian_pass(fired)
                telemetry = brain.step()
                plasticity.decay_traces()

                confidence = telemetry["confidence"]
                best_action = max(confidence, key=confidence.get)
                
                # Neuromodulator-adjusted action threshold:
                # High cortisol → brain hesitates more (wider threshold)
                # High dopamine → brain acts more boldly (narrower threshold)
                base_threshold = cfg.get("action_threshold", 0.04)
                neuromod_threshold = base_threshold * (1.0 + brain.cortisol * 0.5 - (brain.dopamine - 0.5) * 0.3)
                neuromod_threshold = max(0.02, min(0.15, neuromod_threshold))

                # Clear action choice
                decision = best_action if (confidence[best_action] - confidence.get("HOLD", 0)) > neuromod_threshold or best_action == "HOLD" else "HOLD"

                # 4. Update mark with active brain state (triggers brain reversals, cortisol defenses, profit satiation)
                brain_state = {
                    "decision": decision,
                    "cortisol": brain.cortisol,
                    "dopamine": brain.dopamine,
                }
                closed_trades = self.trade_engine.update_mark(candle, tick, brain_state=brain_state)
                for ct in closed_trades:
                    # Modulate dopamine & cortisol upon closing trade
                    reward_val = 1.0 if ct.pnl_inr > 0 else -1.0
                    brain.modulate_transmitters(reward_val * 0.7, 0.2)
                    pending_reward = reward_val * 0.8
                    
                    # Feed trade outcome to Mushroom Body for associative learning
                    trade_outcome = {
                        "side": ct.side,
                        "pnl_pct": ct.pnl_pct,
                        "pnl_inr": ct.pnl_inr,
                        "reason": ct.exit_reason,
                        "hold_duration": ct.exit_tick - ct.entry_tick,
                    }
                    brain.inject_trade_memory(trade_outcome)
                    trade_memory.append(trade_outcome)
                    if len(trade_memory) > 20:
                        trade_memory.pop(0)
                    
                    self.on_event({
                        "type": "trade_closed",
                        "trade": {
                            "id": ct.trade_id,
                            "side": ct.side,
                            "multiplier": ct.multiplier,
                            "entry_price": ct.entry_price,
                            "exit_price": ct.exit_price,
                            "pnl_inr": ct.pnl_inr,
                            "pnl_pct": ct.pnl_pct,
                            "reason": ct.exit_reason,
                            "entry_ts": ct.entry_ts,
                            "exit_ts": ct.exit_ts,
                            "hold_duration": ct.exit_tick - ct.entry_tick,
                        },
                        "wallet": self.trade_engine.get_wallet_summary(candle.close),
                    })

                # 5. Execute micro-trade if brain signals BUY or SELL
                new_trade = None
                if decision in ("BUY", "SELL"):
                    new_trade = self.trade_engine.execute_brain_signal(decision, candle, tick, self.multiplier)
                    if new_trade:
                        brain.on_trade_opened()
                        self.on_event({
                            "type": "trade_opened",
                            "trade": {
                                "id": new_trade.trade_id,
                                "side": new_trade.side,
                                "multiplier": new_trade.multiplier,
                                "entry_price": new_trade.entry_price,
                                "stake_inr": new_trade.stake_inr,
                                "entry_ts": new_trade.entry_ts,
                                "entry_tick": new_trade.entry_tick,
                                "max_hold_ticks": new_trade.max_hold_ticks,
                            },
                            "wallet": self.trade_engine.get_wallet_summary(candle.close),
                        })

                # 6. Evaluate structural pruning periodically
                prune_events = pruning.evaluate()
                for pe in prune_events:
                    self.on_event(pe)

                # 7. Wallet snapshot
                wallet_summary = self.trade_engine.get_wallet_summary(candle.close)
                if not hasattr(self, "total_spikes"):
                    self.total_spikes = 0
                self.total_spikes += len(fired)

                # 8. Update cached state
                c_dict = {
                    "ts": candle.ts,
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "volume": candle.volume,
                }
                self.recent_candles.append(c_dict)
                if len(self.recent_candles) > 300:
                    self.recent_candles.pop(0)

                self.current_tick = tick
                self.latest_decision = decision
                self.latest_confidence = confidence
                self.latest_active_count = telemetry["active_count"]
                self.latest_fired_ids = fired
                self.latest_clusters = telemetry["clusters"]
                self.latest_neurotransmitters = telemetry["neurotransmitters"]
                self.latest_bio_latency = telemetry["biological_reaction_time_ms"]
                self.latest_inference_ms = telemetry["inference_time_ms"]
                self.latest_firing_hz = telemetry["firing_rate_hz"]
                self.latest_mb_active = telemetry.get("mushroom_body_active", 0)
                self.latest_memory_strength = telemetry.get("memory_strength", 0.0)
                self.latest_market_features = market_feats

                # Send rich tick event
                self.on_event({
                    "type": "tick",
                    "tick": tick,
                    "ts": candle.ts,
                    "candle": c_dict,
                    "decision": decision,
                    "confidence": confidence,
                    "active_neurons": telemetry["active_count"],
                    "fired_ids": fired,
                    "total_spikes": self.total_spikes,
                    "total_neurons": conn.n_neurons,
                    "clusters": telemetry["clusters"],
                    "neurotransmitters": telemetry["neurotransmitters"],
                    "bio_latency_ms": telemetry["biological_reaction_time_ms"],
                    "inference_ms": telemetry["inference_time_ms"],
                    "firing_rate_hz": telemetry["firing_rate_hz"],
                    "mushroom_body_active": telemetry.get("mushroom_body_active", 0),
                    "memory_strength": telemetry.get("memory_strength", 0.0),
                    "speed": self.speed_multiplier,
                    "wallet": wallet_summary,
                    "market_features": {
                        "rsi": round(market_feats.get("rsi", 0.0), 3),
                        "pattern_bullish": round(market_feats.get("pattern_bullish", 0.0), 3),
                        "pattern_bearish": round(market_feats.get("pattern_bearish", 0.0), 3),
                        "breakout_signal": round(market_feats.get("breakout_signal", 0.0), 3),
                        "reversal_signal": round(market_feats.get("reversal_signal", 0.0), 3),
                    },
                })

                # 9. Cooperative non-blocking sleep regulation for simulation pacing
                if self.speed_multiplier > 0:
                    sleep_sec = self.base_delay_sec / self.speed_multiplier
                    await asyncio.sleep(max(0.005, sleep_sec))
                else:
                    await asyncio.sleep(0.01)

        self.is_running = False
        final_wallet = self.trade_engine.get_wallet_summary()
        manifest = {
            "created": time.time(),
            "dataset": self.dataset_name,
            "config": cfg,
            "brain": {
                "neurons": conn.n_neurons,
                "synapses": conn.n_synapses,
                "pruned_neurons": brain.pruned_neurons,
                "pruned_synapses": brain.pruned_synapses,
            },
            "wallet": final_wallet,
        }
        return manifest

    def _handle_manual_close(self, candle, tick, brain, trade_memory):
        """Process manual close all request with proper brain feedback."""
        self.pending_manual_close = False
        manually_closed = self.trade_engine.manual_close_all(candle, tick)
        for ct in manually_closed:
            reward_val = 1.0 if ct.pnl_inr > 0 else -1.0
            brain.modulate_transmitters(reward_val * 0.7, 0.2)
            
            trade_outcome = {
                "side": ct.side,
                "pnl_pct": ct.pnl_pct,
                "pnl_inr": ct.pnl_inr,
                "reason": ct.exit_reason,
                "hold_duration": ct.exit_tick - ct.entry_tick,
            }
            brain.inject_trade_memory(trade_outcome)
            trade_memory.append(trade_outcome)
            if len(trade_memory) > 20:
                trade_memory.pop(0)
            
            self.on_event({
                "type": "trade_closed",
                "trade": {
                    "id": ct.trade_id,
                    "side": ct.side,
                    "multiplier": ct.multiplier,
                    "entry_price": ct.entry_price,
                    "exit_price": ct.exit_price,
                    "pnl_inr": ct.pnl_inr,
                    "pnl_pct": ct.pnl_pct,
                    "reason": ct.exit_reason,
                    "entry_ts": ct.entry_ts,
                    "exit_ts": ct.exit_ts,
                    "hold_duration": ct.exit_tick - ct.entry_tick,
                },
                "wallet": self.trade_engine.get_wallet_summary(candle.close),
            })
