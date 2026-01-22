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

    for group_name in data["groups"].keys():
        print(get_channel(group_name))


if __name__ == "__main__":
    main()
