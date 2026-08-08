"""
generate_report.py

Generates an automated, human-readable text report summarizing overall
trend, volatility, strongest/weakest month, and largest gain/loss for
the XAUUSD market, saved into reports/.

Usage (as a script):
    python scripts/generate_report.py

Usage (as a module):
    from generate_report import build_report_text, save_report
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Support running both as a package module and as a standalone script
sys.path.append(str(Path(__file__).resolve().parent))
from analysis import run_full_analysis  # noqa: E402
from config import FEATURES_FILENAME, TREND_THRESHOLD_PCT  # noqa: E402
from config import DATA_PROCESSED_DIR as PROCESSED_DATA_DIR  # noqa: E402
from config import REPORTS_DIR  # noqa: E402


def _determine_overall_trend(df: pd.DataFrame) -> str:
    """Classify the overall trend by comparing first and last close prices."""
    first_close = df["Close"].iloc[0]
    last_close = df["Close"].iloc[-1]
    pct_change = (last_close - first_close) / first_close * 100

    if pct_change > TREND_THRESHOLD_PCT:
        direction = "Uptrend"
    elif pct_change < -TREND_THRESHOLD_PCT:
        direction = "Downtrend"
    else:
        direction = "Sideways / Range-bound"

    return f"{direction} ({pct_change:+.2f}% over the analyzed period)"


def build_report_text(df: pd.DataFrame) -> str:
    """
    Build a formatted text report string summarizing key market insights.

    Args:
        df: Feature-enriched XAUUSD DataFrame.

    Returns:
        The full report as a formatted string.
    """
    results = run_full_analysis(df)
    return_stats = results["return_stats"]
    market_stats = results["market_stats"]
    by_month = results["time_analysis"]["by_month"]

    strongest_month = by_month.idxmax()
    weakest_month = by_month.idxmin()

    trend = _determine_overall_trend(df)
    annualized_vol_pct = return_stats["std_dev"] * (252 ** 0.5) * 100

    lines = [
        "=" * 60,
        "GOLD (XAUUSD) MARKET ANALYSIS REPORT",
        "=" * 60,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Period: {df['Date'].min()} to {df['Date'].max()}",
        f"Total trading days analyzed: {len(df)}",
        "",
        "-- OVERALL TREND --",
        f"Trend: {trend}",
        f"Latest Close: {df['Close'].iloc[-1]:.2f}",
        "",
        "-- VOLATILITY --",
        f"Daily return standard deviation: {return_stats['std_dev'] * 100:.3f}%",
        f"Estimated annualized volatility: {annualized_vol_pct:.2f}%",
        f"Average daily trading range: {market_stats['average_daily_range']:.2f}",
        "",
        "-- SEASONALITY --",
        f"Strongest month (avg. return): {strongest_month} ({by_month[strongest_month] * 100:.3f}%)",
        f"Weakest month (avg. return): {weakest_month} ({by_month[weakest_month] * 100:.3f}%)",
        "",
        "-- NOTABLE MOVES --",
        f"Largest single-day gain: {market_stats['largest_gain_pct'] * 100:.2f}% on {market_stats['largest_gain_date']}",
        f"Largest single-day loss: {market_stats['largest_loss_pct'] * 100:.2f}% on {market_stats['largest_loss_date']}",
        "",
        "-- PRICE RANGE --",
        f"Highest close: {market_stats['highest_close']:.2f}",
        f"Lowest close: {market_stats['lowest_close']:.2f}",
        "",
        "-- RETURN DISTRIBUTION --",
        f"Mean daily return: {return_stats['mean_return'] * 100:.4f}%",
        f"Median daily return: {return_stats['median_return'] * 100:.4f}%",
        f"Skewness: {return_stats['skewness']:.3f}",
        f"Kurtosis: {return_stats['kurtosis']:.3f}",
        "=" * 60,
        "Disclaimer: This report is generated for educational and portfolio",
        "purposes only. It does not constitute financial advice.",
        "=" * 60,
    ]

    return "\n".join(lines)


def save_report(report_text: str, filename: str | None = None) -> Path:
    """Save the report text to reports/, timestamped by default."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if filename is None:
        filename = f"market_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    output_path = REPORTS_DIR / filename
    output_path.write_text(report_text, encoding="utf-8")
    print(f"Saved report to {output_path}")
    return output_path


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for standalone script execution."""
    parser = argparse.ArgumentParser(description="Generate an automated XAUUSD market report.")
    parser.add_argument(
        "--input", type=str, default=str(PROCESSED_DATA_DIR / FEATURES_FILENAME), help="Path to feature CSV file"
    )
    parser.add_argument("--output", type=str, default=None, help="Output filename inside reports/")
    return parser.parse_args()


def main() -> None:
    """Entry point for command-line execution."""
    args = parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(input_path, parse_dates=["Date"])
    report_text = build_report_text(df)
    print(report_text)
    save_report(report_text, filename=args.output)


if __name__ == "__main__":
    main()
