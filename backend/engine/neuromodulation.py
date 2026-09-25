"""Configurable risk-adjusted reward computation.

Reward is computed from realized trade outcome plus context (drawdown,
volatility, duration, risk taken). Not a literal chemical model.
"""


def compute_reward(trade: dict | None, context: dict, config: dict) -> float:
    if trade is None:
        return 0.0
    w = config.get("weights", {})
    pnl_pct = trade.get("pnl_pct", 0.0)
    drawdown = context.get("drawdown", 0.0)
    volatility = context.get("volatility", 0.0)
    duration = min(1.0, trade.get("duration_ticks", 1) / config.get("duration_norm", 50))
    risk = context.get("risk_taken", 0.5)

    r = w.get("pnl", 1.0) * pnl_pct
    r -= w.get("drawdown", 0.5) * drawdown
    r -= w.get("volatility", 0.2) * volatility
    r -= w.get("duration", 0.1) * duration
    r *= (0.5 + risk)  # reward risk-adjusted decisions, not raw gambling
    scale = config.get("scale", 10.0)
    return max(-1.0, min(1.0, r * scale))
