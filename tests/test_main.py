"""Tests for main module."""

import json
from unittest.mock import patch

import pytest

from stotify.main import check_alerts, load_config, main


# --- Fixtures ---


@pytest.fixture
def mock_market_open():
    """Pretend market is open."""
    with patch("stotify.main.is_market_open", return_value=True):
        yield


@pytest.fixture
def mock_market_closed():
    """Pretend market is closed."""
    with patch("stotify.main.is_market_open", return_value=False):
        yield


@pytest.fixture
def mock_send_alert():
    """Mock send_alert, yields the mock for assertions."""
    with patch("stotify.main.send_alert", return_value=True) as mock:
        yield mock


def mock_price(price):
    """Helper to mock get_price with a specific value."""
    return patch("stotify.main.get_price", return_value=price)


def write_config(tmp_path, data):
    """Helper to write a config file and return its path."""
    config_file = tmp_path / "alerts.json"
    config_file.write_text(json.dumps(data))
    return config_file


# --- Config Loading ---


class TestLoadConfig:
    def test_valid_config(self, tmp_path):
        config_file = write_config(
            tmp_path, {"alerts": [{"ticker": "AAPL", "high": 250}]}
        )
        config = load_config(config_file)
        assert len(config["alerts"]) == 1

    def test_rejects_missing_alerts_key(self, tmp_path):
        config_file = write_config(tmp_path, {"tickers": []})
        with pytest.raises(ValueError, match="must have 'alerts'"):
            load_config(config_file)

    def test_rejects_missing_ticker(self, tmp_path):
        config_file = write_config(tmp_path, {"alerts": [{"high": 250}]})
        with pytest.raises(ValueError, match="must have 'ticker'"):
            load_config(config_file)

    def test_rejects_missing_threshold(self, tmp_path):
        config_file = write_config(tmp_path, {"alerts": [{"ticker": "AAPL"}]})
        with pytest.raises(ValueError, match="must have 'high' or 'low'"):
            load_config(config_file)


# --- Alert Checking ---


class TestCheckAlerts:
    def test_skips_when_market_closed(self, mock_market_closed):
        config = {"alerts": [{"ticker": "AAPL", "high": 250}]}
        assert check_alerts(config) == 0

    def test_high_alert_fires_when_price_above_threshold(
        self, mock_market_open, mock_send_alert
    ):
        config = {"alerts": [{"ticker": "AAPL", "high": 250}]}

        with mock_price(260.0):  # price > threshold
            sent = check_alerts(config)

        assert sent == 1
        mock_send_alert.assert_called_once_with("AAPL", 260.0, "high", 250)

    def test_low_alert_fires_when_price_below_threshold(
        self, mock_market_open, mock_send_alert
    ):
        config = {"alerts": [{"ticker": "AAPL", "low": 180}]}

        with mock_price(175.0):  # price < threshold
            sent = check_alerts(config)

        assert sent == 1
        mock_send_alert.assert_called_once_with("AAPL", 175.0, "low", 180)

    def test_no_alert_when_price_in_range(self, mock_market_open, mock_send_alert):
        config = {"alerts": [{"ticker": "AAPL", "high": 250, "low": 180}]}

        with mock_price(200.0):  # 180 < price < 250
            sent = check_alerts(config)

        assert sent == 0
        mock_send_alert.assert_not_called()

    def test_skips_ticker_when_price_unavailable(
        self, mock_market_open, mock_send_alert
    ):
        config = {"alerts": [{"ticker": "INVALID", "high": 100}]}

        with mock_price(None):  # yfinance failed
            sent = check_alerts(config)

        assert sent == 0
        mock_send_alert.assert_not_called()

    def test_skip_market_check_flag_bypasses_hours(self, mock_market_closed):
        config = {"alerts": [{"ticker": "AAPL", "high": 250}]}

        with mock_price(260.0), patch("stotify.main.send_alert", return_value=True):
            sent = check_alerts(config, skip_market_check=True)

        assert sent == 1


# --- CLI Entry Point ---


class TestMain:
    def test_returns_0_on_success(self, tmp_path):
        config_file = write_config(
            tmp_path, {"alerts": [{"ticker": "AAPL", "high": 250}]}
        )

        with patch("stotify.main.check_alerts", return_value=1):
            assert main(str(config_file)) == 0

    def test_returns_1_on_invalid_json(self, tmp_path):
        config_file = tmp_path / "invalid.json"
        config_file.write_text("not json")

        assert main(str(config_file)) == 1

    def test_returns_1_on_missing_file(self):
        assert main("/nonexistent/path.json") == 1
