import os

from engine.activity import Brain
from engine.connectome import Connectome, Edge, sample
from engine.neuromodulation import compute_reward
from engine.plasticity import PlasticityEngine
from engine.pruning import PruningEngine


def _tiny_connectome() -> Connectome:
    edges = [Edge(i, (i + 1) % 50, 5) for i in range(50)] + [Edge(i, (i + 7) % 50, 2) for i in range(50)]
    return sample(edges, 50)


def test_brain_propagates_and_decides():
    brain = Brain(_tiny_connectome(), {"threshold": 0.5})
    brain.set_sensory_input({"momentum": 0.8, "trend": 0.4})
    for _ in range(5):
        brain.step()
    assert set(brain.decision_confidence) == {"BUY", "HOLD", "SELL"}
    assert abs(sum(brain.decision_confidence.values()) - 1.0) < 1e-6


def test_reward_modulation_changes_weights():
    brain = Brain(_tiny_connectome(), {"threshold": 0.5})
    p = PlasticityEngine(brain, {"learning_rate": 0.1})
    before = [s.weight for s in brain.synapses]
    brain.set_sensory_input({"momentum": 1.0})
    brain.step()
    fired = brain.active_neurons()
    assert fired, "sensory input should drive firing"
    p.hebbian_pass(fired)
    p.apply_modulation(0.8)
    assert any(a != b for a, b in zip(before, [s.weight for s in brain.synapses]))
    assert p.counts["strengthened"] + p.counts["weakened"] > 0


def test_pruning_logs_events():
    brain = Brain(_tiny_connectome(), {"threshold": 10.0})  # nothing fires
    pr = PruningEngine(brain, {"patience": 1})
    brain.step()
    events = pr.evaluate()
    assert events
    assert all(e["type"] in ("neuron_pruned", "synapse_pruned") for e in events)
    assert len(pr.ledger) == len(events)


def test_reward_formula_bounds():
    assert compute_reward(None, {}, {}) == 0.0
    r = compute_reward({"pnl_pct": 100.0}, {"drawdown": 0, "volatility": 0, "risk_taken": 0.5}, {"scale": 10})
    assert -1.0 <= r <= 1.0
