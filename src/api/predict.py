"""Real-time prediction service for tomorrow's price."""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd
import numpy as np
import mlflow.pyfunc
from features.engineer_features import create_features
from ingestion.fetch_data import BinanceLiveDataFetcher

logger = logging.getLogger(__name__)


class LivePricePredictor:
    """Make live predictions for tomorrow's cryptocurrency prices."""
    
    def __init__(self, model_uri: str = "models:/xgboost-forecaster/Production"):
        """
        Initialize predictor with MLflow model.
        
        Args:
            model_uri: MLflow model URI
        """
        self.model_uri = model_uri
        self.model = None
        self.fetcher = BinanceLiveDataFetcher()
        self.load_model()
        
    def load_model(self):
        """Load model from MLflow registry."""
        try:
            mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
            mlflow.set_tracking_uri(mlflow_uri)
            
            self.model = mlflow.pyfunc.load_model(self.model_uri)
            logger.info(f"Model loaded successfully from {self.model_uri}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
    
    def fetch_latest_data(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1h",
        lookback_hours: int = 168  # 7 days
    ) -> pd.DataFrame:
        """
        Fetch latest data from Binance.
        
        Args:
            symbol: Trading pair symbol
            interval: Kline interval
            lookback_hours: Number of hours to fetch
            
        Returns:
            df: DataFrame with latest data
        """
        logger.info(f"Fetching latest data for {symbol}...")
        
        # Fetch latest klines
        df = self.fetcher.get_latest_klines(
            symbol=symbol,
            interval=interval,
            limit=lookback_hours
        )
        
        if df is None or len(df) == 0:
            logger.error("Failed to fetch data from Binance")
            return None
        
        logger.info(f"Fetched {len(df)} data points")
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for prediction.
        
        Args:
            df: Raw OHLCV data
            
        Returns:
            features_df: DataFrame with engineered features
        """
        logger.info("Engineering features...")
        
        # Save temporarily
        temp_path = "data/temp/latest_data.parquet"
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        df.to_parquet(temp_path, index=False)
        
        # Create features
        features_df = create_features(temp_path)
        
        logger.info(f"Created {len(features_df.columns)} features")
        return features_df
    
    def predict_tomorrow(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1h"
    ) -> Dict:
        """
        Predict tomorrow's price for a symbol.
        
        Args:
            symbol: Trading pair symbol
            interval: Kline interval
            
        Returns:
            prediction: Dictionary with prediction results
        """
        if self.model is None:
            logger.error("Model not loaded")
            return None
        
        # Fetch latest data
        df = self.fetch_latest_data(symbol, interval)
        if df is None:
            return None
        
        # Get current price
        current_price = df['close'].iloc[-1]
        current_time = df['timestamp'].iloc[-1]
        
        # Prepare features
        features_df = self.prepare_features(df)
        
        if features_df is None or len(features_df) == 0:
            logger.error("Failed to create features")
            return None
        
        # Get latest features (last row)
        latest_features = features_df.iloc[-1:]
        
        # Remove non-feature columns
        feature_cols = [col for col in latest_features.columns 
                       if col not in ['timestamp', 'target', 'close']]
        X = latest_features[feature_cols]
        
        # Make prediction
        try:
            predicted_return = self.model.predict(X)[0]
            
            # Convert return to price
            predicted_price = current_price * (1 + predicted_return)
            
            # Calculate prediction time (tomorrow same time)
            prediction_time = current_time + timedelta(hours=24)
            
            # Calculate confidence (based on model uncertainty)
            # For now, use absolute value of prediction as proxy
            confidence = min(abs(predicted_return) * 10, 1.0)
            
            result = {
                'symbol': symbol,
                'current_price': float(current_price),
                'current_time': current_time.isoformat(),
                'predicted_price': float(predicted_price),
                'predicted_return': float(predicted_return),
                'predicted_return_pct': float(predicted_return * 100),
                'prediction_time': prediction_time.isoformat(),
                'confidence': float(confidence),
                'direction': 'UP' if predicted_return > 0 else 'DOWN',
                'model_version': self.model_uri
            }
            
            logger.info(
                f"Prediction for {symbol}: "
                f"${current_price:,.2f} → ${predicted_price:,.2f} "
                f"({predicted_return*100:+.2f}%)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return None
    
    def predict_multiple_symbols(
        self,
        symbols: List[str] = None,
        interval: str = "1h"
    ) -> Dict[str, Dict]:
        """
        Predict tomorrow's prices for multiple symbols.
        
        Args:
            symbols: List of trading pairs
            interval: Kline interval
            
        Returns:
            predictions: Dictionary mapping symbol to prediction
        """
        if symbols is None:
            symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        
        predictions = {}
        
        for symbol in symbols:
            logger.info(f"Predicting for {symbol}...")
            prediction = self.predict_tomorrow(symbol, interval)
            
            if prediction is not None:
                predictions[symbol] = prediction
            
            # Rate limiting
            import time
            time.sleep(0.5)
        
        return predictions
    
    def get_trading_signal(
        self,
        symbol: str = "BTCUSDT",
        threshold: float = 0.02  # 2% threshold
    ) -> Dict:
        """
        Generate trading signal based on prediction.
        
        Args:
            symbol: Trading pair symbol
            threshold: Minimum return threshold for signal
            
        Returns:
            signal: Dictionary with trading signal
        """
        prediction = self.predict_tomorrow(symbol)
        
        if prediction is None:
            return None
        
        predicted_return = prediction['predicted_return']
        confidence = prediction['confidence']
        
        # Generate signal
        if abs(predicted_return) < threshold:
            action = "HOLD"
            position_size = 0
        elif predicted_return > threshold:
            action = "BUY"
            position_size = min(confidence, 1.0)
        else:
            action = "SELL"
            position_size = min(confidence, 1.0)
        
        signal = {
            **prediction,
            'action': action,
            'position_size': float(position_size),
            'threshold': threshold,
            'signal_strength': abs(predicted_return) / threshold if threshold > 0 else 0
        }
        
        logger.info(
            f"Trading signal for {symbol}: {action} "
            f"(size: {position_size:.2f}, strength: {signal['signal_strength']:.2f})"
        )
        
        return signal


def predict_tomorrow_price(symbol: str = "BTCUSDT") -> Dict:
    """
    Convenience function to predict tomorrow's price.
    
    Args:
        symbol: Trading pair symbol
        
    Returns:
        prediction: Dictionary with prediction results
    """
    predictor = LivePricePredictor()
    return predictor.predict_tomorrow(symbol)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize predictor
    predictor = LivePricePredictor()
    
    # Predict for BTC
    logger.info("=" * 60)
    logger.info("BITCOIN (BTC) PREDICTION")
    logger.info("=" * 60)
    btc_prediction = predictor.predict_tomorrow("BTCUSDT")
    
    if btc_prediction:
        print(f"\nCurrent Price: ${btc_prediction['current_price']:,.2f}")
        print(f"Predicted Price (24h): ${btc_prediction['predicted_price']:,.2f}")
        print(f"Expected Return: {btc_prediction['predicted_return_pct']:+.2f}%")
        print(f"Direction: {btc_prediction['direction']}")
        print(f"Confidence: {btc_prediction['confidence']:.2%}")
    
    # Get trading signal
    logger.info("\n" + "=" * 60)
    logger.info("TRADING SIGNAL")
    logger.info("=" * 60)
    signal = predictor.get_trading_signal("BTCUSDT")
    
    if signal:
        print(f"\nAction: {signal['action']}")
        print(f"Position Size: {signal['position_size']:.2%}")
        print(f"Signal Strength: {signal['signal_strength']:.2f}x")
    
    # Predict multiple symbols
    logger.info("\n" + "=" * 60)
    logger.info("MULTI-ASSET PREDICTIONS")
    logger.info("=" * 60)
    predictions = predictor.predict_multiple_symbols(["BTCUSDT", "ETHUSDT"])
    
    for symbol, pred in predictions.items():
        print(f"\n{symbol}:")
        print(f"  Current: ${pred['current_price']:,.2f}")
        print(f"  Predicted: ${pred['predicted_price']:,.2f}")
        print(f"  Return: {pred['predicted_return_pct']:+.2f}%")
