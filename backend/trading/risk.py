"""Position sizing and exposure guardrails (simulation only)."""


def position_size(capital: float, risk_fraction: float) -> float:
    return capital * max(0.0, min(1.0, risk_fraction))
