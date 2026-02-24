"""Visualization tools for backtesting results."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# Set style
sns.set_style("darkgrid")
plt.rcParams['figure.figsize'] = (14, 8)


def plot_equity_curve(
    cumulative_returns: np.ndarray,
    benchmark_returns: np.ndarray = None,
    title: str = "Strategy Equity Curve",
    save_path: str = None
):
    """
    Plot equity curve with optional benchmark.
    
    Args:
        cumulative_returns: Strategy cumulative returns
        benchmark_returns: Benchmark cumulative returns (optional)
        title: Plot title
        save_path: Path to save figure
    """
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Plot strategy
    ax.plot(cumulative_returns, label='Strategy', linewidth=2, color='#2E86AB')
    
    # Plot benchmark if provided
    if benchmark_returns is not None:
        ax.plot(benchmark_returns, label='Buy & Hold', linewidth=2, 
                color='#A23B72', linestyle='--')
    
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('Time Period', fontsize=12)
    ax.set_ylabel('Cumulative Return', fontsize=12)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Equity curve saved to {save_path}")
    
    return fig


def plot_drawdown(
    cumulative_returns: np.ndarray,
    title: str = "Drawdown Analysis",
    save_path: str = None
):
    """
    Plot drawdown over time.
    
    Args:
        cumulative_returns: Cumulative returns
        title: Plot title
        save_path: Path to save figure
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Calculate drawdown
    peak = np.maximum.accumulate(cumulative_returns)
    drawdown = (peak - cumulative_returns) / peak
    
    # Plot equity curve
    ax1.plot(cumulative_returns, linewidth=2, color='#2E86AB')
    ax1.fill_between(range(len(cumulative_returns)), cumulative_returns, peak, 
                      alpha=0.3, color='red')
    ax1.set_title('Equity Curve with Drawdown', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Cumulative Return', fontsize=11)
    ax1.grid(True, alpha=0.3)
    
    # Plot drawdown
    ax2.fill_between(range(len(drawdown)), 0, -drawdown * 100, 
                      alpha=0.5, color='red')
    ax2.plot(-drawdown * 100, linewidth=2, color='darkred')
    ax2.set_title('Drawdown (%)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Time Period', fontsize=11)
    ax2.set_ylabel('Drawdown (%)', fontsize=11)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Drawdown plot saved to {save_path}")
    
    return fig


def plot_returns_distribution(
    returns: np.ndarray,
    title: str = "Returns Distribution",
    save_path: str = None
):
    """
    Plot returns distribution with statistics.
    
    Args:
        returns: Array of returns
        title: Plot title
        save_path: Path to save figure
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Histogram
    ax1.hist(returns, bins=50, alpha=0.7, color='#2E86AB', edgecolor='black')
    ax1.axvline(np.mean(returns), color='red', linestyle='--', 
                linewidth=2, label=f'Mean: {np.mean(returns):.4f}')
    ax1.axvline(np.median(returns), color='green', linestyle='--', 
                linewidth=2, label=f'Median: {np.median(returns):.4f}')
    ax1.set_title('Returns Histogram', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Return', fontsize=11)
    ax1.set_ylabel('Frequency', fontsize=11)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Q-Q plot
    from scipy import stats
    stats.probplot(returns, dist="norm", plot=ax2)
    ax2.set_title('Q-Q Plot (Normal Distribution)', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Returns distribution saved to {save_path}")
    
    return fig


def plot_rolling_metrics(
    returns: np.ndarray,
    window: int = 100,
    title: str = "Rolling Performance Metrics",
    save_path: str = None
):
    """
    Plot rolling Sharpe ratio and volatility.
    
    Args:
        returns: Array of returns
        window: Rolling window size
        title: Plot title
        save_path: Path to save figure
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    df = pd.DataFrame({'returns': returns})
    
    # Rolling Sharpe ratio (annualized)
    rolling_mean = df['returns'].rolling(window).mean() * 24 * 365
    rolling_std = df['returns'].rolling(window).std() * np.sqrt(24 * 365)
    rolling_sharpe = rolling_mean / rolling_std
    
    ax1.plot(rolling_sharpe, linewidth=2, color='#2E86AB')
    ax1.axhline(0, color='black', linestyle='--', alpha=0.5)
    ax1.set_title('Rolling Sharpe Ratio', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Sharpe Ratio', fontsize=11)
    ax1.grid(True, alpha=0.3)
    
    # Rolling volatility (annualized)
    ax2.plot(rolling_std * 100, linewidth=2, color='#A23B72')
    ax2.set_title('Rolling Volatility (Annualized)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Time Period', fontsize=11)
    ax2.set_ylabel('Volatility (%)', fontsize=11)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Rolling metrics saved to {save_path}")
    
    return fig


def plot_feature_importance(
    model,
    feature_names: list,
    top_n: int = 20,
    title: str = "Feature Importance",
    save_path: str = None
):
    """
    Plot feature importance from XGBoost model.
    
    Args:
        model: Trained XGBoost model
        feature_names: List of feature names
        top_n: Number of top features to show
        title: Plot title
        save_path: Path to save figure
    """
    import xgboost as xgb
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Get feature importance
    importance = model.feature_importances_
    indices = np.argsort(importance)[-top_n:]
    
    # Plot
    ax.barh(range(len(indices)), importance[indices], color='#2E86AB')
    ax.set_yticks(range(len(indices)))
    ax.set_yticklabels([feature_names[i] for i in indices])
    ax.set_xlabel('Importance', fontsize=11)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Feature importance saved to {save_path}")
    
    return fig


def plot_monthly_returns_heatmap(
    returns: np.ndarray,
    dates: pd.DatetimeIndex,
    title: str = "Monthly Returns Heatmap",
    save_path: str = None
):
    """
    Plot monthly returns as heatmap.
    
    Args:
        returns: Array of returns
        dates: DatetimeIndex
        title: Plot title
        save_path: Path to save figure
    """
    df = pd.DataFrame({'returns': returns}, index=dates)
    
    # Resample to monthly
    monthly_returns = df.resample('M').apply(lambda x: (1 + x).prod() - 1)
    
    # Pivot for heatmap
    monthly_returns['year'] = monthly_returns.index.year
    monthly_returns['month'] = monthly_returns.index.month
    pivot = monthly_returns.pivot(index='year', columns='month', values='returns')
    
    # Plot
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(pivot * 100, annot=True, fmt='.2f', cmap='RdYlGn', 
                center=0, ax=ax, cbar_kws={'label': 'Return (%)'})
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Month', fontsize=11)
    ax.set_ylabel('Year', fontsize=11)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Monthly returns heatmap saved to {save_path}")
    
    return fig


def create_performance_report(
    metrics: Dict,
    cumulative_returns: np.ndarray,
    returns: np.ndarray,
    save_dir: str = "reports"
):
    """
    Create comprehensive performance report with all visualizations.
    
    Args:
        metrics: Dictionary of performance metrics
        cumulative_returns: Cumulative returns
        returns: Period returns
        save_dir: Directory to save reports
    """
    import os
    os.makedirs(save_dir, exist_ok=True)
    
    # Equity curve
    plot_equity_curve(
        cumulative_returns,
        title="Strategy Performance",
        save_path=f"{save_dir}/equity_curve.png"
    )
    
    # Drawdown
    plot_drawdown(
        cumulative_returns,
        save_path=f"{save_dir}/drawdown.png"
    )
    
    # Returns distribution
    plot_returns_distribution(
        returns,
        save_path=f"{save_dir}/returns_distribution.png"
    )
    
    # Rolling metrics
    plot_rolling_metrics(
        returns,
        save_path=f"{save_dir}/rolling_metrics.png"
    )
    
    logger.info(f"Performance report created in {save_dir}/")
    
    plt.close('all')
