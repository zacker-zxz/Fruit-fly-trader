"""Performance metrics computed from an equity curve and trade list."""

import math


def metrics(equity_curve: list[float], trades: list, periods_per_year: float = 8760.0) -> dict:
    if not equity_curve:
        return {}
    initial = equity_curve[0]
    final = equity_curve[-1]
    rets = [equity_curve[i] / equity_curve[i - 1] - 1 for i in range(1, len(equity_curve)) if equity_curve[i - 1] > 0]
    total_return = final / initial - 1 if initial else 0.0
    mean = sum(rets) / len(rets) if rets else 0.0
    var = sum((r - mean) ** 2 for r in rets) / len(rets) if rets else 0.0
    std = math.sqrt(var)
    sharpe = (mean / std) * math.sqrt(periods_per_year) if std > 0 else 0.0
    wins = [t for t in trades if t.pnl > 0]
    gross_win = sum(t.pnl for t in wins)
    gross_loss = abs(sum(t.pnl for t in trades if t.pnl <= 0))
    return {
        "total_return": round(total_return, 4),
        "sharpe": round(sharpe, 3),
        "max_drawdown": round(1 - min(equity_curve) / max(equity_curve), 4) if equity_curve and max(equity_curve) > 0 else 0.0,
        "win_rate": round(len(wins) / len(trades), 4) if trades else 0.0,
        "profit_factor": round(gross_win / gross_loss, 3) if gross_loss > 0 else (float("inf") if gross_win > 0 else 0.0),
        "n_trades": len(trades),
        "final_equity": round(final, 2),
    }
