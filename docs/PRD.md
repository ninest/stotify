# Stotify - Product Requirements Document

## Overview

Stotify is a stock price alert system that monitors configured stock tickers and sends push notifications via ntfy.sh when prices cross specified thresholds.

## Problem Statement

Investors want to be notified when stocks hit certain price points without constantly monitoring the market. Stotify provides automated price threshold monitoring with push notifications.

## Technical Stack

- **Language**: Python
- **Package Manager**: UV
- **Stock Data**: Yahoo Finance (yfinance)
- **Notifications**: ntfy.sh
- **Scheduling**: GitHub Actions (cron every 15 minutes)

## Core Features

### 1. Stock Price Monitoring

- Fetch current stock prices from Yahoo Finance
- Support multiple stock tickers
- Check prices against configured thresholds (high/low)
- A single ticker can have both high and low alerts

### 2. Threshold Alerts

- **High alert**: Triggered when current price >= threshold
- **Low alert**: Triggered when current price <= threshold
- Alerts continue to fire every 15 minutes while condition remains true

### 3. Notifications via ntfy.sh

- Send push notifications to granular ntfy.sh channels
- Each alert has its own channel, auto-generated from the alert config
- Channel naming format: `{prefix}-{ticker}-{H|L}{threshold}`
  - Example: `stotify-AAPL-H250` (Apple high alert at $250)
  - Example: `stotify-AAPL-L180` (Apple low alert at $180)
- Users can subscribe to specific alerts or multiple channels
- Notification content includes:
  - Stock ticker symbol
  - Current price
  - Threshold that was triggered (high/low and value)

### 4. Trading Hours Check

- Only run checks during US stock market hours
- Market hours: 9:30 AM - 4:00 PM Eastern Time
- Monday through Friday (exclude weekends)
- Note: Does not account for market holidays

## Configuration

### Stock Alerts JSON (`alerts.json`)

```json
{
  "alerts": [
    {
      "ticker": "AAPL",
      "high": 250,
      "low": 180
    },
    {
      "ticker": "GOOGL",
      "high": 200
    },
    {
      "ticker": "MSFT",
      "low": 400
    }
  ]
}
```

- `ticker`: Stock symbol (required)
- `high`: Price threshold for high alert (optional)
- `low`: Price threshold for low alert (optional)
- At least one of `high` or `low` must be specified

### ntfy.sh Channel Configuration

- Channels are auto-generated per alert using the format: `{prefix}-{ticker}-{H|L}{threshold}`
- Prefix is configurable via `NTFY_PREFIX` environment variable (defaults to "stotify")
- Examples with default prefix:
  - `stotify-AAPL-H250` - High alert for AAPL at $250
  - `stotify-AAPL-L180` - Low alert for AAPL at $180
  - `stotify-GOOGL-H200` - High alert for GOOGL at $200
- Users subscribe to specific channels on their devices to receive alerts
- This allows granular control - follow one alert, one ticker, or all alerts

## Project Structure

```
stotify/
├── docs/
│   └── PRD.md
├── stotify/
│   ├── __init__.py
│   ├── main.py           # CLI entry point
│   ├── stock.py          # Stock price fetching (Yahoo Finance)
│   ├── notifier.py       # ntfy.sh notification sending
│   └── market_hours.py   # Trading hours validation
├── alerts.json           # Stock alert configuration
├── .github/
│   └── workflows/
│       └── check_stocks.yml  # GitHub Actions cron workflow
├── pyproject.toml
└── README.md
```

## Module Responsibilities

### `main.py`
- CLI entry point
- Orchestrates the check flow:
  1. Verify market is open
  2. Load alert configuration
  3. For each alert, fetch price and check thresholds
  4. Send notifications for triggered alerts

### `stock.py`
- Fetch current stock price using yfinance
- Handle API errors gracefully (silent skip on failure)

### `notifier.py`
- Generate channel name from alert config: `{prefix}-{ticker}-{H|L}{threshold}`
- Send notifications to the appropriate ntfy.sh channel
- Format notification message with ticker, price, and threshold

### `market_hours.py`
- Check if current time is within US market hours
- Eastern Time: 9:30 AM - 4:00 PM, Monday-Friday

## GitHub Actions Workflow

```yaml
name: Check Stock Prices

on:
  schedule:
    - cron: '*/15 * * * *'  # Every 15 minutes
  workflow_dispatch:         # Manual trigger for testing

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install UV
        uses: astral-sh/setup-uv@v4
      - name: Run stock checker
        env:
          NTFY_PREFIX: ${{ vars.NTFY_PREFIX }}  # Optional, defaults to "stotify"
        run: uv run python -m stotify.main
```

## Error Handling

- **Yahoo Finance errors**: Silently skip the affected ticker, continue with others
- **ntfy.sh errors**: Log error, continue with other notifications
- **Invalid config**: Exit with error message

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `NTFY_PREFIX` | Prefix for ntfy.sh channel names | No | `stotify` |

## Dependencies

- `yfinance` - Yahoo Finance API wrapper
- `requests` - HTTP client for ntfy.sh
- `pytz` - Timezone handling for market hours

## Out of Scope

- Market holiday detection
- Historical price tracking
- Web UI for configuration
- User authentication
- Alert state persistence (to prevent repeat notifications)

## Future Considerations

- Add market holiday calendar
- Support for other notification services (Slack, Discord, email)
- Percentage-based thresholds (e.g., "notify if drops 5%")
- Cooldown period to reduce notification frequency
