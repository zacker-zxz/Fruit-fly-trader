"""Feature extraction -> sensory signals in [-1, 1].

Provides rich market intelligence for the Drosophila connectome brain:
- Price action: immediate candle return
- Momentum: 10-candle directional strength
- Trend: price vs 20-candle moving average
- Volatility: realized vol over recent window
- Volume: relative volume vs 20-candle average
- RSI: overbought/oversold oscillator (mapped to [-1, 1])
- Candlestick patterns: engulfing, doji, hammer/shooting star
- Range position: where price sits in recent high/low range
- Support/resistance breakout proximity
- Reversal signal: momentum shift detection
"""

import math
from .data_loader import Candle


def features(history: list[Candle], trade_memory: list[dict] | None = None) -> dict[str, float]:
    """Extract rich market features from candle history.
    
    Args:
        history: Recent candle history (at least 21 candles for meaningful signals).
        trade_memory: Optional list of recent trade outcomes for Mushroom Body memory.
    
    Returns:
        Dict mapping signal names to values in [-1, 1].
    """
    base_keys = (
        "price_change", "volume", "momentum", "volatility", "trend",
        "rsi", "pattern_bullish", "pattern_bearish", "range_position",
        "breakout_signal", "reversal_signal", "memory_bias",
    )
    if len(history) < 21:
        return {k: 0.0 for k in base_keys}

    c = history[-1]
    prev = history[-2]
    closes = [x.close for x in history]
    highs = [x.high for x in history]
    lows = [x.low for x in history]
    opens = [x.open for x in history]
    vols = [x.volume for x in history]

    # ── Core signals (original) ──────────────────────────────────────
    ret = (c.close - prev.close) / prev.close if prev.close else 0.0
    price_change = _clamp(ret * 50)

    vol_ma = sum(vols[-20:]) / 20
    volume = _clamp((c.volume - vol_ma) / (vol_ma or 1.0))

    momentum = _clamp((closes[-1] - closes[-10]) / (closes[-10] or 1.0) * 20)

    rets = [
        (closes[i] - closes[i - 1]) / closes[i - 1]
        for i in range(max(1, len(closes) - 20), len(closes))
        if closes[i - 1]
    ]
    mean_ret = sum(rets) / len(rets) if rets else 0.0
    var = sum((r - mean_ret) ** 2 for r in rets) / len(rets) if rets else 0.0
    volatility = max(0.0, min(1.0, (var ** 0.5) * 100))

    ma20 = sum(closes[-20:]) / 20
    trend = _clamp((c.close - ma20) / (ma20 or 1.0) * 30)

    # ── RSI (14-period Wilder's) ─────────────────────────────────────
    rsi = _compute_rsi(closes, period=14)

    # ── Candlestick patterns ─────────────────────────────────────────
    pattern_bullish, pattern_bearish = _detect_candle_patterns(
        opens[-5:], highs[-5:], lows[-5:], closes[-5:]
    )

    # ── Range position: where price sits in the recent high-low range ─
    recent_high = max(highs[-20:])
    recent_low = min(lows[-20:])
    range_span = recent_high - recent_low
    if range_span > 0:
        # Maps to [-1, 1]: -1 = at recent low, +1 = at recent high
        range_position = _clamp(((c.close - recent_low) / range_span - 0.5) * 2.0)
    else:
        range_position = 0.0

    # ── Breakout / support-resistance proximity ──────────────────────
    breakout_signal = _compute_breakout(closes, highs, lows)

    # ── Momentum reversal detection ──────────────────────────────────
    reversal_signal = _compute_reversal(closes, momentum)

    # ── Memory bias from recent trade outcomes (Mushroom Body input) ─
    memory_bias = _compute_memory_bias(trade_memory)

    return {
        "price_change": price_change,
        "volume": volume,
        "momentum": momentum,
        "volatility": volatility,
        "trend": trend,
        "rsi": rsi,
        "pattern_bullish": pattern_bullish,
        "pattern_bearish": pattern_bearish,
        "range_position": range_position,
        "breakout_signal": breakout_signal,
        "reversal_signal": reversal_signal,
        "memory_bias": memory_bias,
    }


def _clamp(v: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _compute_rsi(closes: list[float], period: int = 14) -> float:
    """Relative Strength Index mapped to [-1, 1] where -1=oversold, +1=overbought."""
    if len(closes) < period + 1:
        return 0.0
    
    gains = []
    losses = []
    for i in range(-period, 0):
        delta = closes[i] - closes[i - 1]
        if delta > 0:
            gains.append(delta)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(delta))
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    if avg_loss == 0:
        rsi_raw = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi_raw = 100.0 - (100.0 / (1.0 + rs))
    
    # Map RSI [0, 100] -> [-1, 1]
    return _clamp((rsi_raw - 50.0) / 50.0)


def _detect_candle_patterns(
    opens: list[float], highs: list[float], lows: list[float], closes: list[float]
) -> tuple[float, float]:
    """Detect candlestick patterns from recent candles.
    
    Returns (bullish_signal, bearish_signal) each in [0, 1].
    """
    if len(opens) < 3:
        return 0.0, 0.0
    
    bullish = 0.0
    bearish = 0.0
    
    # Current and previous candle bodies
    body = closes[-1] - opens[-1]
    body_prev = closes[-2] - opens[-2]
    body_size = abs(body)
    body_prev_size = abs(body_prev)
    
    wick_upper = highs[-1] - max(opens[-1], closes[-1])
    wick_lower = min(opens[-1], closes[-1]) - lows[-1]
    candle_range = highs[-1] - lows[-1]
    
    if candle_range < 1e-10:
        return 0.0, 0.0
    
    # ── Bullish Engulfing ──
    if body > 0 and body_prev < 0 and body_size > body_prev_size * 0.8:
        bullish = max(bullish, 0.8)
    
    # ── Bearish Engulfing ──
    if body < 0 and body_prev > 0 and body_size > body_prev_size * 0.8:
        bearish = max(bearish, 0.8)
    
    # ── Hammer (bullish reversal at bottom) ──
    if wick_lower > body_size * 2.0 and wick_upper < body_size * 0.5:
        bullish = max(bullish, 0.6)
    
    # ── Shooting Star (bearish reversal at top) ──
    if wick_upper > body_size * 2.0 and wick_lower < body_size * 0.5:
        bearish = max(bearish, 0.6)
    
    # ── Doji (indecision) ──
    if body_size < candle_range * 0.1:
        # Doji after a run → weak reversal signal
        if body_prev > 0:
            bearish = max(bearish, 0.3)
        elif body_prev < 0:
            bullish = max(bullish, 0.3)
    
    # ── Three consecutive same-direction bodies (momentum confirmation) ──
    if len(closes) >= 3:
        b1 = closes[-3] - opens[-3]
        b2 = closes[-2] - opens[-2]
        b3 = closes[-1] - opens[-1]
        if b1 > 0 and b2 > 0 and b3 > 0:
            bullish = max(bullish, 0.5)
        elif b1 < 0 and b2 < 0 and b3 < 0:
            bearish = max(bearish, 0.5)
    
    return _clamp(bullish, 0, 1), _clamp(bearish, 0, 1)


def _compute_breakout(closes: list[float], highs: list[float], lows: list[float]) -> float:
    """Detect proximity to or breakout from support/resistance levels.
    
    Returns [-1, 1]: positive = bullish breakout, negative = bearish breakdown.
    """
    if len(closes) < 20:
        return 0.0
    
    # Use 20-candle high/low as resistance/support
    resistance = max(highs[-20:-1])  # Exclude current candle
    support = min(lows[-20:-1])
    current = closes[-1]
    span = resistance - support
    
    if span < 1e-10:
        return 0.0
    
    # Breakout above resistance
    if current > resistance:
        return _clamp((current - resistance) / span * 5.0)
    
    # Breakdown below support
    if current < support:
        return _clamp((current - support) / span * 5.0)
    
    # Proximity signal: approaching resistance or support
    dist_to_resistance = (resistance - current) / span
    dist_to_support = (current - support) / span
    
    if dist_to_resistance < 0.1:
        return 0.3  # Near resistance, potential breakout
    elif dist_to_support < 0.1:
        return -0.3  # Near support, potential breakdown
    
    return 0.0


def _compute_reversal(closes: list[float], current_momentum: float) -> float:
    """Detect momentum reversals by comparing short-term vs medium-term momentum.
    
    Returns [-1, 1]: positive = bullish reversal, negative = bearish reversal.
    """
    if len(closes) < 15:
        return 0.0
    
    # Short-term momentum (3-candle)
    short_mom = (closes[-1] - closes[-3]) / (closes[-3] or 1.0) * 20
    # Medium-term momentum (10-candle)
    med_mom = (closes[-1] - closes[-10]) / (closes[-10] or 1.0) * 20
    
    # Reversal: short-term diverges from medium-term
    # If medium momentum is negative but short-term is turning positive → bullish reversal
    if med_mom < -0.2 and short_mom > 0.1:
        return _clamp(short_mom - med_mom, 0, 1)
    # If medium momentum is positive but short-term is turning negative → bearish reversal
    elif med_mom > 0.2 and short_mom < -0.1:
        return _clamp(short_mom - med_mom, -1, 0)
    
    return 0.0


def _compute_memory_bias(trade_memory: list[dict] | None) -> float:
    """Compute associative memory bias from recent trade outcomes.
    
    Encodes whether recent trades in similar conditions were profitable.
    Returns [-1, 1]: positive = recent wins bias toward risk, negative = recent losses bias toward caution.
    """
    if not trade_memory:
        return 0.0
    
    # Weighted average of last N trade outcomes (recent trades weighted more)
    total_weight = 0.0
    weighted_pnl = 0.0
    for i, t in enumerate(trade_memory[-5:]):  # Last 5 trades
        weight = 1.0 + i * 0.5  # More recent = higher weight
        pnl = t.get("pnl_pct", 0.0) / 100.0  # Normalize
        weighted_pnl += weight * pnl
        total_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    bias = weighted_pnl / total_weight
    return _clamp(bias * 3.0)  # Scale for neural sensitivity
