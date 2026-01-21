"""Trading hours detection for US stock market."""

from datetime import datetime, time

import pytz

ET = pytz.timezone("America/New_York")
MARKET_OPEN = time(9, 30)
MARKET_CLOSE = time(16, 0)


def is_market_open(dt: datetime | None = None) -> bool:
    """Check if US stock market is open. Does not account for holidays."""
    if dt is None:
        dt = datetime.now(ET)
    elif dt.tzinfo is None:
        dt = ET.localize(dt)
    else:
        dt = dt.astimezone(ET)

    # Weekday check (Mon=0, Fri=4)
    if dt.weekday() > 4:
        return False

    return MARKET_OPEN <= dt.time() < MARKET_CLOSE
