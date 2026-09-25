"""CSV ingestion with strict schema validation."""

import csv
import hashlib
import os
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Candle:
    ts: float
    open: float
    high: float
    low: float
    close: float
    volume: float


REQUIRED = ("timestamp", "open", "high", "low", "close", "volume")


def file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_csv(path: str) -> list[Candle]:
    candles = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{os.path.basename(path)}: missing columns {missing}")
        for i, row in enumerate(reader):
            try:
                ts = float(row["timestamp"])
                if ts > 1e12:  # epoch millis
                    ts /= 1000.0
            except ValueError:
                dt = datetime.fromisoformat(str(row["timestamp"]).replace("Z", "+00:00"))
                ts = dt.timestamp()
            candles.append(Candle(
                ts=ts,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
            ))
    if len(candles) < 2:
        raise ValueError(f"{os.path.basename(path)}: fewer than 2 rows")
    candles.sort(key=lambda c: c.ts)
    if any(candles[i].ts >= candles[i + 1].ts for i in range(len(candles) - 1)):
        raise ValueError(f"{os.path.basename(path)}: duplicate/out-of-order timestamps")
    return candles
