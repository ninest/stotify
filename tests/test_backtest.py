import pandas as pd

from stotify.backtest import backtest_ma_cross


def make_history(close_values):
    index = pd.date_range("2021-01-01", periods=len(close_values), freq="D")
    return pd.DataFrame({"Close": close_values}, index=index)


def test_backtest_fixed_exit(monkeypatch):
    history = make_history([1, 1, 1, 2, 3, 4])

    def fake_get_history(*_args, **_kwargs):
        return history

    monkeypatch.setattr("stotify.backtest.get_history", fake_get_history)

    result = backtest_ma_cross(
        "TEST",
        fast_window=2,
        slow_window=3,
        exit_mode="fixed",
        hold_days=2,
    )

    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.entry_date == history.index[3]
    assert trade.exit_date == history.index[5]
    assert trade.return_pct == 100.0


def test_backtest_cross_exit(monkeypatch):
    history = make_history([1, 1, 1, 2, 3, 2, 1])

    def fake_get_history(*_args, **_kwargs):
        return history

    monkeypatch.setattr("stotify.backtest.get_history", fake_get_history)

    result = backtest_ma_cross(
        "TEST",
        fast_window=2,
        slow_window=3,
        exit_mode="cross",
    )

    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.entry_date == history.index[3]
    assert trade.exit_date == history.index[6]


def test_backtest_no_history(monkeypatch):
    def fake_get_history(*_args, **_kwargs):
        return None

    monkeypatch.setattr("stotify.backtest.get_history", fake_get_history)

    result = backtest_ma_cross("TEST")
    assert result.trades == []
