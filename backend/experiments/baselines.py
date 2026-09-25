"""Baseline strategies evaluated on the same replay environment."""

import random


def random_strategy(history, rng: random.Random) -> str:
    return rng.choice(["BUY", "HOLD", "SELL"])


def buy_and_hold(history, rng) -> str:
    if not getattr(buy_and_hold, "_entered", False):
        buy_and_hold._entered = True
        return "BUY"
    return "HOLD"


def momentum(history, rng) -> str:
    if len(history) < 11:
        return "HOLD"
    c1, c0 = history[-11].close, history[-1].close
    if c0 > c1 * 1.001:
        return "BUY"
    if c0 < c1 * 0.999:
        return "SELL"
    return "HOLD"


BASELINES = {"random": random_strategy, "buy_hold": buy_and_hold, "momentum": momentum}
