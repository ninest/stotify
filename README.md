ST Backtest App
===============

1. Install dependencies: `uv sync`.
2. Run the app: `uv run streamlit run st_backtest_app.py`.
3. Enter a stock ticker and date range, then click **Run backtest**.

Technical note: A trade starts on the first day the fast MA crosses above the slow MA (after enough days exist to compute both averages). The end date is simply the last day of data to evaluate (not a “best sell” date). Each trade exits by either (a) a fixed hold period (e.g., 30 trading days after entry) or (b) the next time the fast MA crosses below the slow MA, depending on the exit rule you choose in the app.
