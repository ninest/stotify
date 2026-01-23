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

    for group_name, alerts in data["groups"].items():
        print(get_channel(group_name))
        for alert in alerts:
            ticker = alert["ticker"]
            if "high" in alert:
                print(f"- {ticker} > {alert['high']}")
            if "low" in alert:
                print(f"- {ticker} < {alert['low']}")
        print()


if __name__ == "__main__":
    main()
