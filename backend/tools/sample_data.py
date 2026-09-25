"""Generate synthetic-but-deterministic sample OHLCV CSVs (BTC-like 24h, NIFTY-like equity session).

Real datasets are dropped into data/raw/ manually; these generators exist so the
system runs end-to-end without any external dependency.
"""

import csv
import math
import os
import random

RAW = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")


def gen(path: str, start_price: float, n: int, interval_sec: int, vol: float, seed: int, drift: float = 0.0):
    rng = random.Random(seed)
    price = start_price
    t0 = 1700000000
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        for i in range(n):
            shock = rng.gauss(drift, vol)
            o = price
            c = max(0.01, price * (1 + shock))
            hi = max(o, c) * (1 + abs(rng.gauss(0, vol / 2)))
            lo = min(o, c) * (1 - abs(rng.gauss(0, vol / 2)))
            v = abs(rng.gauss(1.0, 0.3)) * 1000
            w.writerow([t0 + i * interval_sec, round(o, 2), round(hi, 2), round(lo, 2), round(c, 2), round(v, 2)])
            price = c


if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    gen(os.path.join(RAW, "BTCUSDT_1h_sample.csv"), 42000, 3000, 3600, 0.004, seed=11)
    gen(os.path.join(RAW, "NIFTY50_1d_sample.csv"), 19500, 1500, 86400, 0.006, seed=23)
    print("sample datasets written to data/raw/")
