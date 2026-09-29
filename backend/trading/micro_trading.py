"""High-frequency micro-trading engine with INR wallet and multiplier leverage.

Executes rapid UP / DOWN directional micro-trades based on Drosophila connectome commands.
Features:
- Dual INR (₹) and USD ($) wallet accounting with live exchange conversion.
- Configurable leverage / multiplier (1x, 2x, 5x, 10x, 20x, 50x).
- Micro-horizon holding: books profit instantly on take-profit (+1.2% * multiplier),
  reversal signal, or timeout expiry (3-12 ticks).
- Real-time mark-to-market valuation, fees, slippage, and performance analytics.
"""

from dataclasses import dataclass, field
import time
from market.data_loader import Candle

DEFAULT_USD_INR_RATE = 83.75
USD_INR_RATE = DEFAULT_USD_INR_RATE  # Backward compatibility alias


@dataclass
class MicroTrade:
    trade_id: int
    entry_tick: int
    entry_ts: float
    side: str           # "UP" (Long/Call) or "DOWN" (Short/Put)
    entry_price: float
    stake_inr: float    # Capital committed in INR
    multiplier: int     # 1x, 5x, 10x, etc.
    max_hold_ticks: int = 8
    exit_tick: int = 0
    exit_ts: float = 0.0
    exit_price: float = 0.0
    exit_reason: str = "OPEN"  # OPEN, PROFIT_BOOKED, STOPPED_OUT, EXPIRED, BRAIN_REVERSAL
    pnl_inr: float = 0.0
    pnl_pct: float = 0.0
    status: str = "OPEN"       # OPEN or CLOSED

    @property
    def notional_inr(self) -> float:
        return self.stake_inr * self.multiplier


class MicroTradingEngine:
    def __init__(
        self,
        initial_capital_inr: float = 500000.0,
        currency: str = "INR",
        default_multiplier: int = 10,
        stake_pct: float = 0.05,
        fee_bps: float = 4.0,
        slippage_bps: float = 3.0,
        take_profit_pct: float = 0.015,
        stop_loss_pct: float = 0.010,
        max_hold_ticks: int = 8,
        market_currency: str = "USD",
        usd_inr_rate: float = DEFAULT_USD_INR_RATE,
        max_concurrent_trades: int = 3,
        hold_ticks_min: int = 5,
        hold_ticks_max: int = 60,
    ):
        self.currency = currency
        self.initial_capital_inr = initial_capital_inr
        self.balance_inr = initial_capital_inr
        self.default_multiplier = default_multiplier
        self.stake_pct = stake_pct
        self.fee_bps = fee_bps
        self.slippage_bps = slippage_bps
        self.take_profit_pct = take_profit_pct
        self.stop_loss_pct = stop_loss_pct
        self.max_hold_ticks = max_hold_ticks
        self.max_concurrent_trades = max(1, max_concurrent_trades)
        self.hold_ticks_min = hold_ticks_min
        self.hold_ticks_max = hold_ticks_max
        self.market_currency = market_currency
        self.usd_inr_rate = max(1.0, float(usd_inr_rate))
        
        self.open_trades: list[MicroTrade] = []
        self.closed_trades: list[MicroTrade] = []
        self.trade_counter = 0
        self.peak_equity_inr = initial_capital_inr
        self.max_drawdown_pct = 0.0
        self.equity_history_inr: list[float] = [initial_capital_inr]
        self.realized_pnl_inr = 0.0

    def reset(self, initial_capital_inr: float | None = None) -> None:
        """Full reset of trading engine and wallet."""
        cap = initial_capital_inr or self.initial_capital_inr
        self.initial_capital_inr = cap
        self.balance_inr = cap
        self.realized_pnl_inr = 0.0
        self.open_trades.clear()
        self.closed_trades.clear()
        self.trade_counter = 0
        self.peak_equity_inr = cap
        self.max_drawdown_pct = 0.0
        self.equity_history_inr = [cap]

    def set_multiplier(self, mult: int) -> None:
        self.default_multiplier = max(1, min(100, mult))

    def set_usd_inr_rate(self, rate: float) -> None:
        """Dynamically update the USD/INR conversion rate."""
        if rate and rate > 0:
            self.usd_inr_rate = float(rate)

    def update_mark(self, candle: Candle, tick: int, brain_state: dict | None = None) -> list[MicroTrade]:
        """Mark open positions to current price; trigger automatic take-profit / stop-loss / brain exits."""
        newly_closed = []
        cost_rate = (self.fee_bps + self.slippage_bps) / 10000.0

        b_state = brain_state or {}
        decision = b_state.get("decision")
        cortisol = b_state.get("cortisol", 0.2)
        dopamine = b_state.get("dopamine", 0.5)

        for trade in list(self.open_trades):
            raw_ret = (candle.close - trade.entry_price) / trade.entry_price
            dir_ret = raw_ret if trade.side == "UP" else -raw_ret
            net_ret = (dir_ret * trade.multiplier) - cost_rate

            duration = tick - trade.entry_tick
            
            should_close = False
            reason = "OPEN"

            # 1. Active Brain Reversal (Fly changes direction based on visual/cognitive shift)
            if (trade.side == "UP" and decision == "SELL") or (trade.side == "DOWN" and decision == "BUY"):
                should_close = True
                reason = "BRAIN_REVERSAL"
            # 2. Cortisol Spike (Aversive stress reflex / risk aversion after drawdown)
            elif cortisol > 0.45 and net_ret < -0.003:
                should_close = True
                reason = "CORTISOL_DEFENSE"
            # 3. Dopamine Satisfaction (Fly secures positive reward surge)
            elif dopamine > 0.65 and net_ret >= 0.008:
                should_close = True
                reason = "DOPAMINE_SATISFACTION"
            # 4. Take Profit booked
            elif net_ret >= self.take_profit_pct * trade.multiplier:
                should_close = True
                reason = "PROFIT_BOOKED"
            # 5. Stop Loss
            elif net_ret <= -self.stop_loss_pct * trade.multiplier:
                should_close = True
                reason = "STOPPED_OUT"
            # 6. Brain Stochastic Hold Horizon Expiry (5s to 50s random window)
            elif duration >= trade.max_hold_ticks:
                should_close = True
                reason = "EXPIRED"

            if should_close:
                closed = self._close_trade(trade, candle, tick, reason, net_ret)
                newly_closed.append(closed)

        # Update equity curve
        current_eq = self.get_wallet_summary(candle.close)["equity_inr"]
        self.equity_history_inr.append(current_eq)
        self.peak_equity_inr = max(self.peak_equity_inr, current_eq)
        dd = (self.peak_equity_inr - current_eq) / self.peak_equity_inr if self.peak_equity_inr > 0 else 0.0
        self.max_drawdown_pct = max(self.max_drawdown_pct, dd)

        return newly_closed

    def execute_brain_signal(self, action: str, candle: Candle, tick: int, multiplier: int | None = None) -> MicroTrade | None:
        """Process brain directional decision ('BUY' = UP, 'SELL' = DOWN, 'HOLD' = Maintain).
        
        Supports multiple concurrent positions (up to max_concurrent_trades).
        Each trade gets a stochastic hold duration modeling the brain's variable attention span.
        """
        mult = multiplier or self.default_multiplier
        side = "UP" if action == "BUY" else ("DOWN" if action == "SELL" else None)
        if not side:
            return None

        # Don't open duplicate same-direction trades within 3 ticks of each other
        for t in self.open_trades:
            if t.side == side and (tick - t.entry_tick) < 3:
                return None

        # Enforce max concurrent trade limit
        if len(self.open_trades) >= self.max_concurrent_trades:
            return None

        # Calculate stake from available capital (stake_pct of available equity)
        used_margin = sum(t.stake_inr for t in self.open_trades)
        available = max(0.0, self.balance_inr - used_margin)
        stake = max(1000.0, available * self.stake_pct)
        if stake > available or available < 1000.0:
            return None

        # Apply slippage on entry
        cost = (self.fee_bps + self.slippage_bps) / 10000.0
        entry_px = candle.close * (1.0 + cost) if side == "UP" else candle.close * (1.0 - cost)

        # Brain-directed stochastic hold duration
        # Models biological variability in the fly's attention span for each trade
        import random
        hold_ticks = random.randint(self.hold_ticks_min, self.hold_ticks_max)

        self.trade_counter += 1
        trade = MicroTrade(
            trade_id=self.trade_counter,
            entry_tick=tick,
            entry_ts=candle.ts,
            side=side,
            entry_price=entry_px,
            stake_inr=round(stake, 2),
            multiplier=mult,
            max_hold_ticks=hold_ticks,
        )
        self.open_trades.append(trade)
        return trade

    def manual_close_all(self, candle: Candle, tick: int) -> list[MicroTrade]:
        """Instantly book all active open trades at market."""
        closed = []
        cost_rate = (self.fee_bps + self.slippage_bps) / 10000.0
        for t in list(self.open_trades):
            raw_ret = (candle.close - t.entry_price) / t.entry_price
            dir_ret = raw_ret if t.side == "UP" else -raw_ret
            c = self._close_trade(t, candle, tick, "MANUAL_BOOK", (dir_ret * t.multiplier) - cost_rate)
            closed.append(c)
        return closed

    def _close_trade(self, trade: MicroTrade, candle: Candle, tick: int, reason: str, net_ret: float) -> MicroTrade:
        cost = (self.fee_bps + self.slippage_bps) / 10000.0
        exit_px = candle.close * (1.0 - cost) if trade.side == "UP" else candle.close * (1.0 + cost)
        
        pnl_inr = trade.stake_inr * net_ret
        trade.exit_tick = tick
        trade.exit_ts = candle.ts
        trade.exit_price = exit_px
        trade.exit_reason = reason
        trade.pnl_inr = round(pnl_inr, 2)
        trade.pnl_pct = round(net_ret * 100.0, 2)
        trade.status = "CLOSED"

        self.balance_inr += pnl_inr
        self.realized_pnl_inr += pnl_inr
        if trade in self.open_trades:
            self.open_trades.remove(trade)
        self.closed_trades.append(trade)
        return trade

    def get_wallet_summary(self, latest_price: float = 0.0) -> dict:
        used_margin = sum(t.stake_inr for t in self.open_trades)
        available_margin = max(0.0, self.balance_inr - used_margin)
        
        # Calculate live unrealized PnL
        unrealized_pnl = 0.0
        open_trades_view = []
        cost_rate = (self.fee_bps + self.slippage_bps) / 10000.0

        for t in self.open_trades:
            px = latest_price or t.entry_price
            raw_ret = (px - t.entry_price) / t.entry_price if t.entry_price else 0.0
            dir_ret = raw_ret if t.side == "UP" else -raw_ret
            net_ret = (dir_ret * t.multiplier) - cost_rate
            u_pnl = t.stake_inr * net_ret
            unrealized_pnl += u_pnl
            open_trades_view.append({
                "trade_id": t.trade_id,
                "side": t.side,
                "multiplier": t.multiplier,
                "entry_price": t.entry_price,
                "current_price": px,
                "stake_inr": t.stake_inr,
                "unrealized_pnl_inr": round(u_pnl, 2),
                "pnl_pct": round(net_ret * 100.0, 2),
                "entry_tick": t.entry_tick,
                "max_hold_ticks": t.max_hold_ticks,
            })

        total_equity = self.balance_inr + unrealized_pnl
        total_pnl = self.realized_pnl_inr + unrealized_pnl
        total_roi_pct = (total_pnl / self.initial_capital_inr) * 100.0 if self.initial_capital_inr else 0.0

        wins = sum(1 for t in self.closed_trades if t.pnl_inr > 0)
        losses = sum(1 for t in self.closed_trades if t.pnl_inr < 0)
        win_rate = (wins / len(self.closed_trades) * 100.0) if self.closed_trades else 0.0

        gross_profit = sum(t.pnl_inr for t in self.closed_trades if t.pnl_inr > 0)
        gross_loss = abs(sum(t.pnl_inr for t in self.closed_trades if t.pnl_inr < 0))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 1.0)

        return {
            "currency": self.currency,
            "currency_symbol": "₹" if self.currency == "INR" else "$",
            "usd_inr_rate": round(self.usd_inr_rate, 4),
            "initial_capital_inr": round(self.initial_capital_inr, 2),
            "balance_inr": round(self.balance_inr, 2),
            "used_margin_inr": round(used_margin, 2),
            "available_margin_inr": round(available_margin, 2),
            "equity_inr": round(total_equity, 2),
            "equity_usd": round(total_equity / self.usd_inr_rate, 2),
            "realized_pnl_inr": round(self.realized_pnl_inr, 2),
            "unrealized_pnl_inr": round(unrealized_pnl, 2),
            "total_pnl_inr": round(total_pnl, 2),
            "total_pnl_usd": round(total_pnl / self.usd_inr_rate, 2),
            "roi_pct": round(total_roi_pct, 2),
            "total_trades": len(self.closed_trades),
            "win_trades": wins,
            "loss_trades": losses,
            "win_rate_pct": round(win_rate, 1),
            "profit_factor": round(profit_factor, 2),
            "max_drawdown_pct": round(self.max_drawdown_pct * 100.0, 2),
            "open_trades": open_trades_view,
            "recent_trades": [
                {
                    "trade_id": t.trade_id,
                    "side": t.side,
                    "multiplier": t.multiplier,
                    "entry_price": t.entry_price,
                    "exit_price": t.exit_price,
                    "stake_inr": t.stake_inr,
                    "pnl_inr": t.pnl_inr,
                    "pnl_pct": t.pnl_pct,
                    "exit_reason": t.exit_reason,
                    "entry_ts": t.entry_ts,
                    "exit_ts": t.exit_ts,
                }
                for t in self.closed_trades[-25:][::-1]
            ]
        }
