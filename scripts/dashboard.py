"""
dashboard.py

Builds an interactive Plotly dashboard for XAUUSD market data: KPI cards
plus a grid of charts (candlestick, moving averages, RSI, MACD, Bollinger
Bands, return distribution, monthly returns, and volatility).

Usage (as a script):
    python scripts/dashboard.py
    # Produces reports/dashboard.html

Usage (as a module, e.g. inside notebooks/05_dashboard.ipynb):
    from dashboard import build_dashboard
    fig = build_dashboard(df)
    fig.show()
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import FEATURES_FILENAME
from config import DATA_PROCESSED_DIR as PROCESSED_DATA_DIR
from config import REPORTS_DIR


def compute_kpis(df: pd.DataFrame) -> dict[str, float]:
    """Compute headline KPI values from the feature-enriched DataFrame."""
    daily_return = df["Daily_Return"] if "Daily_Return" in df.columns else df["Close"].pct_change()
    daily_range = df["High_Low_Range"] if "High_Low_Range" in df.columns else (df["High"] - df["Low"])

    return {
        "latest_price": df["Close"].iloc[-1],
        "highest_price": df["Close"].max(),
        "lowest_price": df["Close"].min(),
        "avg_daily_return_pct": daily_return.mean() * 100,
        "avg_daily_range": daily_range.mean(),
    }


def _add_kpi_annotations(fig: go.Figure, kpis: dict[str, float]) -> None:
    """Add a row of KPI card annotations to the top of the dashboard figure."""
    labels = [
        ("Latest Price", f"${kpis['latest_price']:.2f}"),
        ("Highest Price", f"${kpis['highest_price']:.2f}"),
        ("Lowest Price", f"${kpis['lowest_price']:.2f}"),
        ("Avg Daily Return", f"{kpis['avg_daily_return_pct']:.3f}%"),
        ("Avg Daily Range", f"${kpis['avg_daily_range']:.2f}"),
    ]
    n = len(labels)
    for i, (label, value) in enumerate(labels):
        x_pos = (i + 0.5) / n
        fig.add_annotation(
            x=x_pos, y=1.045, xref="paper", yref="paper",
            text=f"<b>{value}</b><br><span style='font-size:11px;color:#666'>{label}</span>",
            showarrow=False, align="center", font=dict(size=16),
        )


def build_dashboard(df: pd.DataFrame, title: str = "Gold (XAUUSD) Market Analysis Dashboard") -> go.Figure:
    """
    Build the full interactive Plotly dashboard.

    Args:
        df: Feature-enriched XAUUSD DataFrame (output of indicators.add_all_indicators).
        title: Dashboard title.

    Returns:
        A Plotly Figure containing all charts as subplots.
    """
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    kpis = compute_kpis(df)

    # Monthly returns for the bar chart
    monthly_returns = (
        df.set_index("Date")["Daily_Return"]
        .resample("ME")
        .apply(lambda x: (1 + x).prod() - 1)
        * 100
    )

    fig = make_subplots(
        rows=4, cols=2,
        subplot_titles=(
            "Candlestick with EMA20/50/200", "Closing Price with SMA20/SMA50",
            "RSI (14)", "MACD",
            "Bollinger Bands (20, 2σ)", "Daily Return Distribution",
            "Monthly Returns (%)", "Historical Volatility (Annualized)",
        ),
        vertical_spacing=0.07, horizontal_spacing=0.08,
        specs=[[{}, {}], [{}, {}], [{}, {}], [{}, {}]],
    )

    # Row 1, Col 1: Candlestick + EMAs
    fig.add_trace(go.Candlestick(
        x=df["Date"], open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name="Price", showlegend=False,
    ), row=1, col=1)
    for col, color in [("EMA20", "#f39c12"), ("EMA50", "#3498db"), ("EMA200", "#9b59b6")]:
        if col in df.columns:
            fig.add_trace(go.Scatter(x=df["Date"], y=df[col], name=col, line=dict(width=1.3, color=color)), row=1, col=1)

    # Row 1, Col 2: Close + SMA20/SMA50
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], name="Close", line=dict(color="#2c3e50"), showlegend=False), row=1, col=2)
    for col, color in [("SMA20", "#e67e22"), ("SMA50", "#16a085")]:
        if col in df.columns:
            fig.add_trace(go.Scatter(x=df["Date"], y=df[col], name=col, line=dict(width=1.3, color=color)), row=1, col=2)

    # Row 2, Col 1: RSI
    if "RSI14" in df.columns:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["RSI14"], name="RSI14", line=dict(color="#8e44ad"), showlegend=False), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    # Row 2, Col 2: MACD
    if "MACD" in df.columns:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["MACD"], name="MACD", line=dict(color="#2980b9")), row=2, col=2)
        fig.add_trace(go.Scatter(x=df["Date"], y=df["Signal"], name="Signal", line=dict(color="#e74c3c")), row=2, col=2)
        fig.add_trace(go.Bar(x=df["Date"], y=df["MACD_Histogram"], name="MACD Histogram", marker_color="#95a5a6", showlegend=False), row=2, col=2)

    # Row 3, Col 1: Bollinger Bands
    if "BB_Upper" in df.columns:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["BB_Upper"], name="Bollinger Bands", line=dict(color="#bdc3c7", width=1)), row=3, col=1)
        fig.add_trace(go.Scatter(x=df["Date"], y=df["BB_Lower"], name="BB Lower", line=dict(color="#bdc3c7", width=1), fill="tonexty", showlegend=False), row=3, col=1)
        fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], name="Close (BB)", line=dict(color="#2c3e50", width=1.2), showlegend=False), row=3, col=1)

    # Row 3, Col 2: Daily return histogram
    fig.add_trace(go.Histogram(x=df["Daily_Return"] * 100, name="Daily Return %", marker_color="#1abc9c", nbinsx=60, showlegend=False), row=3, col=2)

    # Row 4, Col 1: Monthly returns bar chart
    fig.add_trace(go.Bar(
        x=monthly_returns.index, y=monthly_returns.values, name="Monthly Return %",
        marker_color=["#27ae60" if v >= 0 else "#c0392b" for v in monthly_returns.values],
        showlegend=False,
    ), row=4, col=1)

    # Row 4, Col 2: Historical volatility
    if "Historical_Volatility" in df.columns:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["Historical_Volatility"] * 100, name="Hist. Volatility %", line=dict(color="#d35400"), showlegend=False), row=4, col=2)

    # Axis labels
    fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
    fig.update_yaxes(title_text="Price (USD)", row=1, col=2)
    fig.update_yaxes(title_text="RSI", row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=2, col=2)
    fig.update_yaxes(title_text="Price (USD)", row=3, col=1)
    fig.update_yaxes(title_text="Frequency", row=3, col=2)
    fig.update_yaxes(title_text="Return (%)", row=4, col=1)
    fig.update_yaxes(title_text="Volatility (%)", row=4, col=2)
    for r in range(1, 5):
        for c in range(1, 3):
            fig.update_xaxes(title_text="Date" if not (r == 3 and c == 2) else "Return (%)", row=r, col=c)

    fig.update_layout(
        title=dict(text=title, x=0.5, y=0.99, font=dict(size=22)),
        height=1600, width=1300,
        template="plotly_white",
        margin=dict(t=140, b=70),
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.045, xanchor="center", x=0.5, font=dict(size=11)),
    )

    _add_kpi_annotations(fig, kpis)
    return fig


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for standalone script execution."""
    parser = argparse.ArgumentParser(description="Build the XAUUSD Plotly dashboard as an HTML file.")
    parser.add_argument(
        "--input", type=str, default=str(PROCESSED_DATA_DIR / FEATURES_FILENAME), help="Path to feature CSV file"
    )
    parser.add_argument("--output", type=str, default="dashboard.html", help="Output filename inside reports/")
    return parser.parse_args()


def main() -> None:
    """Entry point for command-line execution."""
    args = parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(input_path, parse_dates=["Date"])
    fig = build_dashboard(df)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / args.output
    fig.write_html(str(output_path))
    print(f"Saved dashboard to {output_path}")


if __name__ == "__main__":
    main()
