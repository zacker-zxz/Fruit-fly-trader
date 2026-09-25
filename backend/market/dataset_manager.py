"""Dataset manager for multiple financial markets and replay slicing.

Provides pre-loaded and auto-generated OHLCV market datasets for:
- Crypto: BTC/USDT, ETH/USDT, SOL/USDT
- Indian Markets: NIFTY 50, BANKNIFTY, RELIANCE
- Forex/Commodities: USD/INR, GOLD/INR

Supports filtering by start date, time offsets, and inspecting dataset metadata.
"""

import csv
import math
import os
import random
import time
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from .data_loader import Candle, load_csv

DATA_RAW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw"))


@dataclass
class MarketMeta:
    symbol: str
    name: str
    asset_class: str  # crypto, indian_equity, commodity, forex
    currency: str     # INR or USD
    timeframe: str
    base_price: float
    volatility: float
    tick_size: float


AVAILABLE_MARKETS: dict[str, MarketMeta] = {
    "BTC_USDT_1m": MarketMeta("BTC/USDT", "Bitcoin Perpetual (1m)", "crypto", "USD", "1m", 64500.0, 0.0035, 0.5),
    "BTC_USDT_1h": MarketMeta("BTC/USDT", "Bitcoin Spot (1h)", "crypto", "USD", "1h", 62000.0, 0.012, 1.0),
    "ETH_USDT_5m": MarketMeta("ETH/USDT", "Ethereum (5m)", "crypto", "USD", "5m", 3450.0, 0.0045, 0.1),
    "SOL_USDT_5m": MarketMeta("SOL/USDT", "Solana Fast Micro (5m)", "crypto", "USD", "5m", 152.0, 0.007, 0.05),
    "NIFTY50_5m": MarketMeta("NIFTY 50", "NSE Nifty 50 Index (5m)", "indian_equity", "INR", "5m", 24850.0, 0.0025, 0.05),
    "NIFTY50_1d": MarketMeta("NIFTY 50", "NSE Nifty 50 Daily (1d)", "indian_equity", "INR", "1d", 24000.0, 0.008, 0.05),
    "BANKNIFTY_5m": MarketMeta("BANKNIFTY", "NSE Bank Nifty Index (5m)", "indian_equity", "INR", "5m", 51200.0, 0.004, 0.1),
    "RELIANCE_5m": MarketMeta("RELIANCE", "Reliance Industries (5m)", "indian_equity", "INR", "5m", 2980.0, 0.003, 0.05),
    "GOLD_INR_1h": MarketMeta("GOLD/INR", "MCX Gold 10g (1h)", "commodity", "INR", "1h", 74200.0, 0.003, 1.0),
    "USD_INR_1h": MarketMeta("USD/INR", "US Dollar to Indian Rupee (1h)", "forex", "INR", "1h", 83.75, 0.0015, 0.0025),
}


def ensure_datasets_exist():
    """Generates rich sample datasets if not already present."""
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    for key, meta in AVAILABLE_MARKETS.items():
        filename = f"{key}.csv"
        filepath = os.path.join(DATA_RAW_DIR, filename)
        if not os.path.exists(filepath):
            generate_synthetic_ohlcv(filepath, meta, num_candles=2500)


def generate_synthetic_ohlcv(filepath: str, meta: MarketMeta, num_candles: int = 2500):
    """Generates a realistic continuous geometric Brownian motion with regime switching."""
    rng = random.Random(hash(meta.symbol) ^ 42)
    now = datetime(2024, 6, 1, 9, 30, tzinfo=timezone.utc)
    
    interval_delta = {
        "1m": timedelta(minutes=1),
        "5m": timedelta(minutes=5),
        "1h": timedelta(hours=1),
        "1d": timedelta(days=1),
    }.get(meta.timeframe, timedelta(minutes=5))

    price = meta.base_price
    rows = []
    
    # Trend regimes: alternating bull, bear, and consolidation cycles
    regimes = [0.0002, -0.00018, 0.0, 0.00035, -0.00025, 0.0001]
    regime_idx = 0
    regime_timer = 0

    for i in range(num_candles):
        regime_timer += 1
        if regime_timer > rng.randint(80, 240):
            regime_idx = (regime_idx + 1) % len(regimes)
            regime_timer = 0

        drift = regimes[regime_idx]
        shock = rng.gauss(0, meta.volatility)
        pct_change = drift + shock
        
        open_p = price
        close_p = max(meta.tick_size, open_p * (1.0 + pct_change))
        high_p = max(open_p, close_p) * (1.0 + abs(rng.gauss(0, meta.volatility * 0.5)))
        low_p = min(open_p, close_p) * (1.0 - abs(rng.gauss(0, meta.volatility * 0.5)))
        high_p = max(high_p, open_p, close_p)
        low_p = min(low_p, open_p, close_p)

        volume = abs(rng.gauss(1000, 400)) * (1.0 + abs(pct_change) * 40)
        ts = int(now.timestamp())

        rows.append({
            "timestamp": ts,
            "open": round(open_p, 4 if meta.base_price < 100 else 2),
            "high": round(high_p, 4 if meta.base_price < 100 else 2),
            "low": round(low_p, 4 if meta.base_price < 100 else 2),
            "close": round(close_p, 4 if meta.base_price < 100 else 2),
            "volume": round(volume, 2),
        })
        price = close_p
        now += interval_delta

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)


def get_available_datasets_info() -> list[dict]:
    """Returns detailed catalog of available markets with date ranges and candle counts."""
    ensure_datasets_exist()
    res = []
    for f in sorted(os.listdir(DATA_RAW_DIR)):
        if not f.lower().endswith(".csv"):
            continue
        stem = f[:-4]
        meta = AVAILABLE_MARKETS.get(stem)
        filepath = os.path.join(DATA_RAW_DIR, f)
        
        # Quick read of first and last row
        start_ts = 0.0
        end_ts = 0.0
        row_count = 0
        latest_price = 0.0
        
        try:
            with open(filepath, newline="") as fp:
                reader = csv.DictReader(fp)
                first = next(reader, None)
                if first:
                    start_ts = float(first["timestamp"])
                    latest_price = float(first["close"])
                    row_count = 1
                    for r in reader:
                        row_count += 1
                        end_ts = float(r["timestamp"])
                        latest_price = float(r["close"])
        except Exception:
            pass

        start_dt = datetime.fromtimestamp(start_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M") if start_ts else "—"
        end_dt = datetime.fromtimestamp(end_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M") if end_ts else "—"

        res.append({
            "id": f,
            "stem": stem,
            "name": meta.name if meta else f,
            "symbol": meta.symbol if meta else f.replace(".csv", ""),
            "asset_class": meta.asset_class if meta else "general",
            "currency": meta.currency if meta else "USD",
            "timeframe": meta.timeframe if meta else "1h",
            "candle_count": row_count,
            "start_dt": start_dt,
            "end_dt": end_dt,
            "start_ts": start_ts,
            "end_ts": end_ts,
            "latest_price": latest_price,
        })
    return res


def load_candles_with_offset(dataset: str, start_time: float | None = None) -> list[Candle]:
    """Loads candles and optionally slices from a chosen start timestamp."""
    path = os.path.join(DATA_RAW_DIR, dataset)
    if not os.path.exists(path):
        ensure_datasets_exist()
    candles = load_csv(path)
    if start_time is not None and start_time > 0:
        # Find index >= start_time
        idx = next((i for i, c in enumerate(candles) if c.ts >= start_time), 0)
        # Keep at least 25 candles before start_time for feature warmup if possible
        warmup_idx = max(0, idx - 25)
        return candles[warmup_idx:]
    return candles
