"""ntfy.sh notification sending."""

import logging
import os

import requests

NTFY_BASE_URL = "https://ntfy.sh"
DEFAULT_PREFIX = "stotify"

logger = logging.getLogger(__name__)


def get_channel(group_name: str, prefix: str | None = None) -> str:
    """Generate ntfy channel name. Format: {prefix}-{group_name}"""
    if prefix is None:
        prefix = os.environ.get("NTFY_PREFIX", DEFAULT_PREFIX)
    return f"{prefix}-{group_name}"


def send_alert(
    ticker: str,
    price: float,
    alert_type: str | None,
    threshold: float | None,
    group_name: str,
    message: str | None = None,
) -> bool:
    """Send price alert to ntfy.sh. Returns True on success, logs errors."""
    channel = get_channel(group_name)
    url = f"{NTFY_BASE_URL}/{channel}"

    if message is None:
        direction = "above" if alert_type == "high" else "below"
        message = (
            f"[{group_name}] {ticker} is ${price:.2f} "
            f"({direction} ${threshold:.2f})"
        )
    else:
        message = f"[{group_name}] {message}"

    try:
        response = requests.post(url, data=message, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to send alert to {channel}: {e}")
        return False
