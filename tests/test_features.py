"""Tests for feature engineering."""
import pytest
import pandas as pd
import numpy as np


def test_feature_creation():
    """Test basic feature creation."""
    # Create sample data
    df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='1h'),
        'open': np.random.uniform(40000, 50000, 100),
        'high': np.random.uniform(40000, 50000, 100),
        'low': np.random.uniform(40000, 50000, 100),
        'close': np.random.uniform(40000, 50000, 100),
        'volume': np.random.uniform(100, 1000, 100)
    })
    
    # Test returns calculation
    df['returns'] = df['close'].pct_change()
    assert not df['returns'].isna().all()
    assert len(df) == 100


def test_lag_features():
    """Test lag feature creation."""
    df = pd.DataFrame({
        'close': [100, 101, 102, 103, 104]
    })
    
    df['close_lag_1'] = df['close'].shift(1)
    
    assert df['close_lag_1'].iloc[1] == 100
    assert df['close_lag_1'].iloc[2] == 101
    assert pd.isna(df['close_lag_1'].iloc[0])
