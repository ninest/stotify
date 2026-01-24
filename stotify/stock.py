"""Stock price fetching via Yahoo Finance."""

import yfinance as yf


def get_price(ticker: str) -> float | None:
    """Fetch current price for ticker. Returns None on any error."""
    try:
        stock = yf.Ticker(ticker)
        # fast_info is quicker than info
        price = stock.fast_info.get("lastPrice")
        if price is None:
            # fallback to regular info
            price = stock.info.get("currentPrice")
        return float(price) if price else None
    except Exception:
        return None


def get_history(ticker: str, period: str = "1y", interval: str = "1d"):
    """Fetch historical data for a ticker. Returns None on any error."""
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period=period, interval=interval)
        if history is None or history.empty:
            return None
        return history
    except Exception:
        return None
