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
