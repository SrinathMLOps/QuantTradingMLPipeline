"""FastAPI inference service with live predictions."""
import os
import logging
from typing import List, Dict
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import mlflow.pyfunc
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response
from api.predict import LivePricePredictor

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Quant Trading ML API",
    version="2.0.0",
    description="Live cryptocurrency price prediction with risk management"
)

# Prometheus metrics
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['endpoint', 'status'])
REQUEST_LATENCY = Histogram('api_request_duration_seconds', 'Request latency')
PREDICTION_COUNT = Counter('predictions_total', 'Total predictions made', ['symbol'])

# Global predictor
PREDICTOR = None


class PredictionRequest(BaseModel):
    features: List[float]


class LivePredictionRequest(BaseModel):
    symbol: str = "BTCUSDT"
    interval: str = "1h"


class MultiSymbolRequest(BaseModel):
    symbols: List[str] = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    interval: str = "1h"


class TradingSignalRequest(BaseModel):
    symbol: str = "BTCUSDT"
    threshold: float = 0.02  # 2%


class PredictionResponse(BaseModel):
    prediction: float
    model_version: str


class LivePredictionResponse(BaseModel):
    symbol: str
    current_price: float
    current_time: str
    predicted_price: float
    predicted_return: float
    predicted_return_pct: float
    prediction_time: str
    confidence: float
    direction: str
    model_version: str


class TradingSignalResponse(BaseModel):
    symbol: str
    current_price: float
    predicted_price: float
    predicted_return_pct: float
    action: str
    position_size: float
    confidence: float
    signal_strength: float
    direction: str


@app.on_event("startup")
async def load_model():
    """Load model and initialize predictor."""
    global PREDICTOR
    
    try:
        PREDICTOR = LivePricePredictor()
        logger.info("Live predictor initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize predictor: {e}")
        PREDICTOR = None


@app.get("/health")
async def health():
    """Health check endpoint."""
    if PREDICTOR is None or PREDICTOR.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {
        "status": "healthy",
        "model_loaded": True,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Make prediction from features (legacy endpoint)."""
    if PREDICTOR is None or PREDICTOR.model is None:
        REQUEST_COUNT.labels(endpoint='/predict', status='503').inc()
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        with REQUEST_LATENCY.time():
            prediction = PREDICTOR.model.predict([request.features])[0]
        
        REQUEST_COUNT.labels(endpoint='/predict', status='200').inc()
        
        return PredictionResponse(
            prediction=float(prediction),
            model_version="1.0"
        )
    except Exception as e:
        REQUEST_COUNT.labels(endpoint='/predict', status='500').inc()
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/live", response_model=LivePredictionResponse)
async def predict_live(request: LivePredictionRequest):
    """
    Predict tomorrow's price using live data from Binance.
    
    This endpoint:
    1. Fetches latest data from Binance
    2. Engineers features
    3. Makes prediction
    4. Returns predicted price for tomorrow
    """
    if PREDICTOR is None:
        REQUEST_COUNT.labels(endpoint='/predict/live', status='503').inc()
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    try:
        with REQUEST_LATENCY.time():
            prediction = PREDICTOR.predict_tomorrow(
                symbol=request.symbol,
                interval=request.interval
            )
        
        if prediction is None:
            REQUEST_COUNT.labels(endpoint='/predict/live', status='500').inc()
            raise HTTPException(status_code=500, detail="Prediction failed")
        
        REQUEST_COUNT.labels(endpoint='/predict/live', status='200').inc()
        PREDICTION_COUNT.labels(symbol=request.symbol).inc()
        
        return LivePredictionResponse(**prediction)
        
    except Exception as e:
        REQUEST_COUNT.labels(endpoint='/predict/live', status='500').inc()
        logger.error(f"Live prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/multi")
async def predict_multi(request: MultiSymbolRequest):
    """
    Predict tomorrow's prices for multiple symbols.
    
    Returns predictions for BTC, ETH, BNB, etc.
    """
    if PREDICTOR is None:
        REQUEST_COUNT.labels(endpoint='/predict/multi', status='503').inc()
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    try:
        with REQUEST_LATENCY.time():
            predictions = PREDICTOR.predict_multiple_symbols(
                symbols=request.symbols,
                interval=request.interval
            )
        
        REQUEST_COUNT.labels(endpoint='/predict/multi', status='200').inc()
        
        for symbol in predictions.keys():
            PREDICTION_COUNT.labels(symbol=symbol).inc()
        
        return {
            "predictions": predictions,
            "timestamp": datetime.now().isoformat(),
            "count": len(predictions)
        }
        
    except Exception as e:
        REQUEST_COUNT.labels(endpoint='/predict/multi', status='500').inc()
        logger.error(f"Multi prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/signal", response_model=TradingSignalResponse)
async def get_trading_signal(request: TradingSignalRequest):
    """
    Get trading signal (BUY/SELL/HOLD) based on prediction.
    
    Returns:
    - Action: BUY, SELL, or HOLD
    - Position size: 0-1 based on confidence
    - Signal strength: How strong the signal is
    """
    if PREDICTOR is None:
        REQUEST_COUNT.labels(endpoint='/signal', status='503').inc()
        raise HTTPException(status_code=503, detail="Predictor not initialized")
    
    try:
        with REQUEST_LATENCY.time():
            signal = PREDICTOR.get_trading_signal(
                symbol=request.symbol,
                threshold=request.threshold
            )
        
        if signal is None:
            REQUEST_COUNT.labels(endpoint='/signal', status='500').inc()
            raise HTTPException(status_code=500, detail="Signal generation failed")
        
        REQUEST_COUNT.labels(endpoint='/signal', status='200').inc()
        
        return TradingSignalResponse(
            symbol=signal['symbol'],
            current_price=signal['current_price'],
            predicted_price=signal['predicted_price'],
            predicted_return_pct=signal['predicted_return_pct'],
            action=signal['action'],
            position_size=signal['position_size'],
            confidence=signal['confidence'],
            signal_strength=signal['signal_strength'],
            direction=signal['direction']
        )
        
    except Exception as e:
        REQUEST_COUNT.labels(endpoint='/signal', status='500').inc()
        logger.error(f"Signal generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/price/current/{symbol}")
async def get_current_price(symbol: str = "BTCUSDT"):
    """Get current live price from Binance."""
    try:
        from ingestion.fetch_data import BinanceLiveDataFetcher
        
        fetcher = BinanceLiveDataFetcher()
        price_data = fetcher.get_current_price(symbol)
        
        if price_data is None:
            raise HTTPException(status_code=500, detail="Failed to fetch price")
        
        return price_data
        
    except Exception as e:
        logger.error(f"Error fetching current price: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Quant Trading ML API",
        "version": "2.0.0",
        "description": "Live cryptocurrency price prediction with risk management",
        "endpoints": {
            "/health": "Health check",
            "/metrics": "Prometheus metrics",
            "/predict/live": "Predict tomorrow's price (live data)",
            "/predict/multi": "Predict multiple symbols",
            "/signal": "Get trading signal (BUY/SELL/HOLD)",
            "/price/current/{symbol}": "Get current live price",
            "/docs": "API documentation"
        },
        "features": [
            "Live data from Binance",
            "Tomorrow's price prediction",
            "Trading signals with confidence",
            "Multi-asset support",
            "Risk management",
            "Real-time monitoring"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
