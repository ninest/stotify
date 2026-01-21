"""Tests for main module."""

import json
from unittest.mock import patch

import pytest

from stotify.main import load_config, check_alerts, main


class TestLoadConfig:
    def test_valid_config(self, tmp_path):
        """Should load valid config."""
        config_file = tmp_path / "alerts.json"
        config_file.write_text(
            json.dumps({"alerts": [{"ticker": "AAPL", "high": 250}]})
        )

        config = load_config(config_file)
        assert len(config["alerts"]) == 1

    def test_missing_alerts_key(self, tmp_path):
        """Should raise on missing 'alerts' key."""
        config_file = tmp_path / "alerts.json"
        config_file.write_text(json.dumps({"tickers": []}))

        with pytest.raises(ValueError, match="must have 'alerts'"):
            load_config(config_file)

    def test_missing_ticker(self, tmp_path):
        """Should raise if alert missing ticker."""
        config_file = tmp_path / "alerts.json"
        config_file.write_text(json.dumps({"alerts": [{"high": 250}]}))

        with pytest.raises(ValueError, match="must have 'ticker'"):
            load_config(config_file)

    def test_missing_threshold(self, tmp_path):
        """Should raise if alert has no high or low."""
        config_file = tmp_path / "alerts.json"
        config_file.write_text(json.dumps({"alerts": [{"ticker": "AAPL"}]}))

        with pytest.raises(ValueError, match="must have 'high' or 'low'"):
            load_config(config_file)


class TestCheckAlerts:
    def test_skips_when_market_closed(self):
        """Should skip alerts when market is closed."""
        config = {"alerts": [{"ticker": "AAPL", "high": 250}]}

        with patch("stotify.main.is_market_open", return_value=False):
            sent = check_alerts(config)

        assert sent == 0

    def test_high_alert_triggered(self):
        """Should send alert when price >= high threshold."""
        config = {"alerts": [{"ticker": "AAPL", "high": 250}]}

        with (
            patch("stotify.main.is_market_open", return_value=True),
            patch("stotify.main.get_price", return_value=260.0),
            patch("stotify.main.send_alert", return_value=True) as mock_send,
        ):
            sent = check_alerts(config)

        assert sent == 1
        mock_send.assert_called_once_with("AAPL", 260.0, "high", 250)

    def test_low_alert_triggered(self):
        """Should send alert when price <= low threshold."""
        config = {"alerts": [{"ticker": "AAPL", "low": 180}]}

        with (
            patch("stotify.main.is_market_open", return_value=True),
            patch("stotify.main.get_price", return_value=175.0),
            patch("stotify.main.send_alert", return_value=True) as mock_send,
        ):
            sent = check_alerts(config)

        assert sent == 1
        mock_send.assert_called_once_with("AAPL", 175.0, "low", 180)

    def test_no_alert_when_in_range(self):
        """Should not send alert when price is between thresholds."""
        config = {"alerts": [{"ticker": "AAPL", "high": 250, "low": 180}]}

        with (
            patch("stotify.main.is_market_open", return_value=True),
            patch("stotify.main.get_price", return_value=200.0),
            patch("stotify.main.send_alert") as mock_send,
        ):
            sent = check_alerts(config)

        assert sent == 0
        mock_send.assert_not_called()

    def test_skips_ticker_on_price_error(self):
        """Should skip ticker if get_price returns None."""
        config = {"alerts": [{"ticker": "INVALID", "high": 100}]}

        with (
            patch("stotify.main.is_market_open", return_value=True),
            patch("stotify.main.get_price", return_value=None),
            patch("stotify.main.send_alert") as mock_send,
        ):
            sent = check_alerts(config)

        assert sent == 0
        mock_send.assert_not_called()

    def test_skip_market_check_flag(self):
        """skip_market_check should bypass market hours check."""
        config = {"alerts": [{"ticker": "AAPL", "high": 250}]}

        with (
            patch("stotify.main.is_market_open", return_value=False),
            patch("stotify.main.get_price", return_value=260.0),
            patch("stotify.main.send_alert", return_value=True),
        ):
            sent = check_alerts(config, skip_market_check=True)

        assert sent == 1


class TestMain:
    def test_main_success(self, tmp_path):
        """Should return 0 on success."""
        config_file = tmp_path / "alerts.json"
        config_file.write_text(
            json.dumps({"alerts": [{"ticker": "AAPL", "high": 250}]})
        )

        with patch("stotify.main.check_alerts", return_value=1):
            result = main(str(config_file))

        assert result == 0

    def test_main_config_error(self, tmp_path):
        """Should return 1 on config error."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("not json")

        result = main(str(config_file))
        assert result == 1

    def test_main_missing_file(self):
        """Should return 1 on missing file."""
        result = main("/nonexistent/path.json")
        assert result == 1
