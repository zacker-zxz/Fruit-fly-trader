"""Synaptic connection with plasticity bookkeeping."""

from dataclasses import dataclass, field


@dataclass
class Synapse:
    synapse_id: int
    source: int
    target: int
    weight: float
    strength: float = 0.5
    activity_count: int = 0
    successful_contribution: float = 0.0
    failure_contribution: float = 0.0
    last_used: int = -1
    eligibility: float = 0.0
    pruned: bool = False

    def touch(self, tick: int) -> None:
        self.activity_count += 1
        self.last_used = tick
        self.eligibility = min(1.0, self.eligibility + 1.0)
