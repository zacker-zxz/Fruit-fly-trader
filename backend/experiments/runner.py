"""Interactive simulation runner with biological Drosophila timing and micro-trading.

Supports:
- Speed multipliers: 1x, 2x, 5x, 10x, 20x, MAX.
- Dynamic pause, resume, stop, and parameter adjustments on the fly.
- INR wallet and fast micro-trading with multiplier leverage.
- Realistic fly neural propagation, biological latency, and neurotransmitter tracking.
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
        
        # Speed control: 1x, 2x, 5x, 10x, 20x (1x = ~1.2s per candle for organic observation)
        self.speed_multiplier = config.get("speed_multiplier", 1)
        self.base_delay_sec = 1.2  # Calm, realistic market tick cadence at 1x
        
        # Multiplier
        self.multiplier = config.get("multiplier", 10)

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
        """Synchronous run loop."""
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
        seed = cfg.get("seed", 42)
        conn = from_file(conn_path, max_neurons=max_neurons, seed=seed)
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
        )

        history: list = []
        pending_reward = 0.0

        for tick, candle in enumerate(candles):
            if self.should_stop:
                break

            # Handle pause
            while self.is_paused and not self.should_stop:
                time.sleep(0.05)

            history.append(candle)
            
            # 1. Update mark and auto-book profits or stop-loss
            closed_trades = self.trade_engine.update_mark(candle, tick)
            for ct in closed_trades:
                # Modulate dopamine & cortisol upon closing trade
                reward_val = 1.0 if ct.pnl_inr > 0 else -1.0
                brain.modulate_transmitters(reward_val * 0.7, 0.2)
                pending_reward = reward_val * 0.8
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

            if tick < 21:
                continue

            # 2. Reward-modulated synaptic plasticity from recent trade
            if pending_reward != 0.0:
                plasticity.apply_modulation(pending_reward)
                pending_reward = 0.0

            # 3. Sensory transduction into Drosophila compound eyes & antennae
            market_feats = features(history)
            brain.modulate_transmitters(0.0, market_feats.get("volatility", 0.1))
            brain.set_sensory_input(market_feats)

            # 4. Neural propagation & decision
            fired = brain.active_neurons()
            plasticity.hebbian_pass(fired)
            telemetry = brain.step()
            plasticity.decay_traces()

            confidence = telemetry["confidence"]
            best_action = max(confidence, key=confidence.get)
            action_threshold = cfg.get("action_threshold", 0.04)

            # Clear action choice
            decision = best_action if (confidence[best_action] - confidence.get("HOLD", 0)) > action_threshold or best_action == "HOLD" else "HOLD"

            # 5. Execute micro-trade or brain-directed reversal
            new_trade = None
            if decision in ("BUY", "SELL"):
                # If fly is in an opposing position, brain actively reverses and books trade!
                for ot in list(self.trade_engine.open_trades):
                    opposing = (ot.side == "UP" and decision == "SELL") or (ot.side == "DOWN" and decision == "BUY")
                    if opposing:
                        raw_ret = (candle.close - ot.entry_price) / ot.entry_price
                        dir_ret = raw_ret if ot.side == "UP" else -raw_ret
                        cost_rate = (self.trade_engine.fee_bps + self.trade_engine.slippage_bps) / 10000.0
                        closed_rev = self.trade_engine._close_trade(ot, candle, tick, "BRAIN_REVERSAL", (dir_ret * ot.multiplier) - cost_rate)
                        reward_val = 1.0 if closed_rev.pnl_inr > 0 else -1.0
                        brain.modulate_transmitters(reward_val * 0.7, 0.2)
                        self.on_event({
                            "type": "trade_closed",
                            "trade": {
                                "id": closed_rev.trade_id,
                                "side": closed_rev.side,
                                "multiplier": closed_rev.multiplier,
                                "entry_price": closed_rev.entry_price,
                                "exit_price": closed_rev.exit_price,
                                "pnl_inr": closed_rev.pnl_inr,
                                "pnl_pct": closed_rev.pnl_pct,
                                "reason": closed_rev.exit_reason,
                                "entry_ts": closed_rev.entry_ts,
                                "exit_ts": closed_rev.exit_ts,
                                "hold_duration": closed_rev.exit_tick - closed_rev.entry_tick,
                            },
                            "wallet": self.trade_engine.get_wallet_summary(candle.close),
                        })

                new_trade = self.trade_engine.execute_brain_signal(decision, candle, tick, self.multiplier)
                if new_trade:
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

            # 8. Send rich tick event
            self.on_event({
                "type": "tick",
                "tick": tick,
                "ts": candle.ts,
                "candle": {
                    "ts": candle.ts,
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "volume": candle.volume,
                },
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
                "speed": self.speed_multiplier,
                "wallet": wallet_summary,
            })

            # 9. Sleep regulation for simulation pacing
            if self.speed_multiplier > 0:
                sleep_sec = self.base_delay_sec / self.speed_multiplier
                # Ensure minimum slice for event processing
                if sleep_sec > 0.002:
                    time.sleep(sleep_sec)

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
