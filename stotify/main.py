"""CLI orchestration for stock price alerts."""

import json
import re
import sys
from pathlib import Path

from stotify.market_hours import is_market_open
from stotify.stock import get_price
from stotify.notifier import send_alert


def is_valid_group_name(name: str) -> bool:
    """Check if group name is valid ntfy.sh channel name."""
    if not name:
        return False
    if len(name) > 100:
        return False
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", name))


def load_config(path: str | Path) -> dict:
    """Load and validate alerts.json config."""
    with open(path) as f:
        config = json.load(f)

    if "groups" not in config or not isinstance(config["groups"], dict):
        raise ValueError("Config must have 'groups' object")

    for group_name, alerts in config["groups"].items():
        # Validate group name
        if not group_name:
            raise ValueError("Group name cannot be empty")
        if len(group_name) > 100:
            raise ValueError(f"Group name '{group_name}' exceeds 100 characters")
        if not is_valid_group_name(group_name):
            raise ValueError(
                f"Group name '{group_name}' contains invalid characters "
                "(only a-z, A-Z, 0-9, -, _ allowed)"
            )

        # Validate group has alerts
        if not alerts or not isinstance(alerts, list):
            raise ValueError(f"Group '{group_name}' has no alerts")

        # Validate each alert
        for alert in alerts:
            if "ticker" not in alert:
                raise ValueError(f"Alert in group '{group_name}' missing 'ticker'")
            if "high" not in alert and "low" not in alert:
                ticker = alert.get("ticker", "unknown")
                raise ValueError(
                    f"Alert for {ticker} in group '{group_name}' must have 'high' or 'low'"
                )

    return config


def check_alerts(config: dict, skip_market_check: bool = False) -> int:
    """Process all alerts. Returns count of notifications sent."""
    if not skip_market_check and not is_market_open():
        print("Market is closed")
        return 0

    sent = 0
    for group_name, alerts in config["groups"].items():
        for alert in alerts:
            ticker = alert["ticker"]
            price = get_price(ticker)

            if price is None:
                continue

            if "high" in alert and price >= alert["high"]:
                if send_alert(ticker, price, "high", alert["high"], group_name):
                    sent += 1

            if "low" in alert and price <= alert["low"]:
                if send_alert(ticker, price, "low", alert["low"], group_name):
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
