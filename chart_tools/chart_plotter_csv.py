import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates
import numpy as np
import sys

if len(sys.argv) < 2:
    print("Usage: python chart_plotter_csv.py <datafile.csv>")
    sys.exit(1)

csv_file = sys.argv[1]

# === DataFrame-Creation ===
df = pd.read_csv(csv_file, parse_dates=["time"])
df.set_index("time", inplace=True)

# Einheitliche Spaltennamen für die Indikatoren
if "sma" in df.columns:
    df["SMA"] = df["sma"]
if "ema" in df.columns:
    df["EMA"] = df["ema"]
if "rsi" in df.columns:
    df["RSI"] = df["rsi"]
# MACD, Signal und Histogramm
if {"macd", "signal", "hist"}.issubset(df.columns):
    df["MACD"] = df["macd"]
    df["MACD_signal"] = df["signal"]
    df["MACD_hist"] = df["hist"]
if "atr" in df.columns:
    df["ATR"] = df["atr"]
# Bollinger-Bänder
if {"bbLower", "bbMiddle", "bbUpper"}.issubset(df.columns):
    df["BB_lower"] = df["bbLower"]
    df["BB_middle"] = df["bbMiddle"]
    df["BB_upper"] = df["bbUpper"]

# Width für Kerzenkörper
time_deltas = np.diff(mdates.date2num(df.index.to_list()))
avg_delta = np.mean(time_deltas)

def plot_indicators(
        df,
        sma: bool = True,
        ema: bool = True,
        bbands: bool = True,
        rsi: bool = True,
        macd: bool = True,
        atr: bool = True,
):
    """
    Zeichnet:
      - Candlestick
      - SMA/EMA/BBands im ersten Chart (wenn verfügbar und gewünscht)
      - Separate Subplots für RSI, MACD, ATR (wenn verfügbar und gewünscht)
    """
    extras = []
    if rsi and "RSI" in df.columns:
        extras.append("RSI")
    if macd and "MACD" in df.columns:
        extras.append("MACD")
    if atr and "ATR" in df.columns:
        extras.append("ATR")

    n_plots = 1 + len(extras)
    fig, axes = plt.subplots(
        n_plots,
        1,
        figsize=(14, 4 + 2 * len(extras)),
        gridspec_kw={"height_ratios": [3] + [1] * len(extras)},
    )
    if n_plots == 1:
        axes = [axes]

    # --- Plot 1: Kerzen + Overlays ---
    ax0 = axes[0]
    def draw_candles(ax):
        w = avg_delta * 0.8
        for t, row in df.iterrows():
            color = "green" if row["close"] >= row["open"] else "red"
            ax.plot([t, t], [row["low"], row["high"]], color="black")
            rect = Rectangle(
                (mdates.date2num(t) - w / 2, min(row["open"], row["close"])),
                w,
                abs(row["close"] - row["open"]),
                color=color,
                alpha=0.8,
            )
            ax.add_patch(rect)
        ax.xaxis_date()

    draw_candles(ax0)

    if sma and "SMA" in df:
        ax0.plot(df.index, df["SMA"], label="SMA", color="blue")
    if ema and "EMA" in df:
        ax0.plot(df.index, df["EMA"], label="EMA", color="orange")
    if bbands and "BB_lower" in df:
        ax0.plot(df.index, df["BB_lower"], label="BB Lower", linestyle="--")
        ax0.plot(df.index, df["BB_middle"], label="BB Middle", linestyle="--")
        ax0.plot(df.index, df["BB_upper"], label="BB Upper", linestyle="--")

    ax0.set_title("Candlestick + Overlays")
    ax0.set_ylabel("Price")
    ax0.legend()
    ax0.grid(True)

    # --- Weitere Subplots ---
    for i, name in enumerate(extras, start=1):
        ax = axes[i]
        if name == "RSI":
            ax.plot(df.index, df["RSI"], label="RSI")
            ax.axhline(70, linestyle="--")
            ax.axhline(30, linestyle="--")
            ax.set_ylabel("RSI")
        elif name == "MACD":
            ax.plot(df.index, df["MACD"], label="MACD")
            ax.plot(df.index, df["MACD_signal"], label="Signal")
            ax.bar(df.index, df["MACD_hist"], width=avg_delta * 0.8, alpha=0.5)
            ax.set_ylabel("MACD")
        elif name == "ATR":
            ax.plot(df.index, df["ATR"], label="ATR")
            ax.set_ylabel("ATR")
        ax.set_title(name)
        ax.legend()
        ax.grid(True)

    plt.tight_layout()
    plt.show()

plot_indicators(df, sma=True, ema=True, bbands=True, rsi=True, macd=True, atr=True)