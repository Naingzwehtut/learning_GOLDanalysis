"""
indicators.py

Calculates price, moving average, momentum, volatility, statistical, and
trend indicators for cleaned XAUUSD market data.

Usage (as a script):
    python scripts/indicators.py

Usage (as a module):
    from indicators import add_all_indicators
    df_features = add_all_indicators(df_clean)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from config import (
    ADX_PERIOD,
    ATR_PERIOD,
    BOLLINGER_STD_MULTIPLIER,
    BOLLINGER_WINDOW,
    CLEAN_FILENAME,
    EMA_LONG_WINDOW,
    EMA_MEDIUM_WINDOW,
    EMA_SHORT_WINDOW,
    FEATURES_FILENAME,
    HIST_VOL_WINDOW,
    MACD_FAST,
    MACD_SIGNAL,
    MACD_SLOW,
    ROC_PERIOD,
    ROLLING_STATS_WINDOW,
    RSI_PERIOD,
    SMA_LONG_WINDOW,
    SMA_SHORT_WINDOW,
    SUPERTREND_MULTIPLIER,
    SUPERTREND_PERIOD,
    TRADING_DAYS_PER_YEAR,
)
from config import DATA_PROCESSED_DIR as PROCESSED_DATA_DIR


# --------------------------------------------------------------------------- #
# Price-based features
# --------------------------------------------------------------------------- #
def add_price_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add Daily Return, Log Return, High-Low Range, and Candle Body Size."""
    df = df.copy()
    df["Daily_Return"] = df["Close"].pct_change()
    df["Log_Return"] = np.log(df["Close"] / df["Close"].shift(1))
    df["High_Low_Range"] = df["High"] - df["Low"]
    df["Candle_Body_Size"] = (df["Close"] - df["Open"]).abs()
    return df


# --------------------------------------------------------------------------- #
# Moving averages
# --------------------------------------------------------------------------- #
def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Add SMA20, SMA50, EMA20, EMA50, EMA200."""
    df = df.copy()
    df["SMA20"] = df["Close"].rolling(window=SMA_SHORT_WINDOW).mean()
    df["SMA50"] = df["Close"].rolling(window=SMA_LONG_WINDOW).mean()
    df["EMA20"] = df["Close"].ewm(span=EMA_SHORT_WINDOW, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=EMA_MEDIUM_WINDOW, adjust=False).mean()
    df["EMA200"] = df["Close"].ewm(span=EMA_LONG_WINDOW, adjust=False).mean()
    return df


# --------------------------------------------------------------------------- #
# Momentum indicators
# --------------------------------------------------------------------------- #
def _rsi(series: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    """Compute the Relative Strength Index using Wilder's smoothing method."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def add_momentum_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add RSI14, MACD, Signal line, MACD Histogram, and Rate of Change."""
    df = df.copy()
    df["RSI14"] = _rsi(df["Close"], period=RSI_PERIOD)

    ema_fast = df["Close"].ewm(span=MACD_FAST, adjust=False).mean()
    ema_slow = df["Close"].ewm(span=MACD_SLOW, adjust=False).mean()
    df["MACD"] = ema_fast - ema_slow
    df["Signal"] = df["MACD"].ewm(span=MACD_SIGNAL, adjust=False).mean()
    df["MACD_Histogram"] = df["MACD"] - df["Signal"]

    df["ROC"] = df["Close"].pct_change(periods=ROC_PERIOD) * 100
    return df


# --------------------------------------------------------------------------- #
# Volatility indicators
# --------------------------------------------------------------------------- #
def _atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    """Compute the Average True Range."""
    prev_close = df["Close"].shift(1)
    tr = pd.concat(
        [
            df["High"] - df["Low"],
            (df["High"] - prev_close).abs(),
            (df["Low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


def add_volatility_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add ATR14, Bollinger Bands (20, 2 std), and 20-day Historical Volatility."""
    df = df.copy()
    df["ATR14"] = _atr(df, period=ATR_PERIOD)

    sma = df["Close"].rolling(window=BOLLINGER_WINDOW).mean()
    std = df["Close"].rolling(window=BOLLINGER_WINDOW).std()
    df["BB_Middle"] = sma
    df["BB_Upper"] = sma + (BOLLINGER_STD_MULTIPLIER * std)
    df["BB_Lower"] = sma - (BOLLINGER_STD_MULTIPLIER * std)

    # Annualized historical volatility from log returns
    log_return = np.log(df["Close"] / df["Close"].shift(1))
    df["Historical_Volatility"] = log_return.rolling(window=HIST_VOL_WINDOW).std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    return df


# --------------------------------------------------------------------------- #
# Rolling statistics
# --------------------------------------------------------------------------- #
def add_rolling_statistics(df: pd.DataFrame, window: int = ROLLING_STATS_WINDOW) -> pd.DataFrame:
    """Add Rolling Mean, Rolling Standard Deviation, and Rolling Volatility of returns."""
    df = df.copy()
    if "Daily_Return" not in df.columns:
        df["Daily_Return"] = df["Close"].pct_change()

    df[f"Rolling_Mean_{window}"] = df["Close"].rolling(window=window).mean()
    df[f"Rolling_Std_{window}"] = df["Close"].rolling(window=window).std()
    df[f"Rolling_Volatility_{window}"] = df["Daily_Return"].rolling(window=window).std()
    return df


# --------------------------------------------------------------------------- #
# Trend indicators
# --------------------------------------------------------------------------- #
def _adx(df: pd.DataFrame, period: int = ADX_PERIOD) -> pd.Series:
    """Compute the Average Directional Index (ADX)."""
    high, low, close = df["High"], df["Low"], df["Close"]

    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    atr = _atr(df, period=period)

    plus_dm_smooth = pd.Series(plus_dm, index=df.index).ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    minus_dm_smooth = pd.Series(minus_dm, index=df.index).ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    plus_di = 100 * (plus_dm_smooth / atr)
    minus_di = 100 * (minus_dm_smooth / atr)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx = dx.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    return adx


def _supertrend(df: pd.DataFrame, period: int = SUPERTREND_PERIOD, multiplier: float = SUPERTREND_MULTIPLIER) -> pd.Series:
    """
    Compute the SuperTrend indicator.

    Returns:
        A Series of 'Bullish' / 'Bearish' trend labels.
    """
    atr = _atr(df, period=period)
    hl2 = (df["High"] + df["Low"]) / 2

    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)

    trend = pd.Series(index=df.index, dtype="object")
    trend.iloc[0] = "Bullish"

    final_upper = upper_band.copy()
    final_lower = lower_band.copy()

    for i in range(1, len(df)):
        close = df["Close"].iloc[i]
        prev_close = df["Close"].iloc[i - 1]

        # Carry bands forward unless price breaks through
        if upper_band.iloc[i] < final_upper.iloc[i - 1] or prev_close > final_upper.iloc[i - 1]:
            final_upper.iloc[i] = upper_band.iloc[i]
        else:
            final_upper.iloc[i] = final_upper.iloc[i - 1]

        if lower_band.iloc[i] > final_lower.iloc[i - 1] or prev_close < final_lower.iloc[i - 1]:
            final_lower.iloc[i] = lower_band.iloc[i]
        else:
            final_lower.iloc[i] = final_lower.iloc[i - 1]

        if close > final_upper.iloc[i - 1]:
            trend.iloc[i] = "Bullish"
        elif close < final_lower.iloc[i - 1]:
            trend.iloc[i] = "Bearish"
        else:
            trend.iloc[i] = trend.iloc[i - 1]

    return trend


def add_trend_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add ADX and SuperTrend."""
    df = df.copy()
    df["ADX"] = _adx(df, period=ADX_PERIOD)
    df["SuperTrend"] = _supertrend(df, period=SUPERTREND_PERIOD, multiplier=SUPERTREND_MULTIPLIER)
    return df


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run the full indicator pipeline: price, moving averages, momentum,
    volatility, rolling statistics, and trend.

    Args:
        df: Cleaned OHLCV DataFrame, sorted ascending by Date.

    Returns:
        DataFrame enriched with all technical indicators.
    """
    df = df.copy()
    df = add_price_features(df)
    df = add_moving_averages(df)
    df = add_momentum_indicators(df)
    df = add_volatility_indicators(df)
    df = add_rolling_statistics(df)
    df = add_trend_indicators(df)
    return df


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for standalone script execution."""
    parser = argparse.ArgumentParser(description="Calculate technical indicators for XAUUSD data.")
    parser.add_argument(
        "--input", type=str, default=str(PROCESSED_DATA_DIR / CLEAN_FILENAME), help="Path to cleaned CSV file"
    )
    parser.add_argument(
        "--output", type=str, default=FEATURES_FILENAME, help="Output filename inside data/processed/"
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for command-line execution."""
    args = parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(input_path, parse_dates=["Date"])
    df_features = add_all_indicators(df)

    output_path = PROCESSED_DATA_DIR / args.output
    df_features.to_csv(output_path, index=False)
    print(f"Saved feature-enriched data to {output_path} ({len(df_features)} rows, {len(df_features.columns)} columns).")


if __name__ == "__main__":
    main()
