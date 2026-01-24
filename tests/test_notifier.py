"""Tests for notifier module."""

from unittest.mock import Mock, patch


from stotify.notifier import get_channel, send_alert


class TestGetChannel:
    def test_get_channel_with_group_name(self):
        """Should format channel with group name and prefix."""
        channel = get_channel("portfolio", prefix="stotify")
        assert channel == "stotify-portfolio"

    def test_get_channel_with_custom_prefix(self):
        """Should use custom prefix when provided."""
        channel = get_channel("tech-watch", prefix="myprefix")
        assert channel == "myprefix-tech-watch"

    def test_get_channel_with_env_prefix(self, monkeypatch):
        """Should use NTFY_PREFIX env var when prefix not specified."""
        monkeypatch.setenv("NTFY_PREFIX", "myprefix")
        channel = get_channel("portfolio")
        assert channel == "myprefix-portfolio"

    def test_get_channel_default_prefix(self, monkeypatch):
        """Should use 'stotify' as default prefix."""
        monkeypatch.delenv("NTFY_PREFIX", raising=False)
        channel = get_channel("crypto-stocks")
        assert channel == "stotify-crypto-stocks"

    def test_get_channel_with_underscores(self):
        """Should handle group names with underscores."""
        channel = get_channel("tech_watch", prefix="stotify")
        assert channel == "stotify-tech_watch"


class TestSendAlert:
    def test_send_alert_success_with_group(self):
        """Should return True on successful POST and include group name."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()

        with patch(
            "stotify.notifier.requests.post", return_value=mock_response
        ) as mock_post:
            result = send_alert("AAPL", 255.50, "high", 250, "portfolio")

        assert result is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        # Check channel uses group name
        assert "stotify-portfolio" in call_args[0][0]
        # Check message includes group prefix
        assert "[portfolio] AAPL is $255.50 (above $250.00)" in call_args[1]["data"]

    def test_send_alert_low_with_group(self):
        """Low alert should say 'below' and include group prefix."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()

        with patch(
            "stotify.notifier.requests.post", return_value=mock_response
        ) as mock_post:
            send_alert("AAPL", 175.00, "low", 180, "portfolio")

        call_args = mock_post.call_args
        data = call_args[1]["data"]
        assert "[portfolio]" in data
        assert "below" in data
        assert "AAPL is $175.00 (below $180.00)" in data

    def test_send_alert_message_format(self):
        """Should format message with [group] prefix."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()

        with patch(
            "stotify.notifier.requests.post", return_value=mock_response
        ) as mock_post:
            send_alert("GOOGL", 340.25, "high", 340, "tech-watch")

        call_args = mock_post.call_args
        data = call_args[1]["data"]
        assert data.startswith("[tech-watch]")
        assert "GOOGL" in data
        assert "$340.25" in data

    def test_send_alert_different_groups_use_different_channels(self):
        """Different groups should route to different channels."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()

        with patch(
            "stotify.notifier.requests.post", return_value=mock_response
        ) as mock_post:
            send_alert("AAPL", 255.50, "high", 250, "portfolio")
            url1 = mock_post.call_args[0][0]

            mock_post.reset_mock()
            send_alert("AAPL", 255.50, "high", 250, "tech-watch")
            url2 = mock_post.call_args[0][0]

        # Same ticker, different groups = different channels
        assert "stotify-portfolio" in url1
        assert "stotify-tech-watch" in url2
        assert url1 != url2

    def test_send_alert_failure(self):
        """Should return False and log on error."""
        with patch(
            "stotify.notifier.requests.post", side_effect=Exception("Network error")
        ):
            with patch("stotify.notifier.logger.error") as mock_log:
                result = send_alert("AAPL", 255.50, "high", 250, "portfolio")

        assert result is False
        mock_log.assert_called_once()

    def test_send_alert_custom_message(self):
        """Custom message should be used when provided."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()

        with patch(
            "stotify.notifier.requests.post", return_value=mock_response
        ) as mock_post:
            result = send_alert(
                "AAPL",
                255.50,
                "ma_cross",
                None,
                "portfolio",
                message="AAPL 50d MA above 200d MA",
            )

        assert result is True
        call_args = mock_post.call_args
        assert "[portfolio] AAPL 50d MA above 200d MA" in call_args[1]["data"]
