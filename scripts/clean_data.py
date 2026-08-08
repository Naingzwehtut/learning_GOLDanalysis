"""
clean_data.py

Cleans and validates raw XAUUSD market data, producing an analysis-ready
CSV file inside data/processed/.

Usage (as a script):
    python scripts/clean_data.py
    python scripts/clean_data.py --input data/raw/xauusd_raw.csv

Usage (as a module):
    from clean_data import clean_gold_data
    df_clean = clean_gold_data(df_raw)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from config import CLEAN_FILENAME, RAW_FILENAME, REQUIRED_COLUMNS
from config import DATA_PROCESSED_DIR as PROCESSED_DATA_DIR
from config import DATA_RAW_DIR as RAW_DATA_DIR


def validate_columns(df: pd.DataFrame) -> None:
    """
    Ensure the DataFrame contains all required OHLCV columns.

    Raises:
        ValueError: If any required column is missing.
    """
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {missing}. Found columns: {list(df.columns)}")


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate rows based on the Date column, keeping the first occurrence."""
    before = len(df)
    df = df.drop_duplicates(subset="Date", keep="first")
    removed = before - len(df)
    if removed:
        print(f"Removed {removed} duplicate row(s).")
    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values in OHLCV columns.

    Strategy:
        - Forward-fill price columns (Open, High, Low, Close) since gaps are
          typically non-trading days rather than true missing observations.
        - Fill missing Volume with 0.
        - Drop any remaining rows that still contain NaNs (e.g. leading gaps).
    """
    price_cols = ["Open", "High", "Low", "Close"]
    missing_before = df[REQUIRED_COLUMNS].isna().sum().sum()

    df[price_cols] = df[price_cols].ffill()
    df["Volume"] = df["Volume"].fillna(0)
    df = df.dropna(subset=REQUIRED_COLUMNS)

    missing_after = df[REQUIRED_COLUMNS].isna().sum().sum()
    print(f"Missing values: {missing_before} -> {missing_after}")
    return df


def convert_date_format(df: pd.DataFrame) -> pd.DataFrame:
    """Convert the Date column to pandas datetime dtype."""
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    n_invalid = df["Date"].isna().sum()
    if n_invalid:
        print(f"Dropping {n_invalid} row(s) with unparseable dates.")
        df = df.dropna(subset=["Date"])
    return df


def sort_ascending(df: pd.DataFrame) -> pd.DataFrame:
    """Sort the DataFrame by Date in ascending order and reset the index."""
    return df.sort_values("Date").reset_index(drop=True)


def clean_gold_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run the full cleaning pipeline on raw gold market data.

    Args:
        df: Raw OHLCV DataFrame.

    Returns:
        A cleaned, validated, and sorted DataFrame.
    """
    df = df.copy()
    validate_columns(df)
    df = convert_date_format(df)
    df = remove_duplicates(df)
    df = handle_missing_values(df)
    df = sort_ascending(df)

    # Sanity check: High should be >= Low for every row
    invalid_rows = df[df["High"] < df["Low"]]
    if not invalid_rows.empty:
        print(f"Warning: {len(invalid_rows)} row(s) have High < Low and will be dropped.")
        df = df[df["High"] >= df["Low"]].reset_index(drop=True)

    return df


def save_processed_data(df: pd.DataFrame, filename: str = CLEAN_FILENAME) -> Path:
    """Save cleaned data to data/processed/."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DATA_DIR / filename
    df.to_csv(output_path, index=False)
    print(f"Saved cleaned data to {output_path} ({len(df)} rows).")
    return output_path


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for standalone script execution."""
    parser = argparse.ArgumentParser(description="Clean raw XAUUSD market data.")
    parser.add_argument(
        "--input", type=str, default=str(RAW_DATA_DIR / RAW_FILENAME), help="Path to raw CSV file"
    )
    parser.add_argument(
        "--output", type=str, default=CLEAN_FILENAME, help="Output filename inside data/processed/"
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for command-line execution."""
    args = parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    df_raw = pd.read_csv(input_path)
    try:
        df_clean = clean_gold_data(df_raw)
        save_processed_data(df_clean, filename=args.output)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
