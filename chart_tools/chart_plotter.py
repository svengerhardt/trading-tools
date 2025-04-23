import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates
import numpy as np
import json
import sys

if len(sys.argv) < 2:
    print("Usage: python chart_plotter.py <datafile.json>")
    sys.exit(1)

with open(sys.argv[1], "r") as f:
    sample_data = json.load(f)

selected_tf = next(iter(sample_data.keys()))

# === DataFrame-Creation ===
candles = pd.DataFrame(sample_data[selected_tf]["candles"])
candles["time"] = pd.to_datetime(candles["time"])
candles.set_index("time", inplace=True)

indicators = pd.DataFrame(sample_data[selected_tf]["indicators"])
indicators["time"] = pd.to_datetime(indicators["time"])
indicators.set_index("time", inplace=True)

df = candles.join(indicators)
# Extract all potential columns, if available
if "sma" in df:
    df["SMA"] = df["sma"]
if "ema" in df:
    df["EMA"] = df["ema"]
if "rsi" in df:
    df["RSI"] = df["rsi"]
if "macd" in df:
    df["MACD"] = df["macd"].apply(lambda x: x["macd"])
    df["MACD_signal"] = df["macd"].apply(lambda x: x["signal"])
    df["MACD_hist"] = df["macd"].apply(lambda x: x["hist"])
if "atr" in df:
    df["ATR"] = df["atr"]
if "bbands" in df:
    df["BB_lower"] = df["bbands"].apply(lambda x: x["lower"])
    df["BB_middle"] = df["bbands"].apply(lambda x: x["middle"])
    df["BB_upper"] = df["bbands"].apply(lambda x: x["upper"])

# Width for candle bodies
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
    Draws:
      - Candlestick
      - Width for candles body overlaid SMA/EMA/BBands in the first chart, if available and desired
      - Separate subplot for RSI, MACD, ATR, if available and desired
    """
    # Which extra subplots should be created?
    extras = []
    if rsi and "RSI" in df.columns:
        extras.append("RSI")
    if macd and "MACD" in df.columns:
        extras.append("MACD")
    if atr and "ATR" in df.columns:
        extras.append("ATR")

    n_plots = 1 + len(extras)
    # Dynamic height: base 4 + 2 per additional chart
    fig, axes = plt.subplots(
        n_plots,
        1,
        figsize=(14, 4 + 2 * len(extras)),
        gridspec_kw={"height_ratios": [3] + [1] * len(extras)},
    )
    # If only 1 plot is returned, wrap in list
    if n_plots == 1:
        axes = [axes]

    # --- Plot 1: Candles + SMA/EMA/BBands ---
    ax0 = axes[0]

    # Candlestick-Function
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

    # Overlay
    if sma and "SMA" in df:
        ax0.plot(df.index, df["SMA"], label="SMA", color="blue")
    if ema and "EMA" in df:
        ax0.plot(df.index, df["EMA"], label="EMA", color="orange")
    if bbands and "BB_lower" in df:
        ax0.plot(df.index, df["BB_lower"], label="BB Lower", linestyle="--")
        ax0.plot(df.index, df["BB_middle"], label="BB Middle", linestyle="--")
        ax0.plot(df.index, df["BB_upper"], label="BB Upper", linestyle="--")
    ax0.set_title(f"Candlestick + Overlays ({selected_tf})")
    ax0.set_ylabel("Price")
    ax0.legend()
    ax0.grid(True)

    # --- Further subplots in the order extras ---
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
