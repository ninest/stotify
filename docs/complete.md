# Completed Tasks

Tasks moved here once done.

---

## Task 1 - Project Setup ✓

- [x] Initialize UV project
- [x] Add dependencies (yfinance, requests, pytz, pytest)
- [x] Create project structure (stotify/, tests/)
- [x] Create sample alerts.json
- [x] Verify setup works

### Notes

- Using Python 3.14.2 with UV
- yfinance 1.0 installed (uses curl-cffi, pandas, numpy under the hood)
- Run tests with `uv run pytest`
- Run python scripts with `uv run python <script>`
- `alerts.json` format: `{"alerts": [{"ticker": "AAPL", "high": 250, "low": 180}]}`
  - `high` and `low` thresholds are optional per alert

---

## Task 2 - Core Modules ✓

- [x] market_hours.py - trading hours check (9:30-16:00 ET, Mon-Fri)
- [x] stock.py - fetch price via yfinance
- [x] notifier.py - send to ntfy.sh with auto-generated channels
- [x] main.py - CLI orchestration

### Notes

- 33 tests total, all passing
- Run with `uv run python -m stotify.main [alerts.json]`
- `skip_market_check` flag available for testing outside market hours
- NTFY_PREFIX env var configures channel prefix (default: "stotify")
