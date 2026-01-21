# Stotify - Product Requirements Document

## Overview

Stock price alert system that monitors configured tickers and sends ntfy.sh notifications when prices cross thresholds.

## Technical Stack

- **Language**: Python
- **Package Manager**: UV
- **Stock Data**: Yahoo Finance (yfinance)
- **Notifications**: ntfy.sh
- **Scheduling**: GitHub Actions (cron every 15 minutes)
- **Testing**: pytest

## Specifications

### Threshold Alerts
- **High alert**: Triggered when current price >= threshold
- **Low alert**: Triggered when current price <= threshold
- Alerts fire every 15 minutes while condition remains true

### ntfy.sh Channels
- Auto-generated per alert: `{prefix}-{ticker}-{H|L}{threshold}`
- Examples: `stotify-AAPL-H250`, `stotify-AAPL-L180`
- Prefix configurable via `NTFY_PREFIX` env var (default: "stotify")

### Trading Hours
- 9:30 AM - 4:00 PM Eastern Time
- Monday through Friday
- Does not account for market holidays

### Configuration (`alerts.json`)
```json
{
  "alerts": [
    { "ticker": "AAPL", "high": 250, "low": 180 },
    { "ticker": "GOOGL", "high": 200 }
  ]
}
```

### Error Handling
- Yahoo Finance errors: silently skip ticker
- ntfy.sh errors: log and continue
- Invalid config: exit with error

## Project Structure

```
stotify/
├── docs/
│   ├── PRD.md
│   ├── complete.md
│   └── future.md
├── stotify/
│   ├── __init__.py
│   ├── main.py
│   ├── stock.py
│   ├── notifier.py
│   └── market_hours.py
├── tests/
│   ├── __init__.py
│   ├── test_stock.py
│   ├── test_notifier.py
│   ├── test_market_hours.py
│   └── test_main.py
├── alerts.json
├── .github/workflows/check_stocks.yml
├── pyproject.toml
├── AGENTS.md
└── CLAUDE.md
```

---

## Tasks

### 1. Project Setup
- [ ] 1.1 Initialize UV project with pyproject.toml
- [ ] 1.2 Add dependencies (yfinance, requests, pytz, pytest)
- [ ] 1.3 Create project structure (stotify/, tests/)
- [ ] 1.4 Create sample alerts.json

### 2. Core Modules
- [ ] 2.1 Implement `market_hours.py` - trading hours check
- [ ] 2.2 Implement `stock.py` - fetch price from Yahoo Finance
- [ ] 2.3 Implement `notifier.py` - send to ntfy.sh with channel generation
- [ ] 2.4 Implement `main.py` - CLI orchestration

### 3. Testing
- [ ] 3.1 Write tests for `market_hours.py`
- [ ] 3.2 Write tests for `stock.py` (mock yfinance)
- [ ] 3.3 Write tests for `notifier.py` (mock requests)
- [ ] 3.4 Write tests for `main.py` (integration)
- [ ] 3.5 Ensure good test coverage

### 4. GitHub Actions
- [ ] 4.1 Create workflow file for cron job
- [ ] 4.2 Add manual trigger for testing
- [ ] 4.3 Configure UV setup in workflow

### 5. Documentation
- [ ] 5.1 Write README.md with setup instructions
