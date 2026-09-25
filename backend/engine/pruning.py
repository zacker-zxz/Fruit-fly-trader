"""Structural plasticity: neuron and synapse pruning with a full ledger."""

from .activity import Brain


class PruningEngine:
    def __init__(self, brain: Brain, config: dict):
        self.brain = brain
        self.cfg = config
        self.ledger: list[dict] = []

    def evaluate(self) -> list[dict]:
        """Prune synapses then neurons that meet criteria. Returns prune events."""
        events: list[dict] = []
        min_activity = self.cfg.get("min_activity", 0.01)
        min_strength = self.cfg.get("min_strength", 0.02)
        patience = self.cfg.get("patience", 200)
        enabled = self.cfg.get("enabled", True)
        if not enabled:
            return events

        # synapses: weak and unused for `patience` ticks
        for s in self.brain.synapses:
            if s.pruned:
                continue
            if s.weight < min_strength and (self.brain.tick - s.last_used > patience if s.last_used >= 0 else self.brain.tick > patience):
                s.pruned = True
                self.brain.pruned_synapses = getattr(self.brain, "pruned_synapses", 0) + 1
                events.append({"type": "synapse_pruned", "tick": self.brain.tick,
                               "synapse_id": s.synapse_id, "weight": s.weight})

        # neurons: persistently inactive with low importance, keep sensory and decision neurons
        protected = self.brain.c.n_neurons // 20 + 3  # sensory block + decisions
        for n in self.brain.neurons:
            if n.pruned or n.neuron_id < protected:
                continue
            recent = n.activity_history[-patience:]
            mean_act = sum(recent) / len(recent) if recent else 0.0
            if mean_act < min_activity and n.importance < self.cfg.get("min_importance", 0.1):
                n.pruned = True
                self.brain.pruned_neurons = getattr(self.brain, "pruned_neurons", 0) + 1
                for s in self.brain.synapses:
                    if not s.pruned and (s.source == n.neuron_id or s.target == n.neuron_id):
                        s.pruned = True
                events.append({"type": "neuron_pruned", "tick": self.brain.tick,
                               "neuron_id": n.neuron_id, "mean_activity": mean_act})
        self.ledger.extend(events)
        return events
