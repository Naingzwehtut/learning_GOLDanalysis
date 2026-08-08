"""Tests for scripts/analysis.py."""

from __future__ import annotations

from analysis import run_full_analysis, summarize_market, summarize_returns, time_based_returns
from indicators import add_all_indicators


def test_summarize_returns_keys_present(synthetic_ohlcv):
    """summarize_returns should return all expected statistical keys."""
    df = add_all_indicators(synthetic_ohlcv)
    stats = summarize_returns(df)

    expected_keys = {
        "mean_return", "median_return", "max_return", "min_return",
        "std_dev", "variance", "skewness", "kurtosis",
    }
    assert expected_keys.issubset(stats.keys())
    # Standard deviation and variance should be non-negative
    assert stats["std_dev"] >= 0
    assert stats["variance"] >= 0
    # Max return should be >= min return
    assert stats["max_return"] >= stats["min_return"]


def test_summarize_market_keys_present(synthetic_ohlcv):
    """summarize_market should return all expected market statistic keys."""
    df = add_all_indicators(synthetic_ohlcv)
    stats = summarize_market(df)

    expected_keys = {
        "highest_close", "lowest_close", "average_daily_range",
        "largest_gain_pct", "largest_gain_date", "largest_loss_pct", "largest_loss_date",
    }
    assert expected_keys.issubset(stats.keys())
    assert stats["highest_close"] >= stats["lowest_close"]
    assert stats["largest_gain_pct"] >= stats["largest_loss_pct"]


def test_time_based_returns_structure(synthetic_ohlcv):
    """time_based_returns should return by_year, by_month, and by_weekday series."""
    df = add_all_indicators(synthetic_ohlcv)
    results = time_based_returns(df)

    assert set(results.keys()) == {"by_year", "by_month", "by_weekday"}
    # Weekday index should never exceed 7 unique entries
    assert len(results["by_weekday"]) <= 7


def test_run_full_analysis_combines_all_sections(synthetic_ohlcv):
    """run_full_analysis should return a dict with return_stats, market_stats, and time_analysis."""
    df = add_all_indicators(synthetic_ohlcv)
    results = run_full_analysis(df)

    assert set(results.keys()) == {"return_stats", "market_stats", "time_analysis"}
