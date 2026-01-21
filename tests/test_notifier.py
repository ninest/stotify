"""Tests for notifier module."""

from unittest.mock import Mock, patch


from stotify.notifier import get_channel, send_alert


class TestGetChannel:
    def test_high_alert_channel(self):
        """High alert should use H prefix."""
        channel = get_channel("AAPL", "high", 250, prefix="stotify")
        assert channel == "stotify-AAPL-H250"

    def test_low_alert_channel(self):
        """Low alert should use L prefix."""
        channel = get_channel("AAPL", "low", 180, prefix="stotify")
        assert channel == "stotify-AAPL-L180"

    def test_decimal_threshold(self):
        """Decimal thresholds should be preserved."""
        channel = get_channel("TSLA", "high", 199.50, prefix="test")
        assert channel == "test-TSLA-H199.5"

    def test_uses_env_prefix(self, monkeypatch):
        """Should use NTFY_PREFIX env var when prefix not specified."""
        monkeypatch.setenv("NTFY_PREFIX", "myprefix")
        channel = get_channel("GOOGL", "high", 200)
        assert channel == "myprefix-GOOGL-H200"

    def test_default_prefix(self, monkeypatch):
        """Should use 'stotify' as default prefix."""
        monkeypatch.delenv("NTFY_PREFIX", raising=False)
        channel = get_channel("MSFT", "low", 300)
        assert channel == "stotify-MSFT-L300"


class TestSendAlert:
    def test_send_alert_success(self):
        """Should return True on successful POST."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()

        with patch(
            "stotify.notifier.requests.post", return_value=mock_response
        ) as mock_post:
            result = send_alert("AAPL", 255.50, "high", 250)

        assert result is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "stotify-AAPL-H250" in call_args[0][0]
        assert "AAPL is $255.50 (above $250.00)" in call_args[1]["data"]

    def test_send_alert_low(self):
        """Low alert should say 'below'."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()

        with patch(
            "stotify.notifier.requests.post", return_value=mock_response
        ) as mock_post:
            send_alert("AAPL", 175.00, "low", 180)

        call_args = mock_post.call_args
        assert "below" in call_args[1]["data"]

    def test_send_alert_failure(self):
        """Should return False and log on error."""
        with patch(
            "stotify.notifier.requests.post", side_effect=Exception("Network error")
        ):
            with patch("stotify.notifier.logger.error") as mock_log:
                result = send_alert("AAPL", 255.50, "high", 250)

        assert result is False
        mock_log.assert_called_once()
