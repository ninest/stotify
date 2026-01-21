"""Tests for stock module."""

from unittest.mock import Mock, patch

from stotify.stock import get_price


def test_get_price_from_fast_info():
    """Should return price from fast_info."""
    mock_ticker = Mock()
    mock_ticker.fast_info.get.return_value = 150.50

    with patch("stotify.stock.yf.Ticker", return_value=mock_ticker):
        price = get_price("AAPL")

    assert price == 150.50


def test_get_price_fallback_to_info():
    """Should fallback to info if fast_info has no price."""
    mock_ticker = Mock()
    mock_ticker.fast_info.get.return_value = None
    mock_ticker.info.get.return_value = 200.00

    with patch("stotify.stock.yf.Ticker", return_value=mock_ticker):
        price = get_price("GOOGL")

    assert price == 200.00


def test_get_price_returns_none_on_no_data():
    """Should return None if no price available."""
    mock_ticker = Mock()
    mock_ticker.fast_info.get.return_value = None
    mock_ticker.info.get.return_value = None

    with patch("stotify.stock.yf.Ticker", return_value=mock_ticker):
        price = get_price("INVALID")

    assert price is None


def test_get_price_returns_none_on_exception():
    """Should return None on any exception."""
    with patch("stotify.stock.yf.Ticker", side_effect=Exception("API error")):
        price = get_price("AAPL")

    assert price is None
