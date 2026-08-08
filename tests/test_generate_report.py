"""Tests for scripts/generate_report.py."""

from __future__ import annotations

from generate_report import build_report_text, save_report
from indicators import add_all_indicators


def test_build_report_text_contains_key_sections(synthetic_ohlcv):
    """The generated report should contain all expected section headers."""
    df = add_all_indicators(synthetic_ohlcv)
    report = build_report_text(df)

    for section in [
        "GOLD (XAUUSD) MARKET ANALYSIS REPORT",
        "OVERALL TREND",
        "VOLATILITY",
        "SEASONALITY",
        "NOTABLE MOVES",
        "PRICE RANGE",
        "RETURN DISTRIBUTION",
    ]:
        assert section in report


def test_build_report_text_is_non_empty_string(synthetic_ohlcv):
    """The report should be a substantial, non-empty string."""
    df = add_all_indicators(synthetic_ohlcv)
    report = build_report_text(df)
    assert isinstance(report, str)
    assert len(report) > 200


def test_save_report_writes_file(tmp_path, monkeypatch, synthetic_ohlcv):
    """save_report should write the report text to disk at the expected location."""
    import generate_report

    monkeypatch.setattr(generate_report, "REPORTS_DIR", tmp_path)

    df = add_all_indicators(synthetic_ohlcv)
    report_text = build_report_text(df)
    output_path = save_report(report_text, filename="test_report.txt")

    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == report_text
