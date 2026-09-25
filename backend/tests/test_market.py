import pytest

from market.data_loader import load_csv
from market.environment import Environment
from market.features import features


def _write(tmp_path, rows):
    p = tmp_path / "x.csv"
    p.write_text("timestamp,open,high,low,close,volume\n" + "\n".join(rows))
    return str(p)


def test_loader_validates_schema(tmp_path):
    p = _write(tmp_path, [f"{1000 + i},1,1,1,1,1" for i in range(5)])
    assert len(load_csv(p)) == 5
    bad = tmp_path / "bad.csv"
    bad.write_text("timestamp,open,close\n1000,1,1\n")
    with pytest.raises(ValueError):
        load_csv(str(bad))


def test_environment_roundtrip():
    from market.data_loader import Candle
    env = Environment(10000, 5, 5)
    c1 = Candle(1000, 100, 101, 99, 100, 10)
    c2 = Candle(1060, 100, 102, 99, 110, 10)
    env.execute("BUY", c1, 0)
    assert env.pf.position == 1
    trade = env.execute("SELL", c2, 1)
    assert trade is not None and trade.pnl > 0
    assert env.pf.position == 0


def test_features_bounded():
    from market.data_loader import Candle
    hist = [Candle(i, 100, 100, 100, 100 + (i % 5), 10) for i in range(30)]
    f = features(hist)
    assert all(-1.0 <= v <= 1.0 for v in f.values())
