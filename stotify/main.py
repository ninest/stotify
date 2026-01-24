"""CLI orchestration for stock price alerts."""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from stotify.market_hours import is_market_open
from stotify.notifier import send_alert
from stotify.strategies import get_strategy

TIMEFRAME_PATTERN = re.compile(r"^\d+(m|h|d)$")


def is_valid_group_name(name: str) -> bool:
    """Check if group name is valid ntfy.sh channel name."""
    if not name:
        return False
    if len(name) > 100:
        return False
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", name))


def is_valid_timeframe(timeframe: str) -> bool:
    """Check if timeframe matches supported patterns (e.g., 15m, 6h, 1d)."""
    return bool(TIMEFRAME_PATTERN.match(timeframe))


def extract_tickers(alert: dict, group_name: str) -> list[str]:
    """Return a list of tickers for an alert, validating the input."""
    if "tickers" in alert and "ticker" in alert:
        raise ValueError(
            f"Alert in group '{group_name}' cannot define both 'ticker' and 'tickers'"
        )
    if "tickers" in alert:
        tickers = alert["tickers"]
        if not isinstance(tickers, list) or not tickers:
            raise ValueError(f"Alert in group '{group_name}' has invalid 'tickers'")
        if not all(isinstance(t, str) and t for t in tickers):
            raise ValueError(f"Alert in group '{group_name}' has invalid 'tickers'")
        return tickers
    if "ticker" in alert:
        ticker = alert["ticker"]
        if not isinstance(ticker, str) or not ticker:
            raise ValueError(f"Alert in group '{group_name}' has invalid 'ticker'")
        return [ticker]
    raise ValueError(f"Alert in group '{group_name}' missing 'ticker' or 'tickers'")


def validate_alert(alert: dict, group_name: str) -> None:
    """Validate a single alert configuration."""
    if "strategy" not in alert:
        raise ValueError(f"Alert in group '{group_name}' missing 'strategy'")
    if "timeframe" not in alert:
        raise ValueError(f"Alert in group '{group_name}' missing 'timeframe'")
    if not isinstance(alert["timeframe"], str) or not is_valid_timeframe(
        alert["timeframe"]
    ):
        raise ValueError(f"Alert in group '{group_name}' has invalid timeframe")

    tickers = extract_tickers(alert, group_name)

    if "params" not in alert or not isinstance(alert["params"], dict):
        raise ValueError(f"Alert in group '{group_name}' missing 'params'")

    strategy_name = alert["strategy"]
    try:
        get_strategy(strategy_name)
    except ValueError as exc:
        raise ValueError(
            f"Alert in group '{group_name}' has invalid strategy '{strategy_name}'"
        ) from exc

    params = alert["params"]
    if strategy_name == "threshold":
        if "high" not in params and "low" not in params:
            ticker_label = ", ".join(tickers)
            raise ValueError(
                f"Alert for {ticker_label} in group '{group_name}' must have "
                "'high' or 'low' in params"
            )
    elif strategy_name == "ma_cross":
        for key in ("fast_window", "slow_window"):
            if key not in params:
                raise ValueError(
                    f"Alert in group '{group_name}' missing '{key}' in params"
                )
            if not isinstance(params[key], int) or params[key] <= 0:
                raise ValueError(
                    f"Alert in group '{group_name}' has invalid '{key}' value"
                )


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
            validate_alert(alert, group_name)

    return config


def check_alerts(
    config: dict,
    skip_market_check: bool = False,
    timeframe_filter: str | None = None,
) -> int:
    """Process all alerts. Returns count of notifications sent."""
    market_open = is_market_open()
    if not skip_market_check and not market_open:
        print("Market is closed; skipping non-1d alerts")

    sent = 0
    for group_name, alerts in config["groups"].items():
        for alert in alerts:
            if not skip_market_check and not market_open and alert["timeframe"] != "1d":
                print(
                    "Skipping alert due to market hours: "
                    f"group={group_name} "
                    f"strategy={alert['strategy']} "
                    f"timeframe={alert['timeframe']}"
                )
                continue

            if timeframe_filter and alert["timeframe"] != timeframe_filter:
                print(
                    "Skipping alert due to timeframe mismatch: "
                    f"group={group_name} "
                    f"strategy={alert['strategy']} "
                    f"timeframe={alert['timeframe']}"
                )
                continue

            strategy = get_strategy(alert["strategy"])
            tickers = extract_tickers(alert, group_name)
            signals = strategy(tickers, alert["params"])
            if not signals:
                print(
                    "No notification sent: "
                    f"group={group_name} "
                    f"strategy={alert['strategy']} "
                    f"tickers={','.join(tickers)} "
                    "reason=conditions not met"
                )
            for signal in signals:
                if send_alert(
                    signal.ticker,
                    signal.price,
                    signal.alert_type,
                    signal.threshold,
                    group_name,
                    message=signal.message,
                ):
                    sent += 1
                    print(
                        "Notification sent: "
                        f"group={group_name} "
                        f"ticker={signal.ticker} "
                        f"strategy={alert['strategy']}"
                    )
                else:
                    print(
                        "Notification failed: "
                        f"group={group_name} "
                        f"ticker={signal.ticker} "
                        f"strategy={alert['strategy']}"
                    )

    return sent


def parse_args(args: list[str]) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run stock alert checks.")
    parser.add_argument(
        "config",
        nargs="?",
        default="alerts.json",
        help="Path to alerts.json config file",
    )
    parser.add_argument(
        "--timeframe",
        default=os.environ.get("STOTIFY_TIMEFRAME"),
        help="Only evaluate alerts matching the timeframe (e.g., 15m, 1d)",
    )
    parser.add_argument(
        "--skip-market-check",
        action="store_true",
        help="Skip market hours check",
    )
    return parser.parse_args(args)


def main(
    config_path: str = "alerts.json",
    timeframe_filter: str | None = None,
    skip_market_check: bool = False,
) -> int:
    """Entry point. Returns 0 on success, 1 on config error."""
    try:
        config = load_config(config_path)
    except (json.JSONDecodeError, ValueError, FileNotFoundError) as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 1

    if timeframe_filter and not is_valid_timeframe(timeframe_filter):
        print("Config error: Invalid timeframe filter", file=sys.stderr)
        return 1

    sent = check_alerts(
        config,
        skip_market_check=skip_market_check,
        timeframe_filter=timeframe_filter,
    )
    print(f"Sent {sent} alert(s)")
    return 0


if __name__ == "__main__":
    parsed = parse_args(sys.argv[1:])
    sys.exit(main(parsed.config, parsed.timeframe, parsed.skip_market_check))
