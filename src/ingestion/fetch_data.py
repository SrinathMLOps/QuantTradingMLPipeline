"""Data ingestion from Binance API."""
import os
import time
import logging
from datetime import datetime, timedelta
import pandas as pd
from binance.client import Client
import boto3

logger = logging.getLogger(__name__)


def fetch_binance_data(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    days_back: int = 90
):
    """Fetch OHLCV data from Binance."""
    api_key = os.getenv("BINANCE_API_KEY", "")
    api_secret = os.getenv("BINANCE_API_SECRET", "")
    
    client = Client(api_key, api_secret)
    
    # Calculate date range
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days_back)
    
    logger.info(f"Fetching {symbol} data from {start_time} to {end_time}")
    
    # Fetch klines with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            klines = client.get_historical_klines(
                symbol,
                interval,
                start_time.strftime("%d %b %Y %H:%M:%S"),
                end_time.strftime("%d %b %Y %H:%M:%S")
            )
            break
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
    
    # Convert to DataFrame
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
        'taker_buy_quote', 'ignore'
    ])
    
    # Clean data
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    df[numeric_cols] = df[numeric_cols].astype(float)
    
    # Save to S3 or local
    output_path = f"data/raw/{symbol}_{interval}.parquet"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    logger.info(f"Saved {len(df)} records to {output_path}")
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetch_binance_data()
