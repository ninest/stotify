"""Tests for strategy implementations."""

from unittest.mock import patch

import pandas as pd

from stotify.strategies import moving_average_cross_strategy, threshold_strategy


def test_threshold_strategy_triggers_for_multiple_tickers():
    """Threshold strategy should emit signals per ticker."""
    with patch("stotify.strategies.get_price", return_value=260.0):
        signals = threshold_strategy(["AAPL", "MSFT"], {"high": 250})

    assert len(signals) == 2
    tickers = {signal.ticker for signal in signals}
    assert tickers == {"AAPL", "MSFT"}


def test_moving_average_cross_strategy_triggers_when_fast_above_slow():
    """MA cross strategy should emit signal when fast MA is above slow MA."""
    history = pd.DataFrame({"Close": [1.0, 2.0, 3.0]})

    with patch("stotify.strategies.get_history", return_value=history):
        signals = moving_average_cross_strategy(
            ["AAPL"],
            {"fast_window": 2, "slow_window": 3, "period": "1mo", "interval": "1d"},
        )

    assert len(signals) == 1
    signal = signals[0]
    assert signal.ticker == "AAPL"
    assert "MA" in signal.message
