"""Computational neuron with biological Drosophila compartments and Leaky-Integrate-and-Fire dynamics.

Includes biological stochasticity:
- Ion channel noise (Gaussian perturbation on each integration step)
- Spontaneous vesicle release probability
- Stochastic threshold jitter (models variable spike initiation zone)

These ensure that identical inputs never produce identical outputs,
matching the inherent noise in real neural systems.
"""

import random
import time
from dataclasses import dataclass, field


# Global RNG seeded from system time for stochastic neural behavior
_NEURAL_RNG = random.Random(time.time_ns())


def reseed_neural_rng(seed: int | None = None) -> None:
    """Re-seed the neural noise RNG. None = time-based (non-deterministic)."""
    global _NEURAL_RNG
    _NEURAL_RNG = random.Random(seed if seed is not None else time.time_ns())


@dataclass
class Neuron:
    neuron_id: int
    kind: str = "internal"  # sensory | internal | decision_buy | decision_hold | decision_sell
    cluster: str = "central_complex"  # optic_lobe | antennal_lobe | mushroom_body | central_complex | motor_output
    activation: float = 0.0
    threshold: float = 1.0
    bias: float = 0.0
    decay: float = 0.7
    refractory_ticks: int = 1
    last_activation: int = -100
    activity_history: list[float] = field(default_factory=list)
    importance: float = 0.0
    reward_association: float = 0.0  # Mushroom Body: accumulated reward association
    fired: bool = False
    pruned: bool = False

    # Biological noise parameters
    noise_amplitude: float = 0.05      # σ of Gaussian ion channel noise
    spontaneous_rate: float = 0.003    # Probability of spontaneous firing per tick
    threshold_jitter: float = 0.02     # σ of threshold variation per tick

    def integrate(self, input_sum: float, tick: int) -> None:
        """Leaky-integrate-and-fire with biological stochasticity."""
        if self.pruned:
            self.fired = False
            return

        # Refractory period: cannot fire immediately after firing
        if tick - self.last_activation <= self.refractory_ticks:
            self.activation *= 0.3
            self.fired = False
            return

        # Ion channel noise: Gaussian perturbation on membrane potential
        noise = _NEURAL_RNG.gauss(0.0, self.noise_amplitude)

        # Leaky integration with noise
        self.activation = self.activation * self.decay + input_sum + self.bias + noise

        # Stochastic threshold: jitters around base threshold each tick
        effective_threshold = self.threshold + _NEURAL_RNG.gauss(0.0, self.threshold_jitter)

        # Spontaneous vesicle release: small probability of firing with no input
        spontaneous = _NEURAL_RNG.random() < self.spontaneous_rate and input_sum < 0.01

        self.fired = self.activation >= effective_threshold or spontaneous
        if self.fired:
            self.activation = 0.0
            self.last_activation = tick
            self.importance += 0.01

        self.activity_history.append(self.activation)
        if len(self.activity_history) > 256:
            self.activity_history.pop(0)

    @property
    def output(self) -> float:
        return 1.0 if self.fired else 0.0
