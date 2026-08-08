"""
config.py

Centralized configuration for the Gold Market Analysis project: file paths,
default ticker, and indicator window lengths. Importing constants from a
single place keeps scripts and notebooks consistent and avoids magic numbers
scattered across the codebase.
"""

from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
IMAGES_DIR = PROJECT_ROOT / "images"

RAW_FILENAME = "xauusd_raw.csv"
CLEAN_FILENAME = "xauusd_clean.csv"
FEATURES_FILENAME = "xauusd_features.csv"

# --------------------------------------------------------------------------- #
# Data source
# --------------------------------------------------------------------------- #
TICKER = "GC=F"  # COMEX Gold Futures — closest free Yahoo Finance proxy for XAUUSD spot
DEFAULT_YEARS_BACK = 10
DEFAULT_INTERVAL = "1d"

REQUIRED_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]

# --------------------------------------------------------------------------- #
# Indicator windows
# --------------------------------------------------------------------------- #
SMA_SHORT_WINDOW = 20
SMA_LONG_WINDOW = 50
EMA_SHORT_WINDOW = 20
EMA_MEDIUM_WINDOW = 50
EMA_LONG_WINDOW = 200

RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
ROC_PERIOD = 10

ATR_PERIOD = 14
BOLLINGER_WINDOW = 20
BOLLINGER_STD_MULTIPLIER = 2
HIST_VOL_WINDOW = 20
TRADING_DAYS_PER_YEAR = 252

ROLLING_STATS_WINDOW = 20

ADX_PERIOD = 14
SUPERTREND_PERIOD = 10
SUPERTREND_MULTIPLIER = 3.0

# --------------------------------------------------------------------------- #
# Report thresholds
# --------------------------------------------------------------------------- #
TREND_THRESHOLD_PCT = 5.0  # +/- % change over the period to call it an up/down trend
