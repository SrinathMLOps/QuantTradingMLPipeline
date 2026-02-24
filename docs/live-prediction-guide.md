# Live Price Prediction Guide

## Overview

This system fetches live data from Binance and predicts tomorrow's cryptocurrency prices in real-time.

## Features

✅ **Live Data Ingestion** - Real-time data from Binance API  
✅ **Tomorrow's Price Prediction** - 24-hour ahead forecasting  
✅ **Trading Signals** - BUY/SELL/HOLD recommendations  
✅ **Multi-Asset Support** - BTC, ETH, BNB, SOL, ADA  
✅ **Confidence Scores** - Model uncertainty quantification  
✅ **Automated Daily Predictions** - Scheduled via CronJob  

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  LIVE PREDICTION FLOW                        │
└─────────────────────────────────────────────────────────────┘

1. Data Ingestion (Real-time)
   ┌──────────────┐
   │   Binance    │
   │     API      │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │  Live Data   │
   │   Fetcher    │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │  Latest      │
   │  OHLCV Data  │
   │  (168 hours) │
   └──────────────┘

2. Feature Engineering
   ┌──────────────┐
   │  Technical   │
   │  Indicators  │
   │  • RSI       │
   │  • MACD      │
   │  • Bollinger │
   │  • ATR       │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │  30+ ML      │
   │  Features    │
   └──────────────┘

3. Prediction
   ┌──────────────┐
   │  XGBoost     │
   │  Model       │
   │  (MLflow)    │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │  Tomorrow's  │
   │  Return      │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │  Predicted   │
   │  Price       │
   └──────────────┘

4. Trading Signal
   ┌──────────────┐
   │  Signal      │
   │  Generator   │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │  BUY/SELL/   │
   │  HOLD        │
   │  + Size      │
   └──────────────┘
```

## API Endpoints

### 1. Predict Tomorrow's Price (Live Data)

**Endpoint:** `POST /predict/live`

**Request:**
```json
{
  "symbol": "BTCUSDT",
  "interval": "1h"
}
```

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "current_price": 45230.50,
  "current_time": "2024-02-24T10:00:00",
  "predicted_price": 46150.25,
  "predicted_return": 0.0203,
  "predicted_return_pct": 2.03,
  "prediction_time": "2024-02-25T10:00:00",
  "confidence": 0.75,
  "direction": "UP",
  "model_version": "models:/xgboost-forecaster/Production"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/predict/live" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT"}'
```

### 2. Get Trading Signal

**Endpoint:** `POST /signal`

**Request:**
```json
{
  "symbol": "BTCUSDT",
  "threshold": 0.02
}
```

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "current_price": 45230.50,
  "predicted_price": 46150.25,
  "predicted_return_pct": 2.03,
  "action": "BUY",
  "position_size": 0.75,
  "confidence": 0.75,
  "signal_strength": 1.02,
  "direction": "UP"
}
```

**Signal Logic:**
- `BUY`: Predicted return > threshold (e.g., +2%)
- `SELL`: Predicted return < -threshold (e.g., -2%)
- `HOLD`: Predicted return between -threshold and +threshold

**Position Size:**
- Based on model confidence (0-1)
- Higher confidence = larger position
- Capped at max_position_size (default 1.0)

### 3. Predict Multiple Symbols

**Endpoint:** `POST /predict/multi`

**Request:**
```json
{
  "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
  "interval": "1h"
}
```

**Response:**
```json
{
  "predictions": {
    "BTCUSDT": {
      "current_price": 45230.50,
      "predicted_price": 46150.25,
      "predicted_return_pct": 2.03,
      "direction": "UP"
    },
    "ETHUSDT": {
      "current_price": 2850.75,
      "predicted_price": 2920.30,
      "predicted_return_pct": 2.44,
      "direction": "UP"
    },
    "BNBUSDT": {
      "current_price": 385.20,
      "predicted_price": 378.50,
      "predicted_return_pct": -1.74,
      "direction": "DOWN"
    }
  },
  "timestamp": "2024-02-24T10:00:00",
  "count": 3
}
```

### 4. Get Current Live Price

**Endpoint:** `GET /price/current/{symbol}`

**Example:**
```bash
curl "http://localhost:8000/price/current/BTCUSDT"
```

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "price": 45230.50,
  "volume_24h": 25430.5,
  "price_change_24h": 1250.30,
  "price_change_pct_24h": 2.84,
  "high_24h": 45500.00,
  "low_24h": 43800.00,
  "timestamp": "2024-02-24T10:00:00"
}
```

## Python Usage

### Basic Prediction

```python
from api.predict import LivePricePredictor

# Initialize predictor
predictor = LivePricePredictor()

# Predict tomorrow's BTC price
prediction = predictor.predict_tomorrow("BTCUSDT")

print(f"Current: ${prediction['current_price']:,.2f}")
print(f"Predicted: ${prediction['predicted_price']:,.2f}")
print(f"Return: {prediction['predicted_return_pct']:+.2f}%")
print(f"Direction: {prediction['direction']}")
```

### Get Trading Signal

```python
# Get trading signal
signal = predictor.get_trading_signal("BTCUSDT", threshold=0.02)

print(f"Action: {signal['action']}")
print(f"Position Size: {signal['position_size']:.1%}")
print(f"Confidence: {signal['confidence']:.1%}")
```

### Predict Multiple Symbols

```python
# Predict multiple cryptocurrencies
symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
predictions = predictor.predict_multiple_symbols(symbols)

for symbol, pred in predictions.items():
    print(f"{symbol}: ${pred['predicted_price']:,.2f} ({pred['predicted_return_pct']:+.2f}%)")
```

## Automated Daily Predictions

### Setup CronJob

The system includes a Kubernetes CronJob that runs daily predictions automatically.

**Schedule:** Every day at midnight UTC

**What it does:**
1. Fetches latest data from Binance
2. Predicts tomorrow's prices for BTC, ETH, BNB, SOL, ADA
3. Generates trading signals
4. Saves predictions to file
5. Logs results

**Deploy:**
```bash
kubectl apply -f infra/k8s/daily-prediction-cronjob.yaml
```

**Check status:**
```bash
kubectl get cronjobs
kubectl get jobs
kubectl logs -l app=daily-prediction
```

### Manual Run

```bash
# Run locally
python scripts/daily_prediction.py

# Run in Kubernetes
kubectl create job --from=cronjob/daily-prediction manual-prediction-$(date +%s)
```

## Data Flow

### 1. Live Data Ingestion

```python
from ingestion.fetch_data import BinanceLiveDataFetcher

fetcher = BinanceLiveDataFetcher()

# Get current price
current = fetcher.get_current_price("BTCUSDT")

# Get latest klines (last 168 hours)
df = fetcher.get_latest_klines("BTCUSDT", "1h", limit=168)

# Get order book
order_book = fetcher.get_order_book("BTCUSDT")

# Get recent trades
trades = fetcher.get_recent_trades("BTCUSDT")
```

### 2. Feature Engineering

```python
from features.engineer_features import create_features

# Create features from raw data
features_df = create_features("data/raw/BTCUSDT_1h.parquet")

# Features include:
# - Technical indicators (RSI, MACD, Bollinger, ATR)
# - Lag features (1h, 4h, 24h)
# - Rolling statistics (mean, std, min, max)
# - Time-based features (hour, day of week)
```

### 3. Model Prediction

```python
import mlflow.pyfunc

# Load model from MLflow
model = mlflow.pyfunc.load_model("models:/xgboost-forecaster/Production")

# Make prediction
predicted_return = model.predict(features)

# Convert to price
predicted_price = current_price * (1 + predicted_return)
```

## Configuration

### Environment Variables

```bash
# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000

# Binance API (optional for public data)
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret

# AWS (for S3 storage)
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

### Supported Symbols

```python
# Major cryptocurrencies
symbols = [
    "BTCUSDT",   # Bitcoin
    "ETHUSDT",   # Ethereum
    "BNBUSDT",   # Binance Coin
    "SOLUSDT",   # Solana
    "ADAUSDT",   # Cardano
    "XRPUSDT",   # Ripple
    "DOGEUSDT",  # Dogecoin
    "MATICUSDT", # Polygon
    "DOTUSDT",   # Polkadot
    "AVAXUSDT"   # Avalanche
]
```

### Intervals

```python
# Supported kline intervals
intervals = [
    "1m",   # 1 minute
    "5m",   # 5 minutes
    "15m",  # 15 minutes
    "1h",   # 1 hour (default)
    "4h",   # 4 hours
    "1d"    # 1 day
]
```

## Monitoring

### Prometheus Metrics

```
# Predictions made
predictions_total{symbol="BTCUSDT"} 150

# API requests
api_requests_total{endpoint="/predict/live",status="200"} 1250

# Request latency
api_request_duration_seconds{quantile="0.95"} 0.45
```

### Grafana Dashboard

Create dashboard with:
- Predictions per symbol
- Prediction accuracy over time
- API latency
- Error rates
- Model confidence distribution

## Troubleshooting

### Issue: Binance API rate limit

**Error:** `429 Too Many Requests`

**Solution:**
```python
# Add delay between requests
import time
time.sleep(1)

# Or use API key for higher limits
fetcher = BinanceLiveDataFetcher(
    api_key="your_key",
    api_secret="your_secret"
)
```

### Issue: Model not found

**Error:** `Model 'Production' not found`

**Solution:**
```bash
# Promote model to production
python -c "
import mlflow
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name='xgboost-forecaster',
    version=1,
    stage='Production'
)
"
```

### Issue: Insufficient data

**Error:** `Not enough data for feature engineering`

**Solution:**
```python
# Increase lookback period
df = fetcher.get_latest_klines("BTCUSDT", "1h", limit=200)
```

## Best Practices

### 1. Rate Limiting

```python
# Respect Binance rate limits
# Weight: 1 per request
# Limit: 1200 requests per minute

import time
for symbol in symbols:
    prediction = predictor.predict_tomorrow(symbol)
    time.sleep(0.5)  # 2 requests per second
```

### 2. Error Handling

```python
try:
    prediction = predictor.predict_tomorrow("BTCUSDT")
except Exception as e:
    logger.error(f"Prediction failed: {e}")
    # Fallback to previous prediction or default
```

### 3. Caching

```python
# Cache predictions for 1 hour
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=100)
def get_cached_prediction(symbol, hour):
    return predictor.predict_tomorrow(symbol)

# Use current hour as cache key
current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
prediction = get_cached_prediction("BTCUSDT", current_hour)
```

### 4. Monitoring

```python
# Log all predictions
logger.info(
    f"Prediction: {symbol} "
    f"${current_price:,.2f} → ${predicted_price:,.2f} "
    f"({predicted_return*100:+.2f}%)"
)

# Track accuracy
actual_price = fetcher.get_current_price(symbol)['price']
error = abs(predicted_price - actual_price) / actual_price
logger.info(f"Prediction error: {error:.2%}")
```

## Example Output

```
==================================================================
DAILY CRYPTOCURRENCY PRICE PREDICTIONS
Timestamp: 2024-02-24T00:00:00
==================================================================

TOMORROW'S PRICE PREDICTIONS
==================================================================

BTCUSDT:
  Current Price:    $   45,230.50
  Predicted Price:  $   46,150.25
  Expected Return:         +2.03%
  Direction:                  UP
  Confidence:              75.0%

ETHUSDT:
  Current Price:    $    2,850.75
  Predicted Price:  $    2,920.30
  Expected Return:         +2.44%
  Direction:                  UP
  Confidence:              82.0%

BNBUSDT:
  Current Price:    $      385.20
  Predicted Price:  $      378.50
  Expected Return:         -1.74%
  Direction:                DOWN
  Confidence:              68.0%

==================================================================
TRADING SIGNALS
==================================================================

BTCUSDT:
  Action:                     BUY
  Position Size:            75.0%
  Signal Strength:          1.02x

ETHUSDT:
  Action:                     BUY
  Position Size:            82.0%
  Signal Strength:          1.22x

BNBUSDT:
  Action:                    HOLD
  Position Size:             0.0%
  Signal Strength:          0.87x

==================================================================
PREDICTION COMPLETE
==================================================================
```

## Next Steps

1. **Test locally:** `python scripts/daily_prediction.py`
2. **Deploy API:** `kubectl apply -f infra/k8s/api-deployment.yaml`
3. **Setup CronJob:** `kubectl apply -f infra/k8s/daily-prediction-cronjob.yaml`
4. **Monitor:** Check Grafana dashboards
5. **Iterate:** Improve model based on prediction accuracy
