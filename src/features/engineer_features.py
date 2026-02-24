"""Feature engineering for time series forecasting."""
import os
import logging
import pandas as pd
import ta

logger = logging.getLogger(__name__)


def create_features(input_path: str = "data/raw/BTCUSDT_1h.parquet"):
    """Create ML features from raw OHLCV data."""
    logger.info(f"Loading data from {input_path}")
    df = pd.read_parquet(input_path)
    
    # Sort by timestamp
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Price-based features
    df['returns'] = df['close'].pct_change()
    df['log_returns'] = pd.np.log(df['close'] / df['close'].shift(1))
    
    # Technical indicators
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_diff'] = macd.macd_diff()
    
    bb = ta.volatility.BollingerBands(df['close'])
    df['bb_high'] = bb.bollinger_hband()
    df['bb_low'] = bb.bollinger_lband()
    df['bb_mid'] = bb.bollinger_mavg()
    
    df['atr'] = ta.volatility.AverageTrueRange(
        df['high'], df['low'], df['close']
    ).average_true_range()
    
    # Lag features
    for lag in [1, 4, 24]:
        df[f'close_lag_{lag}'] = df['close'].shift(lag)
        df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
    
    # Rolling statistics
    for window in [7, 14, 30]:
        df[f'close_ma_{window}'] = df['close'].rolling(window).mean()
        df[f'close_std_{window}'] = df['close'].rolling(window).std()
        df[f'volume_ma_{window}'] = df['volume'].rolling(window).mean()
    
    # Time-based features
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['day_of_month'] = df['timestamp'].dt.day
    
    # Target variable (next hour return)
    df['target'] = df['close'].shift(-1) / df['close'] - 1
    
    # Drop NaN rows
    df = df.dropna()
    
    # Save features
    output_path = "data/processed/features.parquet"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    logger.info(f"Created {len(df.columns)} features, saved to {output_path}")
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_features()
