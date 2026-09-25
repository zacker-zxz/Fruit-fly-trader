"""Computational neuron with biological Drosophila compartments and Leaky-Integrate-and-Fire dynamics."""

from dataclasses import dataclass, field


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
    reward_association: float = 0.0
    fired: bool = False
    pruned: bool = False

    def integrate(self, input_sum: float, tick: int) -> None:
        if self.pruned:
            self.fired = False
            return

        # Refractory period: cannot fire immediately after firing
        if tick - self.last_activation <= self.refractory_ticks:
            self.activation *= 0.3
            self.fired = False
            return

        self.activation = self.activation * self.decay + input_sum + self.bias
        self.fired = self.activation >= self.threshold
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
