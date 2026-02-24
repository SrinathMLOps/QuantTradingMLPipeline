"""Advanced risk metrics for quant trading."""
import numpy as np
import pandas as pd
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def calculate_var(returns: np.ndarray, confidence: float = 0.95) -> float:
    """
    Calculate Value at Risk (VaR).
    
    Args:
        returns: Array of returns
        confidence: Confidence level (default 95%)
        
    Returns:
        var: Value at Risk
    """
    return np.percentile(returns, (1 - confidence) * 100)


def calculate_cvar(returns: np.ndarray, confidence: float = 0.95) -> float:
    """
    Calculate Conditional Value at Risk (CVaR) / Expected Shortfall.
    
    Args:
        returns: Array of returns
        confidence: Confidence level (default 95%)
        
    Returns:
        cvar: Conditional Value at Risk
    """
    var = calculate_var(returns, confidence)
    return np.mean(returns[returns <= var])


def calculate_information_ratio(
    strategy_returns: np.ndarray,
    benchmark_returns: np.ndarray
) -> float:
    """
    Calculate Information Ratio.
    
    Args:
        strategy_returns: Strategy returns
        benchmark_returns: Benchmark returns
        
    Returns:
        ir: Information Ratio
    """
    excess_returns = strategy_returns - benchmark_returns
    tracking_error = np.std(excess_returns)
    
    if tracking_error == 0:
        return 0
    
    return np.mean(excess_returns) / tracking_error


def calculate_omega_ratio(returns: np.ndarray, threshold: float = 0.0) -> float:
    """
    Calculate Omega Ratio.
    
    Args:
        returns: Array of returns
        threshold: Threshold return (default 0)
        
    Returns:
        omega: Omega Ratio
    """
    gains = returns[returns > threshold] - threshold
    losses = threshold - returns[returns < threshold]
    
    if np.sum(losses) == 0:
        return np.inf
    
    return np.sum(gains) / np.sum(losses)


def calculate_tail_ratio(returns: np.ndarray) -> float:
    """
    Calculate Tail Ratio (95th percentile / 5th percentile).
    
    Args:
        returns: Array of returns
        
    Returns:
        tail_ratio: Tail Ratio
    """
    p95 = np.percentile(returns, 95)
    p5 = np.percentile(returns, 5)
    
    if p5 == 0:
        return np.inf
    
    return abs(p95 / p5)


def calculate_kelly_criterion(
    win_rate: float,
    avg_win: float,
    avg_loss: float
) -> float:
    """
    Calculate Kelly Criterion for optimal position sizing.
    
    Args:
        win_rate: Probability of winning
        avg_win: Average win amount
        avg_loss: Average loss amount (positive)
        
    Returns:
        kelly: Kelly percentage
    """
    if avg_loss == 0:
        return 0
    
    win_loss_ratio = avg_win / abs(avg_loss)
    kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
    
    # Apply fractional Kelly (half Kelly for safety)
    return max(0, kelly * 0.5)


def calculate_advanced_metrics(
    strategy_returns: np.ndarray,
    benchmark_returns: np.ndarray = None
) -> Dict:
    """
    Calculate comprehensive risk metrics.
    
    Args:
        strategy_returns: Strategy returns
        benchmark_returns: Benchmark returns (optional)
        
    Returns:
        metrics: Dictionary of risk metrics
    """
    metrics = {}
    
    # VaR and CVaR
    metrics['var_95'] = calculate_var(strategy_returns, 0.95)
    metrics['cvar_95'] = calculate_cvar(strategy_returns, 0.95)
    metrics['var_99'] = calculate_var(strategy_returns, 0.99)
    metrics['cvar_99'] = calculate_cvar(strategy_returns, 0.99)
    
    # Omega ratio
    metrics['omega_ratio'] = calculate_omega_ratio(strategy_returns)
    
    # Tail ratio
    metrics['tail_ratio'] = calculate_tail_ratio(strategy_returns)
    
    # Information ratio (if benchmark provided)
    if benchmark_returns is not None:
        metrics['information_ratio'] = calculate_information_ratio(
            strategy_returns, benchmark_returns
        )
    
    # Kelly criterion
    winning_trades = strategy_returns[strategy_returns > 0]
    losing_trades = strategy_returns[strategy_returns < 0]
    
    if len(strategy_returns) > 0:
        win_rate = len(winning_trades) / len(strategy_returns)
        avg_win = np.mean(winning_trades) if len(winning_trades) > 0 else 0
        avg_loss = abs(np.mean(losing_trades)) if len(losing_trades) > 0 else 0
        
        metrics['kelly_criterion'] = calculate_kelly_criterion(
            win_rate, avg_win, avg_loss
        )
    
    return metrics


def detect_regime_change(
    returns: np.ndarray,
    window: int = 50,
    threshold: float = 2.0
) -> np.ndarray:
    """
    Detect market regime changes using rolling statistics.
    
    Args:
        returns: Array of returns
        window: Rolling window size
        threshold: Number of standard deviations for detection
        
    Returns:
        regime_changes: Boolean array indicating regime changes
    """
    df = pd.DataFrame({'returns': returns})
    
    # Calculate rolling mean and std
    rolling_mean = df['returns'].rolling(window).mean()
    rolling_std = df['returns'].rolling(window).std()
    
    # Detect significant deviations
    z_score = (df['returns'] - rolling_mean) / rolling_std
    regime_changes = np.abs(z_score) > threshold
    
    return regime_changes.values


def calculate_drawdown_duration(cumulative_returns: np.ndarray) -> Dict:
    """
    Calculate drawdown duration statistics.
    
    Args:
        cumulative_returns: Cumulative returns series
        
    Returns:
        stats: Dictionary with drawdown duration stats
    """
    peak = np.maximum.accumulate(cumulative_returns)
    drawdown = (peak - cumulative_returns) / peak
    
    # Find drawdown periods
    in_drawdown = drawdown > 0
    drawdown_starts = np.where(np.diff(in_drawdown.astype(int)) == 1)[0]
    drawdown_ends = np.where(np.diff(in_drawdown.astype(int)) == -1)[0]
    
    # Calculate durations
    if len(drawdown_starts) > 0 and len(drawdown_ends) > 0:
        # Handle case where we're still in drawdown
        if len(drawdown_ends) < len(drawdown_starts):
            drawdown_ends = np.append(drawdown_ends, len(cumulative_returns) - 1)
        
        durations = drawdown_ends - drawdown_starts
        
        return {
            'avg_drawdown_duration': np.mean(durations),
            'max_drawdown_duration': np.max(durations),
            'n_drawdown_periods': len(durations)
        }
    
    return {
        'avg_drawdown_duration': 0,
        'max_drawdown_duration': 0,
        'n_drawdown_periods': 0
    }
