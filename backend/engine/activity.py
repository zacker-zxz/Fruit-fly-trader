"""Per-tick signal propagation over the Drosophila connectome subgraph.

Models authentic anatomical compartments:
- Optic Lobe (Compound Eyes: Visual price action, momentum, trend, patterns)
- Antennal Lobe (Antennae: Market volatility, volume turbulence, breakout signals)
- Mushroom Body (Associative learning, memory of trade outcomes, pattern-reward mapping)
- Central Complex (Steering heading: UP / DOWN action selection)
- Descending Motor Neurons (Wing motor execution: BUY_UP, HOLD, SELL_DOWN)

Tracks neuromodulators (Dopamine, Octopamine, Serotonin, Cortisol) and biological latency.
"""

import time
import math
from .connectome import Connectome
from .neuron import Neuron, _NEURAL_RNG
from .synapse import Synapse


class Brain:
    def __init__(self, connectome: Connectome, config: dict):
        self.c = connectome
        self.cfg = config
        self.tick = 0
        n = connectome.n_neurons
        base_threshold = config.get("threshold", 0.8)
        
        # Partition neurons into biological Drosophila compartments
        n_sensory = max(6, n // 15)
        n_optic = n_sensory // 2
        n_antennal = n_sensory - n_optic
        n_motor = 3
        n_internal = n - n_sensory - n_motor
        n_mb = int(n_internal * 0.40)  # 40% Mushroom Body
        n_cx = n_internal - n_mb       # 60% Central Complex
        
        # Store partition boundaries for later use
        self.n_sensory = n_sensory
        self.n_optic = n_optic
        self.n_antennal = n_antennal
        self.n_mb = n_mb
        self.n_cx = n_cx
        self.mb_start = n_sensory
        self.cx_start = n_sensory + n_mb
        self.motor_start = n - n_motor
        
        self.neurons: list[Neuron] = []
        for i in range(n):
            if i < n_optic:
                # Optic Lobe (Sensory vision: Price Action, Trend, Patterns)
                self.neurons.append(Neuron(neuron_id=i, kind="sensory", cluster="optic_lobe",
                                           threshold=base_threshold * 0.25, decay=0.85,
                                           noise_amplitude=0.03, spontaneous_rate=0.001))
            elif i < n_sensory:
                # Antennal Lobe (Sensory olfactory/turbulence: Volatility, Volume, Breakouts)
                self.neurons.append(Neuron(neuron_id=i, kind="sensory", cluster="antennal_lobe",
                                           threshold=base_threshold * 0.25, decay=0.85,
                                           noise_amplitude=0.03, spontaneous_rate=0.001))
            elif i < n_sensory + n_mb:
                # Mushroom Body (Associative Memory & Pattern-Reward Learning)
                self.neurons.append(Neuron(neuron_id=i, kind="internal", cluster="mushroom_body",
                                           threshold=base_threshold * 0.7, decay=0.75,
                                           noise_amplitude=0.06, spontaneous_rate=0.005))
            elif i < n - n_motor:
                # Central Complex (Navigation & Steering)
                self.neurons.append(Neuron(neuron_id=i, kind="internal", cluster="central_complex",
                                           threshold=base_threshold * 0.65, decay=0.7,
                                           noise_amplitude=0.05, spontaneous_rate=0.003))
            else:
                # Descending Motor Neurons (DNa01, DNa02, DNp01)
                action_kind = ["decision_buy", "decision_hold", "decision_sell"][i - (n - n_motor)]
                self.neurons.append(Neuron(neuron_id=i, kind=action_kind, cluster="motor_output",
                                           threshold=base_threshold * 0.5, decay=0.6,
                                           noise_amplitude=0.04, spontaneous_rate=0.002))

        # Map synapses from connectome edge list
        self.synapses: list[Synapse] = []
        sid = 0
        for ni, edge_ids in connectome.out_edges.items():
            for eid in edge_ids:
                e = connectome.edges[eid]
                tgt_idx = connectome.index.get(e.tgt)
                if tgt_idx is not None:
                    # Weight scaled from biological synapse count
                    w = 0.08 + 0.02 * min(15, e.weight)
                    self.synapses.append(Synapse(synapse_id=sid, source=ni, target=tgt_idx, weight=w))
                    sid += 1

        # Ensure sensory feed-forward projections into Central Complex and Mushroom Body
        mb_start = n_sensory
        cx_start = n_sensory + n_mb
        for s_idx in range(n_sensory):
            # Connect sensory to first few MB Kenyon cells and CX neurons
            target_mb = mb_start + (s_idx * 3) % max(1, n_mb)
            target_cx = cx_start + (s_idx * 5) % max(1, n_cx)
            self.synapses.append(Synapse(synapse_id=sid, source=s_idx, target=target_mb, weight=0.45))
            sid += 1
            self.synapses.append(Synapse(synapse_id=sid, source=s_idx, target=target_cx, weight=0.45))
            sid += 1

        # Mushroom Body output → Central Complex (memory influences decisions)
        for i in range(min(30, n_mb)):
            src_mb = mb_start + i
            tgt_cx = cx_start + (i * 3) % max(1, n_cx)
            self.synapses.append(Synapse(synapse_id=sid, source=src_mb, target=tgt_cx, weight=0.30))
            sid += 1

        # Ensure descending motor projections from Central Complex and Mushroom Body to output neurons
        motor_start = n - n_motor
        for i in range(20):
            src_cx = cx_start + (i * 7) % max(1, n_cx)
            # Route to UP (0), HOLD (1), DOWN (2)
            tgt_m = motor_start + (i % 3)
            self.synapses.append(Synapse(synapse_id=sid, source=src_cx, target=tgt_m, weight=0.35))
            sid += 1

        # Neuromodulators
        self.dopamine: float = 0.5      # [0, 1] Reward & appetitive learning (surges on win)
        self.cortisol: float = 0.2      # [0, 1] Stress hormone & risk aversion (surges on loss)
        self.octopamine: float = 0.3    # [0, 1] Arousal, market volatility flight-response
        self.serotonin: float = 0.6     # [0, 1] Baseline behavioral stability & impulse control
        
        self.decision_confidence: dict[str, float] = {"BUY": 0.33, "HOLD": 0.34, "SELL": 0.33}
        self.pruned_neurons: int = 0
        self.pruned_synapses: int = 0
        self.last_inference_ms: float = 1.0
        
        # Trade cooldown: serotonin-modulated impulse control
        self.ticks_since_last_trade: int = 999
        
        # Mushroom Body associative memory state
        self._mb_memory_signal: float = 0.0  # Current memory bias injected into MB

    def modulate_transmitters(self, reward_delta: float, volatility: float) -> None:
        """Dynamically update fly neurotransmitters based on trade outcomes and market state."""
        # Dopamine surges with positive reward (profit booked)
        if reward_delta > 0:
            self.dopamine = min(1.0, self.dopamine + reward_delta * 0.35)
            self.cortisol = max(0.05, self.cortisol - reward_delta * 0.25)
        elif reward_delta < 0:
            # Cortisol stress hormone surges on loss / stop out
            self.cortisol = min(1.0, self.cortisol + abs(reward_delta) * 0.35)
            self.dopamine = max(0.05, self.dopamine - abs(reward_delta) * 0.25)

        # Baseline decay towards resting equilibrium
        self.dopamine += (0.5 - self.dopamine) * 0.05
        self.cortisol += (0.2 - self.cortisol) * 0.05

        # Octopamine scales with market turbulence & sensory drive
        target_oa = min(1.0, max(0.1, volatility * 1.5))
        self.octopamine += (target_oa - self.octopamine) * 0.15

        # Serotonin balances impulsive flipping — recovers slowly
        self.serotonin = max(0.1, min(0.9, 0.8 - self.cortisol * 0.35))

    def inject_trade_memory(self, trade_outcome: dict) -> None:
        """Inject trade outcome into Mushroom Body for associative learning.
        
        This models dopaminergic reinforcement of Kenyon cell → MBON pathways:
        - Profitable trades strengthen the MB neurons that were active at entry
        - Losing trades weaken those same neurons
        """
        pnl_pct = trade_outcome.get("pnl_pct", 0.0) / 100.0
        side = trade_outcome.get("side", "UP")
        
        # Update memory bias signal that gets injected into MB on next tick
        self._mb_memory_signal = max(-1.0, min(1.0, pnl_pct * 5.0))
        
        # Directly modulate reward_association in Mushroom Body neurons
        # This creates associative memories: neurons that were recently active
        # during trading get their reward_association adjusted
        for i in range(self.mb_start, self.mb_start + self.n_mb):
            n = self.neurons[i]
            if n.pruned:
                continue
            # Neurons that recently fired get stronger memory update
            recent_activity = sum(n.activity_history[-5:]) / max(1, len(n.activity_history[-5:]))
            if recent_activity > 0.1:
                lr = 0.15  # Memory formation learning rate
                n.reward_association += lr * pnl_pct * (1.0 + recent_activity)
                n.reward_association = max(-1.0, min(1.0, n.reward_association))
                # Adjust threshold based on learned association
                # Good associations → slightly more excitable
                n.threshold += -0.005 * pnl_pct * recent_activity
                n.threshold = max(0.2, min(2.0, n.threshold))

    def set_sensory_input(self, signals: dict[str, float]) -> None:
        """Drive Drosophila compound eyes and antennae with rich market features."""
        n_sensory = self.n_sensory
        n_optic = self.n_optic
        
        # ── Optic Lobe: Price Action, Momentum, Trend, Patterns, RSI ──
        optic_keys = ["price_change", "momentum", "trend", "pattern_bullish", "pattern_bearish", "rsi"]
        per_optic = max(1, n_optic // len(optic_keys))
        for gi, key in enumerate(optic_keys):
            val = signals.get(key, 0.0)
            start = gi * per_optic
            end = start + per_optic if gi < len(optic_keys) - 1 else n_optic
            for j, ni in enumerate(range(start, min(end, n_optic))):
                neuron = self.neurons[ni]
                # Tuning curve across [-1, 1]
                tuning = -1.0 + 2.0 * j / max(1, (end - start - 1))
                drive = max(0.0, 1.0 - abs(val - tuning))
                # Boost excitability with Octopamine (high arousal fly sees sharper)
                gain = 0.7 + 0.5 * self.octopamine
                neuron.activation += gain * (drive * 0.8 + abs(val) * 0.4)

        # ── Antennal Lobe: Volatility, Volume, Breakout, Reversal, Range ──
        antennal_keys = ["volatility", "volume", "breakout_signal", "reversal_signal", "range_position"]
        start_al = n_optic
        per_antennal = max(1, (n_sensory - n_optic) // len(antennal_keys))
        for gi, key in enumerate(antennal_keys):
            val = signals.get(key, 0.0)
            start = start_al + gi * per_antennal
            end = start + per_antennal if gi < len(antennal_keys) - 1 else n_sensory
            for j, ni in enumerate(range(start, min(end, n_sensory))):
                neuron = self.neurons[ni]
                gain = 0.8 + 0.4 * self.octopamine
                neuron.activation += gain * abs(val) * 0.9

        # ── Mushroom Body Memory Injection ──
        # Inject trade outcome memory and memory_bias feature into Kenyon cells
        memory_bias = signals.get("memory_bias", 0.0)
        combined_memory = (self._mb_memory_signal * 0.6 + memory_bias * 0.4)
        for i in range(self.mb_start, min(self.mb_start + 10, self.mb_start + self.n_mb)):
            n = self.neurons[i]
            if not n.pruned:
                # Neurons with positive reward_association get boosted
                mem_drive = combined_memory * 0.5 + n.reward_association * 0.3
                n.activation += mem_drive
        # Decay the memory signal over time
        self._mb_memory_signal *= 0.85

        # ── Descending Motor Neuron Drive ──
        p_chg = signals.get("price_change", 0.0)
        mom = signals.get("momentum", 0.0)
        trend = signals.get("trend", 0.0)
        rsi = signals.get("rsi", 0.0)
        pattern_bull = signals.get("pattern_bullish", 0.0)
        pattern_bear = signals.get("pattern_bearish", 0.0)
        reversal = signals.get("reversal_signal", 0.0)
        
        # Composite directional drive from multiple market features
        directional_drive = (
            p_chg * 2.5 +
            mom * 1.5 +
            trend * 1.0 +
            pattern_bull * 1.5 - pattern_bear * 1.5 +
            reversal * 1.2 +
            rsi * -0.8  # Counter-trend: overbought → sell pressure, oversold → buy pressure
        )
        
        motor_start = self.motor_start
        # Reset motor neuron activations each step so decisions are freshly calculated
        self.neurons[motor_start].activation = 0.0
        self.neurons[motor_start + 1].activation = 0.0
        self.neurons[motor_start + 2].activation = 0.0

        # ── Neuromodulator effects on motor decisions ──
        # Dopamine boosts risk-taking (lower threshold for action)
        da_boost = 1.0 + 0.8 * (self.dopamine - 0.5)
        # Cortisol induces hesitation → stronger HOLD bias
        cort_damp = max(0.3, 1.0 - self.cortisol * 0.8)
        # Serotonin controls impulsivity → if low, random noise in motor drive
        sero_stability = 0.6 + 0.4 * self.serotonin
        
        # Serotonin-modulated impulse control: suppress action if we traded very recently
        self.ticks_since_last_trade += 1
        impulse_gate = min(1.0, self.ticks_since_last_trade / max(3, 8.0 * (1.0 - self.serotonin)))

        # Motor neuron noise: models biological variability in motor commands
        motor_noise = _NEURAL_RNG.gauss(0.0, 0.08 * (1.0 - sero_stability))

        if directional_drive > 0.03:
            drive_strength = min(4.0, abs(directional_drive) * 2.0 * da_boost * cort_damp * impulse_gate)
            self.neurons[motor_start].activation = drive_strength + motor_noise
        elif directional_drive < -0.03:
            drive_strength = min(4.0, abs(directional_drive) * 2.0 * da_boost * cort_damp * impulse_gate)
            self.neurons[motor_start + 2].activation = drive_strength + motor_noise
        else:
            # HOLD: cortisol amplifies hold signal
            hold_drive = 0.60 + self.cortisol * 0.4
            self.neurons[motor_start + 1].activation = hold_drive

    def on_trade_opened(self) -> None:
        """Called when a trade is opened to reset the serotonin impulse gate."""
        self.ticks_since_last_trade = 0

    def step(self) -> dict[str, float]:
        """Propagate neural signals across connectome. Returns decision activations and telemetry."""
        t0 = time.perf_counter()
        self.tick += 1
        n = self.c.n_neurons
        input_sums = [0.0] * n

        # 1. Fire sensory neurons based on transduced market activation
        n_sensory = self.n_sensory
        for i in range(n_sensory):
            sn = self.neurons[i]
            if sn.activation >= sn.threshold:
                sn.fired = True
                sn.activation = 0.0
                sn.last_activation = self.tick
            else:
                sn.fired = False

        # 2. Synaptic transmission across connectome
        # Modulated by dopamine (rewards reinforce transmission efficiency)
        da_gain = 0.8 + 0.4 * self.dopamine
        for s in self.synapses:
            if s.pruned:
                continue
            src = self.neurons[s.source]
            if src.fired or src.activation > 0.15:
                signal = 1.0 if src.fired else (src.activation * 0.5)
                input_sums[s.target] += s.weight * s.strength * da_gain * signal
                s.touch(self.tick)

        # 3. Neuronal integration & spike generation for internal and motor neurons
        cluster_counts = {"optic_lobe": 0, "antennal_lobe": 0, "mushroom_body": 0,
                          "central_complex": 0, "motor_output": 0}
        total_fired = 0

        for idx in range(n):
            neuron = self.neurons[idx]
            if idx >= n_sensory:
                neuron.integrate(input_sums[neuron.neuron_id], self.tick)
            if neuron.fired:
                total_fired += 1
                cluster_counts[neuron.cluster] = cluster_counts.get(neuron.cluster, 0) + 1

        # 4. Motor Output Neurons (Last 3: BUY_UP, HOLD, SELL_DOWN)
        motor_start = self.motor_start
        buy_n = self.neurons[motor_start]
        hold_n = self.neurons[motor_start + 1]
        sell_n = self.neurons[motor_start + 2]

        raw_decisions = {
            "BUY": max(0.0, buy_n.activation + (1.2 if buy_n.fired else 0.0)),
            "HOLD": max(0.12, hold_n.activation + (0.6 if hold_n.fired else 0.0)),
            "SELL": max(0.0, sell_n.activation + (1.2 if sell_n.fired else 0.0)),
        }

        # Softmax / Normalized confidence distribution
        eps = 1e-4
        total_act = sum(v + eps for v in raw_decisions.values())
        self.decision_confidence = {k: (v + eps) / total_act for k, v in raw_decisions.items()}

        t1 = time.perf_counter()
        self.last_inference_ms = max(0.1, (t1 - t0) * 1000.0)

        # Biological latency estimate: Drosophila saccadic reflex ~22-35ms
        bio_latency_ms = 28.0 - (self.octopamine * 8.0) + (self.last_inference_ms * 0.5)

        # Estimated biological spike frequency in Hz
        firing_rate_hz = (total_fired / max(1, n)) * 600.0 + 30.0

        # Mushroom Body activity summary for telemetry
        mb_activity = sum(
            1 for i in range(self.mb_start, self.mb_start + self.n_mb)
            if self.neurons[i].fired
        )
        mb_memory_strength = sum(
            abs(self.neurons[i].reward_association)
            for i in range(self.mb_start, self.mb_start + self.n_mb)
            if not self.neurons[i].pruned
        ) / max(1, self.n_mb)

        return {
            "decisions": raw_decisions,
            "confidence": self.decision_confidence,
            "active_count": total_fired,
            "clusters": cluster_counts,
            "neurotransmitters": {
                "dopamine": round(self.dopamine, 3),
                "cortisol": round(self.cortisol, 3),
                "octopamine": round(self.octopamine, 3),
                "serotonin": round(self.serotonin, 3),
            },
            "biological_reaction_time_ms": round(bio_latency_ms, 1),
            "inference_time_ms": round(self.last_inference_ms, 2),
            "firing_rate_hz": round(firing_rate_hz, 1),
            "mushroom_body_active": mb_activity,
            "memory_strength": round(mb_memory_strength, 4),
        }

    def active_neurons(self) -> list[int]:
        return [n.neuron_id for n in self.neurons if n.fired]
