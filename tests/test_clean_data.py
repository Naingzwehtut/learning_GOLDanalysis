"""Tests for scripts/clean_data.py."""

from __future__ import annotations

import pandas as pd
import pytest

from clean_data import (
    clean_gold_data,
    convert_date_format,
    handle_missing_values,
    remove_duplicates,
    sort_ascending,
    validate_columns,
)


def test_validate_columns_passes_with_all_required(synthetic_ohlcv):
    """validate_columns should not raise when all required columns are present."""
    validate_columns(synthetic_ohlcv)  # should not raise


def test_validate_columns_raises_when_missing():
    """validate_columns should raise ValueError when a required column is missing."""
    df = pd.DataFrame({"Date": [1, 2], "Open": [1, 2]})
    with pytest.raises(ValueError, match="Missing required column"):
        validate_columns(df)


def test_remove_duplicates_drops_duplicate_dates(synthetic_ohlcv_with_issues):
    """Duplicate rows sharing the same Date should be reduced to one occurrence."""
    df = convert_date_format(synthetic_ohlcv_with_issues)
    before = len(df)
    after = remove_duplicates(df)
    assert len(after) < before
    assert after["Date"].duplicated().sum() == 0


def test_handle_missing_values_leaves_no_nans(synthetic_ohlcv_with_issues):
    """After handling missing values, no NaNs should remain in required columns."""
    df = convert_date_format(synthetic_ohlcv_with_issues)
    df = handle_missing_values(df)
    assert df[["Open", "High", "Low", "Close", "Volume"]].isna().sum().sum() == 0


def test_sort_ascending_orders_by_date(synthetic_ohlcv):
    """sort_ascending should return rows ordered from earliest to latest date."""
    shuffled = synthetic_ohlcv.sample(frac=1, random_state=1).reset_index(drop=True)
    shuffled = convert_date_format(shuffled)
    sorted_df = sort_ascending(shuffled)
    assert sorted_df["Date"].is_monotonic_increasing


def test_clean_gold_data_end_to_end(synthetic_ohlcv_with_issues):
    """The full cleaning pipeline should produce a sorted, deduplicated, NaN-free DataFrame."""
    cleaned = clean_gold_data(synthetic_ohlcv_with_issues)

    assert cleaned["Date"].is_monotonic_increasing
    assert cleaned["Date"].duplicated().sum() == 0
    assert cleaned.isna().sum().sum() == 0
    assert (cleaned["High"] >= cleaned["Low"]).all()


def test_clean_gold_data_raises_on_missing_columns():
    """clean_gold_data should raise ValueError if required columns are absent."""
    df = pd.DataFrame({"Date": ["2022-01-01"], "Open": [1]})
    with pytest.raises(ValueError):
        clean_gold_data(df)
