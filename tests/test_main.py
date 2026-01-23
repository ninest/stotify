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
    def test_valid_config_with_groups(self, tmp_path):
        """Valid groups structure should load successfully."""
        config_file = write_config(
            tmp_path, {"groups": {"portfolio": [{"ticker": "AAPL", "high": 250}]}}
        )
        config = load_config(config_file)
        assert "groups" in config
        assert "portfolio" in config["groups"]
        assert len(config["groups"]["portfolio"]) == 1

    def test_multiple_groups(self, tmp_path):
        """Multiple groups should all load."""
        config_file = write_config(
            tmp_path,
            {
                "groups": {
                    "portfolio": [{"ticker": "AAPL", "high": 250}],
                    "tech-watch": [{"ticker": "GOOGL", "low": 320}],
                }
            },
        )
        config = load_config(config_file)
        assert len(config["groups"]) == 2
        assert "portfolio" in config["groups"]
        assert "tech-watch" in config["groups"]

    def test_rejects_missing_groups_key(self, tmp_path):
        """Config without 'groups' key should error."""
        config_file = write_config(tmp_path, {"alerts": []})
        with pytest.raises(ValueError, match="must have 'groups'"):
            load_config(config_file)

    def test_rejects_empty_group(self, tmp_path):
        """Groups with no alerts should error."""
        config_file = write_config(tmp_path, {"groups": {"empty": []}})
        with pytest.raises(ValueError, match="Group 'empty' has no alerts"):
            load_config(config_file)

    def test_rejects_invalid_group_name_spaces(self, tmp_path):
        """Group names with spaces should error."""
        config_file = write_config(
            tmp_path, {"groups": {"my portfolio": [{"ticker": "AAPL", "high": 250}]}}
        )
        with pytest.raises(
            ValueError, match="Group name 'my portfolio' contains invalid characters"
        ):
            load_config(config_file)

    def test_rejects_invalid_group_name_special_chars(self, tmp_path):
        """Group names with special chars should error."""
        config_file = write_config(
            tmp_path, {"groups": {"portfolio!": [{"ticker": "AAPL", "high": 250}]}}
        )
        with pytest.raises(
            ValueError, match="Group name 'portfolio!' contains invalid characters"
        ):
            load_config(config_file)

    def test_accepts_valid_group_name_with_hyphens(self, tmp_path):
        """Group names with hyphens should be valid."""
        config_file = write_config(
            tmp_path, {"groups": {"tech-watch": [{"ticker": "AAPL", "high": 250}]}}
        )
        config = load_config(config_file)
        assert "tech-watch" in config["groups"]

    def test_accepts_valid_group_name_with_underscores(self, tmp_path):
        """Group names with underscores should be valid."""
        config_file = write_config(
            tmp_path, {"groups": {"tech_watch": [{"ticker": "AAPL", "high": 250}]}}
        )
        config = load_config(config_file)
        assert "tech_watch" in config["groups"]

    def test_rejects_empty_group_name(self, tmp_path):
        """Empty group name should error."""
        config_file = write_config(
            tmp_path, {"groups": {"": [{"ticker": "AAPL", "high": 250}]}}
        )
        with pytest.raises(ValueError, match="Group name cannot be empty"):
            load_config(config_file)

    def test_rejects_group_name_exceeding_100_chars(self, tmp_path):
        """Group names > 100 characters should error."""
        long_name = "a" * 101
        config_file = write_config(
            tmp_path, {"groups": {long_name: [{"ticker": "AAPL", "high": 250}]}}
        )
        with pytest.raises(ValueError, match="exceeds 100 characters"):
            load_config(config_file)

    def test_accepts_group_name_exactly_100_chars(self, tmp_path):
        """Group names exactly 100 characters should be valid."""
        exact_name = "a" * 100
        config_file = write_config(
            tmp_path, {"groups": {exact_name: [{"ticker": "AAPL", "high": 250}]}}
        )
        config = load_config(config_file)
        assert exact_name in config["groups"]

    def test_group_names_are_case_sensitive(self, tmp_path):
        """Group names should be case-sensitive."""
        config_file = write_config(
            tmp_path,
            {
                "groups": {
                    "Portfolio": [{"ticker": "AAPL", "high": 250}],
                    "portfolio": [{"ticker": "GOOGL", "high": 300}],
                }
            },
        )
        config = load_config(config_file)
        assert "Portfolio" in config["groups"]
        assert "portfolio" in config["groups"]
        assert len(config["groups"]) == 2

    def test_rejects_missing_ticker_in_group(self, tmp_path):
        """Alerts missing ticker should error with group context."""
        config_file = write_config(
            tmp_path, {"groups": {"portfolio": [{"high": 250}]}}
        )
        with pytest.raises(
            ValueError, match="Alert in group 'portfolio' missing 'ticker'"
        ):
            load_config(config_file)

    def test_rejects_missing_threshold_in_group(self, tmp_path):
        """Alerts missing thresholds should error with group context."""
        config_file = write_config(
            tmp_path, {"groups": {"portfolio": [{"ticker": "AAPL"}]}}
        )
        with pytest.raises(
            ValueError,
            match="Alert for AAPL in group 'portfolio' must have 'high' or 'low'",
        ):
            load_config(config_file)

    def test_allows_both_high_and_low_in_group(self, tmp_path):
        """Alerts with both high and low should be valid."""
        config_file = write_config(
            tmp_path,
            {"groups": {"portfolio": [{"ticker": "AAPL", "high": 250, "low": 180}]}},
        )
        config = load_config(config_file)
        assert config["groups"]["portfolio"][0]["high"] == 250
        assert config["groups"]["portfolio"][0]["low"] == 180


# --- Alert Checking ---


class TestCheckAlerts:
    def test_skips_when_market_closed(self, mock_market_closed):
        """Should skip all checks when market is closed."""
        config = {"groups": {"portfolio": [{"ticker": "AAPL", "high": 250}]}}
        assert check_alerts(config) == 0

    def test_high_alert_fires_when_price_above_threshold(
        self, mock_market_open, mock_send_alert
    ):
        """High alert should fire when price exceeds threshold."""
        config = {"groups": {"portfolio": [{"ticker": "AAPL", "high": 250}]}}

        with mock_price(260.0):  # price > threshold
            sent = check_alerts(config)

        assert sent == 1
        mock_send_alert.assert_called_once_with("AAPL", 260.0, "high", 250, "portfolio")

    def test_low_alert_fires_when_price_below_threshold(
        self, mock_market_open, mock_send_alert
    ):
        """Low alert should fire when price falls below threshold."""
        config = {"groups": {"portfolio": [{"ticker": "AAPL", "low": 180}]}}

        with mock_price(175.0):  # price < threshold
            sent = check_alerts(config)

        assert sent == 1
        mock_send_alert.assert_called_once_with("AAPL", 175.0, "low", 180, "portfolio")

    def test_no_alert_when_price_in_range(self, mock_market_open, mock_send_alert):
        """No alert should fire when price is between thresholds."""
        config = {"groups": {"portfolio": [{"ticker": "AAPL", "high": 250, "low": 180}]}}

        with mock_price(200.0):  # 180 < price < 250
            sent = check_alerts(config)

        assert sent == 0
        mock_send_alert.assert_not_called()

    def test_skips_ticker_when_price_unavailable(
        self, mock_market_open, mock_send_alert
    ):
        """Should skip alerts when price fetch fails."""
        config = {"groups": {"portfolio": [{"ticker": "INVALID", "high": 100}]}}

        with mock_price(None):  # yfinance failed
            sent = check_alerts(config)

        assert sent == 0
        mock_send_alert.assert_not_called()

    def test_skip_market_check_flag_bypasses_hours(self, mock_market_closed):
        """skip_market_check=True should allow checks when market closed."""
        config = {"groups": {"portfolio": [{"ticker": "AAPL", "high": 250}]}}

        with mock_price(260.0), patch("stotify.main.send_alert", return_value=True):
            sent = check_alerts(config, skip_market_check=True)

        assert sent == 1

    def test_multiple_groups_send_to_different_groups(
        self, mock_market_open, mock_send_alert
    ):
        """Alerts in different groups should pass correct group name."""
        config = {
            "groups": {
                "portfolio": [{"ticker": "AAPL", "high": 250}],
                "tech-watch": [{"ticker": "GOOGL", "low": 320}],
            }
        }

        with mock_price(260.0):
            sent = check_alerts(config)

        assert sent == 2
        # Check both calls include their group names
        calls = mock_send_alert.call_args_list
        assert calls[0][0] == ("AAPL", 260.0, "high", 250, "portfolio")
        assert calls[1][0] == ("GOOGL", 260.0, "low", 320, "tech-watch")

    def test_multiple_alerts_in_same_group(self, mock_market_open, mock_send_alert):
        """Multiple alerts in same group should all use that group name."""
        config = {
            "groups": {
                "portfolio": [
                    {"ticker": "AAPL", "high": 250},
                    {"ticker": "MSFT", "high": 400},
                ]
            }
        }

        with mock_price(500.0):  # Both will trigger
            sent = check_alerts(config)

        assert sent == 2
        calls = mock_send_alert.call_args_list
        assert calls[0][0] == ("AAPL", 500.0, "high", 250, "portfolio")
        assert calls[1][0] == ("MSFT", 500.0, "high", 400, "portfolio")

    def test_same_ticker_in_multiple_groups(self, mock_market_open, mock_send_alert):
        """Same ticker in different groups should trigger separate alerts."""
        config = {
            "groups": {
                "portfolio": [{"ticker": "AAPL", "high": 250}],
                "tech-watch": [{"ticker": "AAPL", "high": 250}],
            }
        }

        with mock_price(260.0):
            sent = check_alerts(config)

        assert sent == 2
        calls = mock_send_alert.call_args_list
        assert calls[0][0] == ("AAPL", 260.0, "high", 250, "portfolio")
        assert calls[1][0] == ("AAPL", 260.0, "high", 250, "tech-watch")


# --- CLI Entry Point ---


class TestMain:
    def test_returns_0_on_success(self, tmp_path):
        """Main should return 0 when config is valid and checks run."""
        config_file = write_config(
            tmp_path, {"groups": {"portfolio": [{"ticker": "AAPL", "high": 250}]}}
        )

        with patch("stotify.main.check_alerts", return_value=1):
            assert main(str(config_file)) == 0

    def test_returns_1_on_invalid_json(self, tmp_path):
        """Main should return 1 on invalid JSON."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("not json")

        assert main(str(config_file)) == 1

    def test_returns_1_on_missing_file(self):
        """Main should return 1 when config file doesn't exist."""
        assert main("/nonexistent/path.json") == 1
