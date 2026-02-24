"""XGBoost model training with MLflow tracking."""
import os
import logging
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import mlflow
import mlflow.xgboost

logger = logging.getLogger(__name__)


def train_xgboost(input_path: str = "data/processed/features.parquet"):
    """Train XGBoost model with MLflow tracking."""
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment("xgboost-forecasting")
    
    logger.info(f"Loading features from {input_path}")
    df = pd.read_parquet(input_path)
    
    # Prepare features and target
    feature_cols = [col for col in df.columns if col not in ['timestamp', 'target']]
    X = df[feature_cols]
    y = df['target']
    
    # Train/test split (time-based)
    split_idx = int(len(df) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
    
    # Start MLflow run
    with mlflow.start_run():
        # Hyperparameters
        params = {
            'objective': 'reg:squarederror',
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42
        }
        
        # Log parameters
        mlflow.log_params(params)
        
        # Train model
        logger.info("Training XGBoost model...")
        model = xgb.XGBRegressor(**params)
        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            early_stopping_rounds=10,
            verbose=False
        )
        
        # Predictions
        y_pred = model.predict(X_test)
        
        # Metrics
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        logger.info(f"MSE: {mse:.6f}, MAE: {mae:.6f}, R2: {r2:.4f}")
        
        # Log metrics
        mlflow.log_metrics({
            'mse': mse,
            'mae': mae,
            'r2': r2
        })
        
        # Log model
        mlflow.xgboost.log_model(
            model,
            "model",
            registered_model_name="xgboost-forecaster"
        )
        
        logger.info("Model training completed and logged to MLflow")
        
    return model


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_xgboost()
