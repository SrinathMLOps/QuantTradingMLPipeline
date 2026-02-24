"""XGBoost model training with MLflow tracking and backtesting."""
import os
import logging
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import mlflow
import mlflow.xgboost

from backtest.strategy import QuantStrategy
from backtest.risk_metrics import calculate_advanced_metrics
from backtest.visualization import (
    plot_equity_curve, plot_drawdown, plot_feature_importance,
    create_performance_report
)

logger = logging.getLogger(__name__)


def train_xgboost(input_path: str = "data/processed/features.parquet"):
    """Train XGBoost model with MLflow tracking and backtesting."""
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment("xgboost-quant-trading")
    
    logger.info(f"Loading features from {input_path}")
    df = pd.read_parquet(input_path)
    
    # Prepare features and target
    feature_cols = [col for col in df.columns if col not in ['timestamp', 'target', 'close']]
    X = df[feature_cols]
    y = df['target']
    prices = df['close'].values
    
    # Train/test split (time-based, NO SHUFFLE)
    split_idx = int(len(df) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    prices_test = prices[split_idx:]
    
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
        
        # ML Metrics
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        logger.info(f"ML Metrics - MSE: {mse:.6f}, MAE: {mae:.6f}, R2: {r2:.4f}")
        
        mlflow.log_metrics({
            'mse': mse,
            'mae': mae,
            'r2': r2
        })
        
        # === BACKTESTING ===
        logger.info("Running backtest with risk management...")
        
        strategy = QuantStrategy(
            transaction_cost=0.0005,  # 0.05%
            max_drawdown_threshold=0.20,  # 20%
            stop_loss=0.05,  # 5%
            position_sizing="confidence"
        )
        
        # Run backtest
        backtest_results = strategy.backtest(
            predictions=y_pred,
            actual_returns=y_test.values,
            prices=prices_test,
            confidence=np.abs(y_pred)
        )
        
        # Log trading metrics
        trading_metrics = {
            'total_return': backtest_results['total_return'],
            'annual_return': backtest_results['annual_return'],
            'sharpe_ratio': backtest_results['sharpe_ratio'],
            'sortino_ratio': backtest_results['sortino_ratio'],
            'calmar_ratio': backtest_results['calmar_ratio'],
            'max_drawdown': backtest_results['max_drawdown'],
            'win_rate': backtest_results['win_rate'],
            'profit_factor': backtest_results['profit_factor'],
            'n_trades': backtest_results['n_trades']
        }
        
        mlflow.log_metrics(trading_metrics)
        
        logger.info(f"Trading Performance:")
        logger.info(f"  Total Return: {backtest_results['total_return']:.2%}")
        logger.info(f"  Sharpe Ratio: {backtest_results['sharpe_ratio']:.3f}")
        logger.info(f"  Max Drawdown: {backtest_results['max_drawdown']:.2%}")
        logger.info(f"  Win Rate: {backtest_results['win_rate']:.2%}")
        
        # Advanced risk metrics
        advanced_metrics = calculate_advanced_metrics(
            backtest_results['strategy_returns']
        )
        mlflow.log_metrics(advanced_metrics)
        
        # Create visualizations
        logger.info("Creating performance visualizations...")
        create_performance_report(
            metrics=backtest_results,
            cumulative_returns=backtest_results['cumulative_returns'],
            returns=backtest_results['strategy_returns'],
            save_dir="reports"
        )
        
        # Feature importance
        plot_feature_importance(
            model,
            feature_names=feature_cols,
            save_path="reports/feature_importance.png"
        )
        
        # Log artifacts
        mlflow.log_artifacts("reports")
        
        # Log model
        mlflow.xgboost.log_model(
            model,
            "model",
            registered_model_name="xgboost-forecaster"
        )
        
        # Save training statistics for drift detection
        train_stats = {
            'feature_means': X_train.mean().to_dict(),
            'feature_stds': X_train.std().to_dict()
        }
        mlflow.log_dict(train_stats, "train_statistics.json")
        
        logger.info("Model training and backtesting completed!")
        
    return model, backtest_results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_xgboost()
