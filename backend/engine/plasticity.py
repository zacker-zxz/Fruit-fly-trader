"""Reward-modulated STDP with eligibility traces.

Local Hebbian traces accumulate when presynaptic firing precedes postsynaptic
firing. A scalar neuromodulatory signal (reward/punishment) gates weight
change. All modifications are recorded in an event log for inspection.
"""

from .activity import Brain


class PlasticityEngine:
    def __init__(self, brain: Brain, config: dict):
        self.brain = brain
        self.cfg = config
        self.events: list[dict] = []
        self.counts = {"strengthened": 0, "weakened": 0, "pruned_neurons": 0, "pruned_synapses": 0}

    def decay_traces(self) -> None:
        d = self.cfg.get("trace_decay", 0.9)
        for s in self.brain.synapses:
            if not s.pruned:
                s.eligibility *= d

    def hebbian_pass(self, fired_before: list[int]) -> None:
        """Coincident firing strengthens eligibility of active synapses."""
        fired = set(fired_before)
        for s in self.brain.synapses:
            if s.pruned:
                continue
            if s.source in fired:
                s.strength = min(1.0, s.strength + self.cfg.get("hebbian_rate", 0.002))
                # co-activation makes the synapse eligible for later credit
                s.eligibility = min(1.0, s.eligibility + self.cfg.get("trace_gain", 0.5))

    def apply_modulation(self, reward: float) -> dict:
        """Apply reward-modulated weight change to eligible synapses."""
        lr = self.cfg.get("learning_rate", 0.01)
        cap = self.cfg.get("weight_cap", 2.0)
        strengthened = weakened = 0
        for s in self.brain.synapses:
            if s.pruned or abs(s.eligibility) < 1e-6:
                continue
            delta = lr * reward * s.eligibility
            before = s.weight
            s.weight = max(0.0, min(cap, s.weight + delta))
            if reward >= 0:
                s.successful_contribution += abs(delta)
            else:
                s.failure_contribution += abs(delta)
            if s.weight > before:
                strengthened += 1
            elif s.weight < before:
                weakened += 1
            s.eligibility *= 0.5  # credit assigned, trace decays
        self.counts["strengthened"] += strengthened
        self.counts["weakened"] += weakened
        event = {"tick": self.brain.tick, "reward": reward,
                 "strengthened": strengthened, "weakened": weakened}
        self.events.append(event)
        return event
