"""Tests for scripts/indicators.py."""

from __future__ import annotations

import numpy as np

from indicators import (
    add_all_indicators,
    add_momentum_indicators,
    add_moving_averages,
    add_price_features,
    add_trend_indicators,
    add_volatility_indicators,
)


def test_add_price_features_adds_expected_columns(synthetic_ohlcv):
    """add_price_features should add Daily_Return, Log_Return, High_Low_Range, Candle_Body_Size."""
    df = add_price_features(synthetic_ohlcv)
    for col in ["Daily_Return", "Log_Return", "High_Low_Range", "Candle_Body_Size"]:
        assert col in df.columns

    # High-Low range should always be non-negative
    assert (df["High_Low_Range"] >= 0).all()
    # Candle body size should always be non-negative
    assert (df["Candle_Body_Size"] >= 0).all()


def test_add_moving_averages_adds_expected_columns(synthetic_ohlcv):
    """add_moving_averages should add SMA20, SMA50, EMA20, EMA50, EMA200."""
    df = add_moving_averages(synthetic_ohlcv)
    for col in ["SMA20", "SMA50", "EMA20", "EMA50", "EMA200"]:
        assert col in df.columns

    # SMA20 should be NaN for the first 19 rows (insufficient window)
    assert df["SMA20"].iloc[:19].isna().all()
    # SMA20 should be populated once the window is filled
    assert df["SMA20"].iloc[19:].notna().all()


def test_rsi_bounded_between_0_and_100(synthetic_ohlcv):
    """RSI14 values should always fall within [0, 100]."""
    df = add_momentum_indicators(synthetic_ohlcv)
    rsi_values = df["RSI14"].dropna()
    assert (rsi_values >= 0).all()
    assert (rsi_values <= 100).all()


def test_macd_histogram_equals_macd_minus_signal(synthetic_ohlcv):
    """MACD_Histogram should equal MACD - Signal for every row."""
    df = add_momentum_indicators(synthetic_ohlcv)
    diff = (df["MACD"] - df["Signal"]) - df["MACD_Histogram"]
    assert np.allclose(diff.dropna(), 0, atol=1e-9)


def test_atr_and_bollinger_bands_are_non_negative_width(synthetic_ohlcv):
    """ATR should be non-negative and Bollinger upper band should be >= lower band."""
    df = add_volatility_indicators(synthetic_ohlcv)
    assert (df["ATR14"].dropna() >= 0).all()

    band_diff = (df["BB_Upper"] - df["BB_Lower"]).dropna()
    assert (band_diff >= 0).all()


def test_trend_indicators_supertrend_labels_valid(synthetic_ohlcv):
    """SuperTrend should only ever be 'Bullish' or 'Bearish'."""
    df = add_trend_indicators(synthetic_ohlcv)
    assert set(df["SuperTrend"].unique()).issubset({"Bullish", "Bearish"})
    # ADX should be non-negative where defined
    assert (df["ADX"].dropna() >= 0).all()


def test_add_all_indicators_no_crash_and_preserves_row_count(synthetic_ohlcv):
    """The full indicator pipeline should run without error and preserve row count."""
    df = add_all_indicators(synthetic_ohlcv)
    assert len(df) == len(synthetic_ohlcv)
    # Should have added a substantial number of new columns
    assert len(df.columns) > len(synthetic_ohlcv.columns) + 15
