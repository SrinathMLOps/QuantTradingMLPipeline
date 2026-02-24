"""Backtesting strategy with proper risk management."""
import numpy as np
import pandas as pd
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class QuantStrategy:
    """Professional quant trading strategy with risk controls."""
    
    def __init__(
        self,
        transaction_cost: float = 0.0005,  # 0.05% per trade
        max_drawdown_threshold: float = 0.20,  # 20% max drawdown
        stop_loss: float = 0.05,  # 5% stop loss per position
        position_sizing: str = "confidence",  # "fixed" or "confidence"
        max_position_size: float = 1.0
    ):
        self.transaction_cost = transaction_cost
        self.max_drawdown_threshold = max_drawdown_threshold
        self.stop_loss = stop_loss
        self.position_sizing = position_sizing
        self.max_position_size = max_position_size
        
    def generate_signals(
        self,
        predictions: np.ndarray,
        confidence: np.ndarray = None
    ) -> np.ndarray:
        """
        Generate trading signals from model predictions.
        
        Args:
            predictions: Model predictions (returns)
            confidence: Model confidence scores (optional)
            
        Returns:
            signals: Position sizes (-1 to 1)
        """
        if self.position_sizing == "fixed":
            # Simple binary signals
            signals = np.where(predictions > 0, 1, -1)
        else:
            # Confidence-based position sizing
            if confidence is None:
                confidence = np.abs(predictions)
            
            # Scale by confidence, clip to max position size
            signals = np.clip(
                predictions * confidence * 10,
                -self.max_position_size,
                self.max_position_size
            )
        
        return signals
    
    def apply_risk_controls(
        self,
        signals: np.ndarray,
        returns: np.ndarray,
        prices: np.ndarray
    ) -> Tuple[np.ndarray, Dict]:
        """
        Apply risk management rules.
        
        Returns:
            controlled_signals: Signals after risk controls
            risk_events: Dictionary of risk events
        """
        controlled_signals = signals.copy()
        risk_events = {
            'stop_loss_triggered': 0,
            'max_drawdown_triggered': 0,
            'trading_halted_at': None
        }
        
        cumulative_return = np.zeros(len(signals))
        peak = 1.0
        
        for i in range(len(signals)):
            if i == 0:
                cumulative_return[i] = 1.0
                continue
            
            # Calculate cumulative return
            cumulative_return[i] = cumulative_return[i-1] * (1 + returns[i] * controlled_signals[i-1])
            
            # Update peak
            if cumulative_return[i] > peak:
                peak = cumulative_return[i]
            
            # Calculate drawdown
            drawdown = (peak - cumulative_return[i]) / peak
            
            # Max drawdown control - halt trading
            if drawdown > self.max_drawdown_threshold:
                controlled_signals[i:] = 0
                risk_events['max_drawdown_triggered'] = 1
                risk_events['trading_halted_at'] = i
                logger.warning(f"Max drawdown exceeded at index {i}. Trading halted.")
                break
            
            # Stop loss per position
            if i > 0 and controlled_signals[i-1] != 0:
                position_return = returns[i] * controlled_signals[i-1]
                if position_return < -self.stop_loss:
                    controlled_signals[i] = 0
                    risk_events['stop_loss_triggered'] += 1
        
        return controlled_signals, risk_events
    
    def calculate_transaction_costs(
        self,
        signals: np.ndarray
    ) -> np.ndarray:
        """Calculate transaction costs based on position changes."""
        # Calculate position changes (trades)
        trades = np.abs(np.diff(signals, prepend=0))
        costs = trades * self.transaction_cost
        return costs
    
    def backtest(
        self,
        predictions: np.ndarray,
        actual_returns: np.ndarray,
        prices: np.ndarray,
        confidence: np.ndarray = None
    ) -> Dict:
        """
        Run complete backtest with risk management.
        
        Returns:
            results: Dictionary with performance metrics
        """
        # Generate signals
        signals = self.generate_signals(predictions, confidence)
        
        # Apply risk controls
        controlled_signals, risk_events = self.apply_risk_controls(
            signals, actual_returns, prices
        )
        
        # Calculate transaction costs
        costs = self.calculate_transaction_costs(controlled_signals)
        
        # Calculate strategy returns
        strategy_returns = controlled_signals * actual_returns - costs
        
        # Calculate cumulative returns
        cumulative_returns = (1 + strategy_returns).cumprod()
        
        # Calculate metrics
        metrics = self.calculate_metrics(
            strategy_returns,
            cumulative_returns,
            controlled_signals,
            risk_events
        )
        
        # Add time series data
        metrics['cumulative_returns'] = cumulative_returns
        metrics['strategy_returns'] = strategy_returns
        metrics['signals'] = controlled_signals
        metrics['costs'] = costs
        
        return metrics
    
    def calculate_metrics(
        self,
        returns: np.ndarray,
        cumulative_returns: np.ndarray,
        signals: np.ndarray,
        risk_events: Dict
    ) -> Dict:
        """Calculate comprehensive performance metrics."""
        
        # Basic returns
        total_return = cumulative_returns[-1] - 1
        
        # Annualized metrics (assuming hourly data)
        periods_per_year = 24 * 365
        n_periods = len(returns)
        years = n_periods / periods_per_year
        
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        annual_vol = np.std(returns) * np.sqrt(periods_per_year)
        
        # Sharpe ratio (assuming 0% risk-free rate)
        sharpe_ratio = annual_return / annual_vol if annual_vol > 0 else 0
        
        # Maximum drawdown
        peak = np.maximum.accumulate(cumulative_returns)
        drawdown = (peak - cumulative_returns) / peak
        max_drawdown = np.max(drawdown)
        
        # Win rate
        winning_trades = returns[returns > 0]
        losing_trades = returns[returns < 0]
        win_rate = len(winning_trades) / len(returns) if len(returns) > 0 else 0
        
        # Average win/loss
        avg_win = np.mean(winning_trades) if len(winning_trades) > 0 else 0
        avg_loss = np.mean(losing_trades) if len(losing_trades) > 0 else 0
        
        # Profit factor
        total_wins = np.sum(winning_trades)
        total_losses = abs(np.sum(losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        # Number of trades
        n_trades = np.sum(np.abs(np.diff(signals, prepend=0)) > 0)
        
        # Sortino ratio (downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = np.std(downside_returns) * np.sqrt(periods_per_year)
        sortino_ratio = annual_return / downside_std if downside_std > 0 else 0
        
        # Calmar ratio (return / max drawdown)
        calmar_ratio = annual_return / max_drawdown if max_drawdown > 0 else 0
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'annual_volatility': annual_vol,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'n_trades': n_trades,
            'risk_events': risk_events
        }


def walk_forward_validation(
    df: pd.DataFrame,
    train_func,
    predict_func,
    n_splits: int = 3,
    train_size: float = 0.6
) -> pd.DataFrame:
    """
    Walk-forward validation for time series.
    
    Args:
        df: DataFrame with features and target
        train_func: Function to train model
        predict_func: Function to make predictions
        n_splits: Number of walk-forward splits
        train_size: Proportion of data for training
        
    Returns:
        results_df: DataFrame with results for each split
    """
    results = []
    
    split_size = len(df) // n_splits
    
    for i in range(n_splits):
        # Define train/test windows
        train_start = i * split_size
        train_end = train_start + int(split_size * train_size)
        test_end = min(train_end + split_size, len(df))
        
        # Split data
        train_data = df.iloc[train_start:train_end]
        test_data = df.iloc[train_end:test_end]
        
        logger.info(f"Split {i+1}/{n_splits}: Train {train_start}:{train_end}, Test {train_end}:{test_end}")
        
        # Train and predict
        model = train_func(train_data)
        predictions = predict_func(model, test_data)
        
        # Store results
        results.append({
            'split': i + 1,
            'train_start': train_start,
            'train_end': train_end,
            'test_start': train_end,
            'test_end': test_end,
            'predictions': predictions,
            'actuals': test_data['target'].values
        })
    
    return pd.DataFrame(results)
