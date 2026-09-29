import pytest
from market.data_loader import Candle
from trading.micro_trading import MicroTradingEngine
from market.dataset_manager import get_available_datasets_info, load_candles_with_offset


def test_micro_trading_engine_inr_wallet():
    # Test manual fixed bracket take-profit (+1.5% * 10 = +15%)
    engine = MicroTradingEngine(
        initial_capital_inr=500000.0,
        default_multiplier=10,
        exit_mode="manual",
        use_manual_tp_sl=True,
    )
    c1 = Candle(ts=1000.0, open=100.0, high=105.0, low=99.0, close=100.0, volume=500.0)
    
    # Execute BUY/UP trade
    trade = engine.execute_brain_signal("BUY", c1, tick=1, multiplier=10)
    assert trade is not None
    assert trade.side == "UP"
    assert trade.multiplier == 10
    assert len(engine.open_trades) == 1
    
    # Candle moves up +2.5% -> with 10x multiplier that's +25% return, triggering take-profit
    c2 = Candle(ts=1005.0, open=100.0, high=103.0, low=100.0, close=102.5, volume=600.0)
    closed = engine.update_mark(c2, tick=2)
    assert len(closed) == 1
    assert closed[0].exit_reason == "PROFIT_BOOKED"
    assert closed[0].pnl_inr > 0
    assert engine.balance_inr > 500000.0


def test_micro_trading_auto_biological_exits():
    # Default is auto (the fly decides when to book profit and cut loss)
    engine = MicroTradingEngine(initial_capital_inr=500000.0, default_multiplier=10, exit_mode="auto")
    c1 = Candle(ts=1000.0, open=100.0, high=101.0, low=99.0, close=100.0, volume=500.0)
    
    # 1. Test Dopamine Satisfaction (Fly reward center reaches satisfaction on gain)
    engine.execute_brain_signal("BUY", c1, tick=1, multiplier=10)
    c2 = Candle(ts=1001.0, open=100.0, high=101.0, low=100.0, close=100.5, volume=500.0)
    closed = engine.update_mark(c2, tick=2, brain_state={"dopamine": 0.75, "cortisol": 0.1})
    assert len(closed) == 1
    assert closed[0].exit_reason == "DOPAMINE_SATISFACTION"

    # 2. Test Cortisol Defense (Fly stress cuts losing trade reflexively)
    engine.execute_brain_signal("BUY", c1, tick=3, multiplier=10)
    c3 = Candle(ts=1002.0, open=100.0, high=100.0, low=99.0, close=99.6, volume=500.0)
    closed = engine.update_mark(c3, tick=4, brain_state={"dopamine": 0.3, "cortisol": 0.6})
    assert len(closed) == 1
    assert closed[0].exit_reason == "CORTISOL_DEFENSE"

    # 3. Test Brain Reversal (Fly changes motor direction)
    engine.execute_brain_signal("BUY", c1, tick=5, multiplier=10)
    c4 = Candle(ts=1003.0, open=100.0, high=100.2, low=99.8, close=100.1, volume=500.0)
    closed = engine.update_mark(c4, tick=6, brain_state={"decision": "SELL"})
    assert len(closed) == 1
    assert closed[0].exit_reason == "BRAIN_REVERSAL"

    # 4. Test Trailing Profit (Locks in gains after peak profit drops)
    t = engine.execute_brain_signal("BUY", c1, tick=7, multiplier=10)
    # Peak profit candle
    c_peak = Candle(ts=1004.0, open=100.0, high=101.5, low=100.0, close=101.2, volume=500.0)
    engine.update_mark(c_peak, tick=8, brain_state={"dopamine": 0.4})
    assert t.peak_pnl_pct > 0.008
    # Retracement candle (gives back > 30% from peak)
    c_retrace = Candle(ts=1005.0, open=101.0, high=101.0, low=100.2, close=100.5, volume=500.0)
    closed = engine.update_mark(c_retrace, tick=9, brain_state={"dopamine": 0.4})
    assert len(closed) == 1
    assert closed[0].exit_reason == "TRAILING_PROFIT"


def test_micro_trading_expiry():
    engine = MicroTradingEngine(initial_capital_inr=500000.0, default_multiplier=5, max_hold_ticks=4,
                                hold_ticks_min=4, hold_ticks_max=4)
    c1 = Candle(ts=1000.0, open=100.0, high=101.0, low=99.0, close=100.0, volume=500.0)
    engine.execute_brain_signal("SELL", c1, tick=1)
    
    # Flat candles
    c_flat = Candle(ts=1010.0, open=100.0, high=100.1, low=99.9, close=100.0, volume=500.0)
    engine.update_mark(c_flat, tick=2)
    engine.update_mark(c_flat, tick=3)
    engine.update_mark(c_flat, tick=4)
    closed = engine.update_mark(c_flat, tick=5)  # 5 - 1 = 4 >= max_hold_ticks
    assert len(closed) == 1
    assert closed[0].exit_reason == "EXPIRED"


def test_dataset_manager_listing():
    markets = get_available_datasets_info()
    assert len(markets) >= 8
    symbols = [m["symbol"] for m in markets]
    assert any("BTC" in s for s in symbols)
    assert any("NIFTY" in s for s in symbols)


def test_micro_trading_manual_close():
    engine = MicroTradingEngine(initial_capital_inr=500000.0, default_multiplier=10)
    c1 = Candle(ts=1000.0, open=100.0, high=101.0, low=99.0, close=100.0, volume=500.0)
    engine.execute_brain_signal("BUY", c1, tick=1)
    assert len(engine.open_trades) == 1
    
    # Manual close at tick 2
    c2 = Candle(ts=1005.0, open=100.5, high=101.0, low=100.0, close=100.8, volume=500.0)
    closed = engine.manual_close_all(c2, tick=2)
    assert len(closed) == 1
    assert closed[0].exit_reason == "MANUAL_BOOK"
    assert len(engine.open_trades) == 0
    assert len(engine.closed_trades) == 1

