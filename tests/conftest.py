"""
conftest.py

Shared pytest fixtures for the Gold Market Analysis test suite.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Make scripts/ importable from tests/
sys.path.append(str(Path(__file__).resolve().parent.parent / "scripts"))


@pytest.fixture
def synthetic_ohlcv() -> pd.DataFrame:
    """
    Generate a small, deterministic synthetic OHLCV DataFrame for testing.

    Uses a fixed random seed so tests are reproducible.
    """
    rng = np.random.default_rng(42)
    n = 300
    dates = pd.date_range("2022-01-01", periods=n, freq="D")
    price = 1800 + np.cumsum(rng.normal(0, 5, n))

    df = pd.DataFrame({
        "Date": dates,
        "Open": price + rng.normal(0, 1, n),
        "High": price + np.abs(rng.normal(0, 3, n)),
        "Low": price - np.abs(rng.normal(0, 3, n)),
        "Close": price,
        "Volume": rng.integers(1000, 5000, n),
    })
    return df


@pytest.fixture
def synthetic_ohlcv_with_issues(synthetic_ohlcv: pd.DataFrame) -> pd.DataFrame:
    """Synthetic OHLCV data with injected duplicates and missing values for cleaning tests."""
    df = synthetic_ohlcv.copy()

    # Inject a duplicate row
    df = pd.concat([df, df.iloc[[5]]], ignore_index=True)

    # Inject missing values
    df.loc[10, "Close"] = np.nan
    df.loc[20, "Volume"] = np.nan

    return df
