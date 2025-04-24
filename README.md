# Trading Tools

## chart_plotter.py 

Candlestick Chart Visualization with Technical Indicators

This script loads candlestick and indicator data from a JSON file and generates a detailed multi-panel chart for quick technical analysis.

**Features:**

* Candlestick plotting with overlays:
  * **SMA / EMA** (Simple & Exponential Moving Average)
  * **Bollinger Bands**
* Additional subplots:
  * **RSI** (Relative Strength Index)
  * **MACD** (Moving Average Convergence Divergence)
  * **ATR** (Average True Range)

**Input:**

* JSON file with a structure containing timeframes (e.g., "5m") and:
  * candles: OHLCV data
  * indicators: corresponding values for SMA, EMA, RSI, MACD, ATR, BBands

Example

```json
{
  "5m": {
    "candles": [
      {
        "time": "2025-04-23T13:30:00.000Z",
        "open": 94009.31,
        "high": 94253.82,
        "low": 93919.34,
        "close": 94000.08,
        "volume": 168.81393
      },
      {
        "time": "2025-04-23T13:35:00.000Z",
        "open": 94000.08,
        "high": 94696.05,
        "low": 93381,
        "close": 93536.01,
        "volume": 1086.05628
      },
      ...
    ],
    "indicators": [
      {
        "time": "2025-04-23T13:30:00.000Z",
        "sma": 93769.41,
        "ema": 93919.2,
        "rsi": 61.47,
        "macd": {
          "macd": 90.1,
          "signal": 84.61,
          "hist": 5.49
        },
        "atr": 143.4,
        "bbands": {
          "lower": 93435.96,
          "middle": 93769.41,
          "upper": 94102.85
        }
      },
      {
        "time": "2025-04-23T13:35:00.000Z",
        "sma": 93772.91,
        "ema": 93842.56,
        "rsi": 40.66,
        "macd": {
          "macd": 16.38,
          "signal": 61.87,
          "hist": -45.49
        },
        "atr": 227.09,
        "bbands": {
          "lower": 93451.01,
          "middle": 93772.91,
          "upper": 94094.81
        }
      },
      ...
    ]
  }
}
```

**Usage:**

```
python chart_plotter.py path/to/your_data.json
```

The script automatically selects the first available timeframe and visualizes the combined data.

## Freqtrade Backend Strategy

Testing backend strategy

**Installation**

```
brew install ta-lib
pip install freqtrade
pip install pytest
```

**Run tests**

```
pytest test_backend_strategy.py
```