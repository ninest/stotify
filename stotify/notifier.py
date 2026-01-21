"""ntfy.sh notification sending."""

import logging
import os

import requests

NTFY_BASE_URL = "https://ntfy.sh"
DEFAULT_PREFIX = "stotify"

logger = logging.getLogger(__name__)


def get_channel(
    ticker: str, alert_type: str, threshold: float, prefix: str | None = None
) -> str:
    """Generate ntfy channel name. Format: {prefix}-{ticker}-{H|L}{threshold}"""
    if prefix is None:
        prefix = os.environ.get("NTFY_PREFIX", DEFAULT_PREFIX)
    type_char = "H" if alert_type == "high" else "L"
    # Remove decimal if whole number
    threshold_str = (
        str(int(threshold)) if threshold == int(threshold) else str(threshold)
    )
    return f"{prefix}-{ticker}-{type_char}{threshold_str}"


def send_alert(ticker: str, price: float, alert_type: str, threshold: float) -> bool:
    """Send price alert to ntfy.sh. Returns True on success, logs errors."""
    channel = get_channel(ticker, alert_type, threshold)
    url = f"{NTFY_BASE_URL}/{channel}"

    direction = "above" if alert_type == "high" else "below"
    message = f"{ticker} is ${price:.2f} ({direction} ${threshold:.2f})"

    try:
        response = requests.post(url, data=message, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to send alert to {channel}: {e}")
        return False
