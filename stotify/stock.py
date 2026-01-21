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
