"""Tests for market_hours module."""

from datetime import datetime

import pytz

from stotify.market_hours import is_market_open, ET


def test_market_open_midday_weekday():
    """Wednesday 12:00 ET should be open."""
    dt = ET.localize(datetime(2024, 1, 10, 12, 0))  # Wednesday
    assert is_market_open(dt) is True


def test_market_closed_weekend():
    """Saturday should be closed."""
    dt = ET.localize(datetime(2024, 1, 13, 12, 0))  # Saturday
    assert is_market_open(dt) is False


def test_market_closed_before_open():
    """9:29 ET should be closed."""
    dt = ET.localize(datetime(2024, 1, 10, 9, 29))
    assert is_market_open(dt) is False


def test_market_open_at_open():
    """9:30 ET should be open."""
    dt = ET.localize(datetime(2024, 1, 10, 9, 30))
    assert is_market_open(dt) is True


def test_market_closed_at_close():
    """16:00 ET should be closed."""
    dt = ET.localize(datetime(2024, 1, 10, 16, 0))
    assert is_market_open(dt) is False


def test_market_open_before_close():
    """15:59 ET should be open."""
    dt = ET.localize(datetime(2024, 1, 10, 15, 59))
    assert is_market_open(dt) is True


def test_naive_datetime_treated_as_et():
    """Naive datetime should be localized to ET."""
    dt = datetime(2024, 1, 10, 12, 0)
    assert is_market_open(dt) is True


def test_other_timezone_converted():
    """UTC time should be converted to ET."""
    utc = pytz.UTC
    # 17:00 UTC = 12:00 ET (winter)
    dt = utc.localize(datetime(2024, 1, 10, 17, 0))
    assert is_market_open(dt) is True
