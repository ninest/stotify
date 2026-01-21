"""CLI orchestration for stock price alerts."""

import json
import sys
from pathlib import Path

from stotify.market_hours import is_market_open
from stotify.stock import get_price
from stotify.notifier import send_alert


def load_config(path: str | Path) -> dict:
    """Load and validate alerts.json config."""
    with open(path) as f:
        config = json.load(f)

    if "alerts" not in config or not isinstance(config["alerts"], list):
        raise ValueError("Config must have 'alerts' array")

    for alert in config["alerts"]:
        if "ticker" not in alert:
            raise ValueError("Each alert must have 'ticker'")
        if "high" not in alert and "low" not in alert:
            raise ValueError(f"Alert for {alert['ticker']} must have 'high' or 'low'")

    return config


def check_alerts(config: dict, skip_market_check: bool = False) -> int:
    """Process all alerts. Returns count of notifications sent."""
    if not skip_market_check and not is_market_open():
        print("Market is closed")
        return 0

    sent = 0
    for alert in config["alerts"]:
        ticker = alert["ticker"]
        price = get_price(ticker)

        if price is None:
            continue

        if "high" in alert and price >= alert["high"]:
            if send_alert(ticker, price, "high", alert["high"]):
                sent += 1

        if "low" in alert and price <= alert["low"]:
            if send_alert(ticker, price, "low", alert["low"]):
                sent += 1

    return sent


def main(config_path: str = "alerts.json") -> int:
    """Entry point. Returns 0 on success, 1 on config error."""
    try:
        config = load_config(config_path)
    except (json.JSONDecodeError, ValueError, FileNotFoundError) as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 1

    sent = check_alerts(config)
    print(f"Sent {sent} alert(s)")
    return 0


if __name__ == "__main__":
    config_file = sys.argv[1] if len(sys.argv) > 1 else "alerts.json"
    sys.exit(main(config_file))
