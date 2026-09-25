"""Chronological replay trading environment. No future information leaks."""

from dataclasses import dataclass, field

from .data_loader import Candle


@dataclass
class Trade:
    entry_ts: float
    exit_ts: float
    side: str
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float
    duration_ticks: int


@dataclass
class Portfolio:
    capital: float
    position: int = 0          # +1 long, -1 short, 0 flat
    entry_price: float = 0.0
    entry_ts: float = 0.0
    equity_curve: list[float] = field(default_factory=list)
    trades: list[Trade] = field(default_factory=list)
    peak_equity: float = 0.0
    max_drawdown: float = 0.0
    fees_paid: float = 0.0


class Environment:
    def __init__(self, initial_capital: float, fee_bps: float, slippage_bps: float):
        self.initial_capital = initial_capital
        self.fee_bps = fee_bps
        self.slippage_bps = slippage_bps
        self.pf = Portfolio(capital=initial_capital)

    def mark(self, candle: Candle) -> float:
        if self.pf.position == 0:
            equity = self.pf.capital
        else:
            equity = self.pf.capital + self.pf.position * (candle.close - self.pf.entry_price) / self.pf.entry_price * self.pf.capital
        self.pf.equity_curve.append(equity)
        self.pf.peak_equity = max(self.pf.peak_equity, equity)
        dd = (self.pf.peak_equity - equity) / self.pf.peak_equity if self.pf.peak_equity else 0.0
        self.pf.max_drawdown = max(self.pf.max_drawdown, dd)
        return equity

    def execute(self, action: str, candle: Candle, tick: int) -> Trade | None:
        """BUY opens long (or closes short), SELL opens short (or closes long)."""
        cost = (self.fee_bps + self.slippage_bps) / 10000.0
        px = candle.close * (1 + cost) if action == "BUY" else candle.close * (1 - cost)
        trade = None
        if action == "BUY":
            if self.pf.position == -1:
                trade = self._close(candle, tick, "long_close")
            elif self.pf.position == 0:
                self.pf.position = 1
                self.pf.entry_price = px
                self.pf.entry_ts = candle.ts
                self.pf.capital -= self.pf.capital * cost
                self.pf.fees_paid += self.pf.capital * cost
        elif action == "SELL":
            if self.pf.position == 1:
                trade = self._close(candle, tick, "short_close")
            elif self.pf.position == 0:
                self.pf.position = -1
                self.pf.entry_price = px
                self.pf.entry_ts = candle.ts
                self.pf.capital -= self.pf.capital * cost
                self.pf.fees_paid += self.pf.capital * cost
        return trade

    def _close(self, candle: Candle, tick: int, side: str) -> Trade:
        cost = (self.fee_bps + self.slippage_bps) / 10000.0
        exit_px = candle.close * (1 - cost) if self.pf.position == 1 else candle.close * (1 + cost)
        ret = self.pf.position * (exit_px - self.pf.entry_price) / self.pf.entry_price
        pnl = self.pf.capital * ret
        self.pf.capital += pnl
        self.pf.fees_paid += self.pf.capital * cost
        trade = Trade(entry_ts=self.pf.entry_ts, exit_ts=candle.ts, side=side,
                      entry_price=self.pf.entry_price, exit_price=exit_px,
                      pnl=pnl, pnl_pct=ret, duration_ticks=tick - int(self.pf.entry_ts))
        self.pf.trades.append(trade)
        self.pf.position = 0
        self.pf.entry_price = 0.0
        return trade
