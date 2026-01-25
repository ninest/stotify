"""Backtesting utilities for strategy visualization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from stotify.stock import get_history

ExitMode = Literal["fixed", "cross"]


@dataclass(frozen=True)
class Trade:
    """A single simulated trade."""

    entry_date: pd.Timestamp
    entry_price: float
    exit_date: pd.Timestamp
    exit_price: float
    return_pct: float
    hold_days: int


@dataclass(frozen=True)
class BacktestResult:
    """Backtest output with trades and summary metrics."""

    history: pd.DataFrame
    trades: list[Trade]
    metrics: dict[str, float]


def backtest_ma_cross(
    ticker: str,
    *,
    start: str | None = None,
    end: str | None = None,
    fast_window: int = 50,
    slow_window: int = 200,
    interval: str = "1d",
    exit_mode: ExitMode = "fixed",
    hold_days: int = 30,
    period: str = "5y",
) -> BacktestResult:
    """Backtest a simple moving average crossover strategy."""
    history = get_history(
        ticker,
        period=period,
        interval=interval,
        start=start,
        end=end,
    )
    if history is None or history.empty:
        return BacktestResult(history=pd.DataFrame(), trades=[], metrics={})

    closes = history["Close"].dropna()
    history = history.loc[closes.index].copy()
    history["fast_ma"] = closes.rolling(window=fast_window).mean()
    history["slow_ma"] = closes.rolling(window=slow_window).mean()

    signal = history["fast_ma"] > history["slow_ma"]
    cross_up = signal & ~signal.shift(1, fill_value=False)
    cross_down = ~signal & signal.shift(1, fill_value=False)

    trades: list[Trade] = []
    index = history.index

    entry_dates = index[cross_up.fillna(False)]
    for entry_date in entry_dates:
        entry_pos = index.get_loc(entry_date)
        entry_price = float(history.at[entry_date, "Close"])

        if exit_mode == "cross":
            future_cross = cross_down.iloc[entry_pos + 1 :]
            if future_cross.any():
                exit_pos = future_cross.idxmax()
                exit_date = exit_pos
                exit_index_pos = index.get_loc(exit_date)
            else:
                exit_index_pos = len(index) - 1
                exit_date = index[exit_index_pos]
        else:
            exit_index_pos = min(entry_pos + hold_days, len(index) - 1)
            exit_date = index[exit_index_pos]

        exit_price = float(history.at[exit_date, "Close"])
        return_pct = ((exit_price - entry_price) / entry_price) * 100
        hold_length = exit_index_pos - entry_pos

        trades.append(
            Trade(
                entry_date=entry_date,
                entry_price=entry_price,
                exit_date=exit_date,
                exit_price=exit_price,
                return_pct=return_pct,
                hold_days=hold_length,
            )
        )

    metrics = _summarize_trades(trades)
    return BacktestResult(history=history, trades=trades, metrics=metrics)


def _summarize_trades(trades: list[Trade]) -> dict[str, float]:
    if not trades:
        return {}

    returns = [trade.return_pct for trade in trades]
    wins = [ret for ret in returns if ret > 0]
    total_return = 1.0
    for ret in returns:
        total_return *= 1 + (ret / 100)
    total_return_pct = (total_return - 1) * 100

    return {
        "total_trades": float(len(trades)),
        "win_rate": (len(wins) / len(returns)) * 100,
        "avg_return": sum(returns) / len(returns),
        "total_return": total_return_pct,
    }
