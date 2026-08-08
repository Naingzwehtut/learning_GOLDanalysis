"""
fetch_data.py

Downloads historical XAUUSD (Gold/USD) market data using yfinance and
saves it as a raw CSV file inside data/raw/.

Usage (as a script):
    python scripts/fetch_data.py
    python scripts/fetch_data.py --start 2015-01-01 --end 2025-01-01 --interval 1d

Usage (as a module):
    from fetch_data import fetch_gold_data
    df = fetch_gold_data(start="2015-01-01", end="2025-01-01", interval="1d")
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

from config import DATA_RAW_DIR as RAW_DATA_DIR
from config import DEFAULT_YEARS_BACK, RAW_FILENAME
from config import TICKER


def _default_date_range() -> tuple[str, str]:
    """Return (start, end) date strings covering the default 10-year window."""
    end = datetime.today()
    start = end - timedelta(days=365 * DEFAULT_YEARS_BACK)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def fetch_gold_data(
    start: str | None = None,
    end: str | None = None,
    interval: str = "1d",
    ticker: str = TICKER,
    max_retries: int = 3,
) -> pd.DataFrame:
    """
    Download historical Gold (XAUUSD proxy) data from Yahoo Finance.

    Retries transient network/download failures with a short backoff before
    giving up, since Yahoo Finance occasionally rate-limits or times out.

    Args:
        start: Start date in 'YYYY-MM-DD' format. Defaults to 10 years ago.
        end: End date in 'YYYY-MM-DD' format. Defaults to today.
        interval: Data interval, e.g. '1d', '1h', '1wk'.
        ticker: Yahoo Finance ticker symbol to download.
        max_retries: Number of download attempts before raising.

    Returns:
        A pandas DataFrame with OHLCV data indexed by date.

    Raises:
        ValueError: If the download returns no data after all retries.
        RuntimeError: If the download fails for any other reason after all retries.
    """
    default_start, default_end = _default_date_range()
    start = start or default_start
    end = end or default_end

    print(f"Downloading {ticker} data from {start} to {end} (interval={interval})...")

    last_error: Exception | None = None
    df: pd.DataFrame | None = None

    for attempt in range(1, max_retries + 1):
        try:
            df = yf.download(
                ticker,
                start=start,
                end=end,
                interval=interval,
                progress=False,
                auto_adjust=False,
            )
            if df is not None and not df.empty:
                break
            last_error = ValueError(f"No data returned for ticker '{ticker}' on attempt {attempt}.")
        except Exception as exc:  # noqa: BLE001 - surface any network/library error clearly
            last_error = exc
            print(f"Attempt {attempt}/{max_retries} failed: {exc}")
        if attempt < max_retries:
            wait_seconds = attempt * 2
            print(f"Retrying in {wait_seconds}s...")
            time.sleep(wait_seconds)

    if df is None or df.empty:
        if isinstance(last_error, ValueError):
            raise ValueError(
                f"No data returned for ticker '{ticker}' after {max_retries} attempt(s). "
                "Check your internet connection, the ticker symbol, or the date range."
            )
        raise RuntimeError(f"Failed to download data for {ticker} after {max_retries} attempt(s): {last_error}")

    # yfinance sometimes returns MultiIndex columns for a single ticker; flatten them.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.index.name = "Date"
    df = df.reset_index()

    print(f"Downloaded {len(df)} rows.")
    return df


def save_raw_data(df: pd.DataFrame, filename: str = RAW_FILENAME) -> Path:
    """
    Save the downloaded DataFrame to data/raw/, safely overwriting old data.

    Args:
        df: DataFrame to save.
        filename: Output CSV filename.

    Returns:
        Path to the saved file.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RAW_DATA_DIR / filename

    if output_path.exists():
        print(f"Existing file found at {output_path}. It will be overwritten.")

    df.to_csv(output_path, index=False)
    print(f"Saved raw data to {output_path}")
    return output_path


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for standalone script execution."""
    parser = argparse.ArgumentParser(description="Download historical XAUUSD data.")
    parser.add_argument("--start", type=str, default=None, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", type=str, default=None, help="End date YYYY-MM-DD")
    parser.add_argument("--interval", type=str, default="1d", help="Data interval, e.g. 1d, 1h, 1wk")
    parser.add_argument("--filename", type=str, default=RAW_FILENAME, help="Output CSV filename")
    return parser.parse_args()


def main() -> None:
    """Entry point for command-line execution."""
    args = parse_args()
    try:
        df = fetch_gold_data(start=args.start, end=args.end, interval=args.interval)
        save_raw_data(df, filename=args.filename)
    except (ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
