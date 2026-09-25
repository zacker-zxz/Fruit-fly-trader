"""Feature extraction -> sensory signals in [-1, 1]."""

from .data_loader import Candle


def features(history: list[Candle]) -> dict[str, float]:
    if len(history) < 21:
        return {k: 0.0 for k in ("price_change", "volume", "momentum", "volatility", "trend")}
    c = history[-1]
    prev = history[-2]
    closes = [x.close for x in history]
    vols = [x.volume for x in history]

    ret = (c.close - prev.close) / prev.close if prev.close else 0.0
    price_change = max(-1.0, min(1.0, ret * 50))

    vol_ma = sum(vols[-20:]) / 20
    volume = max(-1.0, min(1.0, (c.volume - vol_ma) / (vol_ma or 1.0)))

    momentum = max(-1.0, min(1.0, (closes[-1] - closes[-10]) / (closes[-10] or 1.0) * 20))

    rets = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(max(1, len(closes) - 20), len(closes)) if closes[i - 1]]
    mean_ret = sum(rets) / len(rets) if rets else 0.0
    var = sum((r - mean_ret) ** 2 for r in rets) / len(rets) if rets else 0.0
    volatility = max(0.0, min(1.0, (var ** 0.5) * 100))

    ma20 = sum(closes[-20:]) / 20
    trend = max(-1.0, min(1.0, (c.close - ma20) / (ma20 or 1.0) * 30))

    return {"price_change": price_change, "volume": volume, "momentum": momentum,
            "volatility": volatility, "trend": trend}
