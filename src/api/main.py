"""FastAPI inference service."""
import os
import logging
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mlflow.pyfunc
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response

logger = logging.getLogger(__name__)

app = FastAPI(title="Quant Trading ML API", version="1.0.0")

# Prometheus metrics
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['endpoint', 'status'])
REQUEST_LATENCY = Histogram('api_request_duration_seconds', 'Request latency')

# Load model
MODEL = None


class PredictionRequest(BaseModel):
    features: List[float]


class PredictionResponse(BaseModel):
    prediction: float
    model_version: str


@app.on_event("startup")
async def load_model():
    """Load model from MLflow registry."""
    global MODEL
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    mlflow.set_tracking_uri(mlflow_uri)
    
    try:
        MODEL = mlflow.pyfunc.load_model("models:/xgboost-forecaster/Production")
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        MODEL = None


@app.get("/health")
async def health():
    """Health check endpoint."""
    if MODEL is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Make prediction."""
    if MODEL is None:
        REQUEST_COUNT.labels(endpoint='/predict', status='503').inc()
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        with REQUEST_LATENCY.time():
            prediction = MODEL.predict([request.features])[0]
        
        REQUEST_COUNT.labels(endpoint='/predict', status='200').inc()
        
        return PredictionResponse(
            prediction=float(prediction),
            model_version="1.0"
        )
    except Exception as e:
        REQUEST_COUNT.labels(endpoint='/predict', status='500').inc()
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
