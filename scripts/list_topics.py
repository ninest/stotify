#!/usr/bin/env python3
"""List all ntfy.sh subscription topics from alerts.json."""

import json
from pathlib import Path

from stotify.main import extract_tickers
from stotify.notifier import get_channel

ALERTS_FILE = Path(__file__).parent.parent / "alerts.json"


def main() -> None:
    """Parse alerts and output ntfy.sh topics."""
    with open(ALERTS_FILE) as f:
        data = json.load(f)

    for group_name, alerts in data["groups"].items():
        print(get_channel(group_name))
        for alert in alerts:
            tickers = ",".join(extract_tickers(alert, group_name))
            strategy = alert.get("strategy", "unknown")
            timeframe = alert.get("timeframe", "unspecified")
            params = alert.get("params", {})
            print(
                "- "
                f"tickers={tickers} "
                f"strategy={strategy} "
                f"timeframe={timeframe} "
                f"params={params}"
            )
        print()


if __name__ == "__main__":
    main()
