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

---

## Makefile ✓

- [x] `make test` - run pytest
- [x] `make format` - format + fix with ruff
- [x] `make check` - lint without modifying

### Notes

- Added ruff to dev dependencies

---

## Task 4 - GitHub Actions ✓

- [x] Created workflow directory (.github/workflows)
- [x] Created check_stocks.yml workflow
- [x] Configured cron schedule (every 15 min, Mon-Fri, 1-9 PM UTC)
- [x] Set up UV with caching
- [x] Committed workflow to repo

### Notes

- Runs every 15 min during market hours (9:30 AM - 4 PM ET) via `Check Stock Alerts_15M`
- Uses astral-sh/setup-uv@v7 for fast dependency installation
- NTFY_PREFIX configurable via repository variable
- Manual trigger available via workflow_dispatch
- No remote configured - run `git remote add origin <url>` then `git push` to enable
- `Check Stock Alerts_1D` runs after market close and skips the market-hours gate
  so rolling averages can run even when markets are closed.

---

## Task 5 - Custom Notification Groups ✓

- [x] TDD: Wrote comprehensive tests (37 total, all passing)
- [x] Updated config schema from `alerts` array to `groups` object
- [x] Added group name validation (a-z, A-Z, 0-9, -, _, max 100 chars)
- [x] Simplified notifier to use group-based channels
- [x] Updated all core modules (main.py, notifier.py)
- [x] Updated scripts/list_topics.py for groups
- [x] Updated example alerts.json config
- [x] All 49 tests passing

### Notes

**Breaking change (v2.0):** Config format changed

Old format:
```json
{
  "alerts": [
    {"ticker": "AAPL", "high": 250, "low": 246}
  ]
}
```

New format:
```json
{
  "groups": {
    "portfolio": [
      {"ticker": "AAPL", "high": 250, "low": 246}
    ]
  }
}
```

**Benefits:**
- Single ntfy.sh subscription per group instead of per alert-threshold
- Logical organization of alerts (e.g., "portfolio", "tech-watch")
- Messages now prefixed with `[group-name]` for easy filtering
- Channels simplified: `stotify-portfolio` vs `stotify-AAPL-H250`

**Migration:**
- Wrap existing alerts in a group: `{"groups": {"my-stocks": [...alerts...]}}`
- Run `scripts/list_topics.py` to see new channel names
- Update ntfy.sh subscriptions
