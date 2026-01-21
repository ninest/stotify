#!/usr/bin/env python3
"""List all ntfy.sh subscription topics from alerts.json."""

import json
from pathlib import Path

from stotify.notifier import get_channel

ALERTS_FILE = Path(__file__).parent.parent / "alerts.json"


def main() -> None:
    """Parse alerts and output ntfy.sh topics."""
    with open(ALERTS_FILE) as f:
        data = json.load(f)

    for alert in data["alerts"]:
        ticker = alert["ticker"]
        if "high" in alert:
            print(get_channel(ticker, "high", alert["high"]))
        if "low" in alert:
            print(get_channel(ticker, "low", alert["low"]))


if __name__ == "__main__":
    main()
