"""
run_pipeline.py

Runs the entire Gold Market Analysis pipeline end-to-end in one command:
fetch -> clean -> indicators -> analysis -> dashboard -> report.

Usage:
    python scripts/run_pipeline.py
    python scripts/run_pipeline.py --start 2015-01-01 --end 2025-01-01 --interval 1d
    python scripts/run_pipeline.py --skip-fetch   # reuse existing data/raw/xauusd_raw.csv
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from analysis import run_full_analysis  # noqa: E402
from clean_data import clean_gold_data, save_processed_data  # noqa: E402
from config import (  # noqa: E402
    DATA_PROCESSED_DIR,
    DATA_RAW_DIR,
    FEATURES_FILENAME,
    RAW_FILENAME,
    REPORTS_DIR,
)
from dashboard import build_dashboard  # noqa: E402
from fetch_data import fetch_gold_data, save_raw_data  # noqa: E402
from generate_report import build_report_text, save_report  # noqa: E402
from indicators import add_all_indicators  # noqa: E402

import pandas as pd  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pipeline")


def run_pipeline(
    start: str | None = None,
    end: str | None = None,
    interval: str = "1d",
    skip_fetch: bool = False,
) -> None:
    """
    Execute the full pipeline: fetch, clean, engineer features, analyze,
    build the dashboard, and generate the report.

    Args:
        start: Start date 'YYYY-MM-DD' for the data download. Defaults to 10 years back.
        end: End date 'YYYY-MM-DD' for the data download. Defaults to today.
        interval: Data interval, e.g. '1d', '1h', '1wk'.
        skip_fetch: If True, reuse the existing raw CSV instead of downloading again.
    """
    pipeline_start = time.time()
    logger.info("Starting Gold Market Analysis pipeline")

    # Step 1: Fetch
    if skip_fetch:
        raw_path = DATA_RAW_DIR / RAW_FILENAME
        if not raw_path.exists():
            logger.error("Skip-fetch requested but no raw data found at %s", raw_path)
            sys.exit(1)
        logger.info("[1/6] Skipping fetch, using existing %s", raw_path)
        df_raw = pd.read_csv(raw_path)
    else:
        logger.info("[1/6] Fetching data...")
        df_raw = fetch_gold_data(start=start, end=end, interval=interval)
        save_raw_data(df_raw)

    # Step 2: Clean
    logger.info("[2/6] Cleaning data...")
    df_clean = clean_gold_data(df_raw)
    save_processed_data(df_clean)

    # Step 3: Feature engineering
    logger.info("[3/6] Calculating indicators...")
    df_features = add_all_indicators(df_clean)
    features_path = DATA_PROCESSED_DIR / FEATURES_FILENAME
    df_features.to_csv(features_path, index=False)
    logger.info(
        "Saved feature-enriched data to %s (%d rows, %d cols)",
        features_path, len(df_features), len(df_features.columns),
    )

    # Step 4: Analysis
    logger.info("[4/6] Running statistical analysis...")
    results = run_full_analysis(df_features)
    logger.info(
        "Mean daily return: %.4f%% | Std dev: %.4f%%",
        results["return_stats"]["mean_return"] * 100,
        results["return_stats"]["std_dev"] * 100,
    )

    # Step 5: Dashboard
    logger.info("[5/6] Building dashboard...")
    fig = build_dashboard(df_features)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    dashboard_path = REPORTS_DIR / "dashboard.html"
    fig.write_html(str(dashboard_path))
    logger.info("Saved dashboard to %s", dashboard_path)

    # Step 6: Report
    logger.info("[6/6] Generating report...")
    report_text = build_report_text(df_features)
    save_report(report_text, filename="market_report.txt")

    elapsed = time.time() - pipeline_start
    logger.info("Pipeline complete in %.1fs", elapsed)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for standalone script execution."""
    parser = argparse.ArgumentParser(description="Run the full Gold Market Analysis pipeline.")
    parser.add_argument("--start", type=str, default=None, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", type=str, default=None, help="End date YYYY-MM-DD")
    parser.add_argument("--interval", type=str, default="1d", help="Data interval, e.g. 1d, 1h, 1wk")
    parser.add_argument(
        "--skip-fetch", action="store_true", help="Reuse existing data/raw/xauusd_raw.csv instead of downloading"
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for command-line execution."""
    args = parse_args()
    try:
        run_pipeline(start=args.start, end=args.end, interval=args.interval, skip_fetch=args.skip_fetch)
    except Exception as exc:  # noqa: BLE001 - top-level catch to log and exit cleanly
        logger.error("Pipeline failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
