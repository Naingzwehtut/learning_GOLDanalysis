"""
export_excel.py

Exports a multi-sheet Excel workbook summarizing the analysis: raw statistics,
market statistics, seasonality breakdowns, and a sample of the feature-enriched
data — useful for sharing results with non-technical stakeholders.

Usage (as a script):
    python scripts/export_excel.py
    # Produces reports/market_summary.xlsx

Usage (as a module):
    from export_excel import export_summary_workbook
    export_summary_workbook(df)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent))
from analysis import run_full_analysis  # noqa: E402
from config import FEATURES_FILENAME  # noqa: E402
from config import DATA_PROCESSED_DIR as PROCESSED_DATA_DIR  # noqa: E402
from config import REPORTS_DIR  # noqa: E402


def export_summary_workbook(df: pd.DataFrame, filename: str = "market_summary.xlsx") -> Path:
    """
    Build and save a multi-sheet Excel summary workbook.

    Sheets:
        - Return Stats: mean, median, std dev, skewness, kurtosis, etc.
        - Market Stats: highest/lowest close, largest gain/loss, average range.
        - Return by Year / Month / Weekday: seasonality breakdowns.
        - Data Sample: the most recent 250 rows of feature-enriched data.

    Args:
        df: Feature-enriched XAUUSD DataFrame.
        filename: Output filename inside reports/.

    Returns:
        Path to the saved workbook.
    """
    results = run_full_analysis(df)

    return_stats_df = pd.DataFrame(
        list(results["return_stats"].items()), columns=["Metric", "Value"]
    )
    market_stats_df = pd.DataFrame(
        list(results["market_stats"].items()), columns=["Metric", "Value"]
    )
    by_year_df = results["time_analysis"]["by_year"].rename("Avg Daily Return").reset_index()
    by_year_df.columns = ["Year", "Avg Daily Return"]
    by_month_df = results["time_analysis"]["by_month"].rename("Avg Daily Return").reset_index()
    by_month_df.columns = ["Month", "Avg Daily Return"]
    by_weekday_df = results["time_analysis"]["by_weekday"].rename("Avg Daily Return").reset_index()
    by_weekday_df.columns = ["Weekday", "Avg Daily Return"]

    data_sample = df.tail(250)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / filename

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        return_stats_df.to_excel(writer, sheet_name="Return Stats", index=False)
        market_stats_df.to_excel(writer, sheet_name="Market Stats", index=False)
        by_year_df.to_excel(writer, sheet_name="Return by Year", index=False)
        by_month_df.to_excel(writer, sheet_name="Return by Month", index=False)
        by_weekday_df.to_excel(writer, sheet_name="Return by Weekday", index=False)
        data_sample.to_excel(writer, sheet_name="Data Sample (last 250)", index=False)

    _autosize_columns(output_path)
    print(f"Saved Excel summary workbook to {output_path}")
    return output_path


def _autosize_columns(path: Path) -> None:
    """Widen Excel columns to roughly fit their content for readability."""
    from openpyxl import load_workbook

    wb = load_workbook(path)
    for sheet in wb.worksheets:
        for column_cells in sheet.columns:
            length = max((len(str(cell.value)) for cell in column_cells if cell.value is not None), default=10)
            col_letter = column_cells[0].column_letter
            sheet.column_dimensions[col_letter].width = min(max(length + 2, 10), 40)
    wb.save(path)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for standalone script execution."""
    parser = argparse.ArgumentParser(description="Export an Excel summary workbook for XAUUSD analysis.")
    parser.add_argument(
        "--input", type=str, default=str(PROCESSED_DATA_DIR / FEATURES_FILENAME), help="Path to feature CSV file"
    )
    parser.add_argument("--output", type=str, default="market_summary.xlsx", help="Output filename inside reports/")
    return parser.parse_args()


def main() -> None:
    """Entry point for command-line execution."""
    args = parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(input_path, parse_dates=["Date"])
    export_summary_workbook(df, filename=args.output)


if __name__ == "__main__":
    main()
