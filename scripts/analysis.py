"""
analysis.py

Performs statistical and time-based analysis on feature-enriched XAUUSD data:
return statistics, market statistics, and return breakdowns by year/month/weekday.

Usage (as a script):
    python scripts/analysis.py

Usage (as a module):
    from analysis import summarize_returns, summarize_market, time_based_returns
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from scipy import stats

from config import FEATURES_FILENAME
from config import DATA_PROCESSED_DIR as PROCESSED_DATA_DIR


def summarize_returns(df: pd.DataFrame) -> dict[str, float]:
    """
    Compute summary statistics for daily returns.

    Args:
        df: DataFrame containing a 'Daily_Return' column.

    Returns:
        Dictionary of return statistics.
    """
    returns = df["Daily_Return"].dropna()
    return {
        "mean_return": returns.mean(),
        "median_return": returns.median(),
        "max_return": returns.max(),
        "min_return": returns.min(),
        "std_dev": returns.std(),
        "variance": returns.var(),
        "skewness": stats.skew(returns),
        "kurtosis": stats.kurtosis(returns),
    }


def summarize_market(df: pd.DataFrame) -> dict[str, float]:
    """
    Compute high-level market statistics.

    Args:
        df: DataFrame containing OHLC columns and 'High_Low_Range' / 'Daily_Return'.

    Returns:
        Dictionary of market statistics.
    """
    daily_range = df["High_Low_Range"] if "High_Low_Range" in df.columns else (df["High"] - df["Low"])
    returns = df["Daily_Return"].dropna() if "Daily_Return" in df.columns else df["Close"].pct_change().dropna()

    largest_gain_idx = returns.idxmax()
    largest_loss_idx = returns.idxmin()

    return {
        "highest_close": df["Close"].max(),
        "lowest_close": df["Close"].min(),
        "average_daily_range": daily_range.mean(),
        "largest_gain_pct": returns.max(),
        "largest_gain_date": str(df.loc[largest_gain_idx, "Date"]),
        "largest_loss_pct": returns.min(),
        "largest_loss_date": str(df.loc[largest_loss_idx, "Date"]),
    }


def time_based_returns(df: pd.DataFrame) -> dict[str, pd.Series]:
    """
    Compute average return breakdowns by year, month, and weekday.

    Args:
        df: DataFrame containing 'Date' and 'Daily_Return' columns.

    Returns:
        Dictionary with 'by_year', 'by_month', and 'by_weekday' Series.
    """
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    if "Daily_Return" not in df.columns:
        df["Daily_Return"] = df["Close"].pct_change()

    by_year = df.groupby(df["Date"].dt.year)["Daily_Return"].mean()
    by_month = df.groupby(df["Date"].dt.month_name())["Daily_Return"].mean()
    by_weekday = df.groupby(df["Date"].dt.day_name())["Daily_Return"].mean()

    # Order month/weekday naturally rather than alphabetically
    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    by_month = by_month.reindex([m for m in month_order if m in by_month.index])
    by_weekday = by_weekday.reindex([d for d in weekday_order if d in by_weekday.index])

    return {"by_year": by_year, "by_month": by_month, "by_weekday": by_weekday}


def run_full_analysis(df: pd.DataFrame) -> dict:
    """Run all analysis functions and return a combined results dictionary."""
    return {
        "return_stats": summarize_returns(df),
        "market_stats": summarize_market(df),
        "time_analysis": time_based_returns(df),
    }


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for standalone script execution."""
    parser = argparse.ArgumentParser(description="Run statistical analysis on XAUUSD feature data.")
    parser.add_argument(
        "--input", type=str, default=str(PROCESSED_DATA_DIR / FEATURES_FILENAME), help="Path to feature CSV file"
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for command-line execution: prints analysis results to the console."""
    args = parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(input_path, parse_dates=["Date"])
    results = run_full_analysis(df)

    print("\n=== Return Statistics ===")
    for key, value in results["return_stats"].items():
        print(f"{key}: {value:.6f}")

    print("\n=== Market Statistics ===")
    for key, value in results["market_stats"].items():
        print(f"{key}: {value}")

    print("\n=== Average Return by Year ===")
    print(results["time_analysis"]["by_year"])

    print("\n=== Average Return by Month ===")
    print(results["time_analysis"]["by_month"])

    print("\n=== Average Return by Weekday ===")
    print(results["time_analysis"]["by_weekday"])


if __name__ == "__main__":
    main()
