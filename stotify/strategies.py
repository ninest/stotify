"""Strategy evaluation for stock alerts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from stotify.stock import get_history, get_price


@dataclass(frozen=True)
class StrategySignal:
    """A signal produced by a strategy evaluation."""

    ticker: str
    price: float
    alert_type: str | None
    threshold: float | None
    message: str | None = None


StrategyFn = Callable[[list[str], dict], list[StrategySignal]]

STRATEGIES: dict[str, StrategyFn] = {}


def register_strategy(name: str) -> Callable[[StrategyFn], StrategyFn]:
    """Register a strategy function by name."""

    def decorator(func: StrategyFn) -> StrategyFn:
        STRATEGIES[name] = func
        return func

    return decorator


def get_strategy(name: str) -> StrategyFn:
    """Return a strategy function by name."""
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy '{name}'")
    return STRATEGIES[name]


@register_strategy("threshold")
def threshold_strategy(tickers: list[str], params: dict) -> list[StrategySignal]:
    """Trigger when price crosses high/low thresholds."""
    signals: list[StrategySignal] = []
    high = params.get("high")
    low = params.get("low")

    for ticker in tickers:
        price = get_price(ticker)
        if price is None:
            continue

        if high is not None and price >= high:
            signals.append(
                StrategySignal(
                    ticker=ticker,
                    price=price,
                    alert_type="high",
                    threshold=float(high),
                )
            )

        if low is not None and price <= low:
            signals.append(
                StrategySignal(
                    ticker=ticker,
                    price=price,
                    alert_type="low",
                    threshold=float(low),
                )
            )

    return signals


@register_strategy("ma_cross")
def moving_average_cross_strategy(tickers: list[str], params: dict) -> list[StrategySignal]:
    """Trigger when a fast moving average is above a slow moving average."""
    signals: list[StrategySignal] = []
    fast_window = int(params["fast_window"])
    slow_window = int(params["slow_window"])
    period = params.get("period", "1y")
    interval = params.get("interval", "1d")

    for ticker in tickers:
        history = get_history(ticker, period=period, interval=interval)
        if history is None or history.empty:
            continue

        closes = history["Close"].dropna()
        if len(closes) < slow_window:
            continue

        fast_ma = closes.rolling(window=fast_window).mean().iloc[-1]
        slow_ma = closes.rolling(window=slow_window).mean().iloc[-1]
        if fast_ma is None or slow_ma is None:
            continue
        if fast_ma != fast_ma or slow_ma != slow_ma:
            continue

        if fast_ma > slow_ma:
            price = float(closes.iloc[-1])
            message = (
                f"{ticker} {fast_window}d MA (${fast_ma:.2f}) "
                f"above {slow_window}d MA (${slow_ma:.2f})"
            )
            signals.append(
                StrategySignal(
                    ticker=ticker,
                    price=price,
                    alert_type="ma_cross",
                    threshold=None,
                    message=message,
                )
            )

    return signals
