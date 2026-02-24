"""Live data ingestion from Binance API with real-time updates."""
import os
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd
from binance.client import Client
import boto3
import json

logger = logging.getLogger(__name__)


class BinanceLiveDataFetcher:
    """Fetch live data from Binance with real-time updates."""
    
    def __init__(
        self,
        api_key: str = None,
        api_secret: str = None,
        symbols: List[str] = None
    ):
        """
        Initialize Binance client.
        
        Args:
            api_key: Binance API key (optional for public data)
            api_secret: Binance API secret (optional for public data)
            symbols: List of trading pairs (default: ["BTCUSDT"])
        """
        self.api_key = api_key or os.getenv("BINANCE_API_KEY", "")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET", "")
        self.client = Client(self.api_key, self.api_secret)
        self.symbols = symbols or ["BTCUSDT"]
        
    def get_current_price(self, symbol: str = "BTCUSDT") -> Dict:
        """
        Get current live price from Binance.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            price_data: Dictionary with current price info
        """
        try:
            ticker = self.client.get_ticker(symbol=symbol)
            
            return {
                'symbol': symbol,
                'price': float(ticker['lastPrice']),
                'volume_24h': float(ticker['volume']),
                'price_change_24h': float(ticker['priceChange']),
                'price_change_pct_24h': float(ticker['priceChangePercent']),
                'high_24h': float(ticker['highPrice']),
                'low_24h': float(ticker['lowPrice']),
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {e}")
            return None
    
    def get_latest_klines(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1h",
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Get latest klines (candlestick data) from Binance.
        
        Args:
            symbol: Trading pair symbol
            interval: Kline interval (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of klines to fetch (max 1000)
            
        Returns:
            df: DataFrame with OHLCV data
        """
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Clean data
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            df[numeric_cols] = df[numeric_cols].astype(float)
            
            logger.info(f"Fetched {len(df)} latest klines for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching klines for {symbol}: {e}")
            return None
    
    def fetch_historical_data(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1h",
        days_back: int = 90
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from Binance.
        
        Args:
            symbol: Trading pair symbol
            interval: Kline interval
            days_back: Number of days to fetch
            
        Returns:
            df: DataFrame with historical data
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)
        
        logger.info(f"Fetching {symbol} data from {start_time} to {end_time}")
        
        # Fetch klines with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                klines = self.client.get_historical_klines(
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
        
        return df
    
    def save_data(
        self,
        df: pd.DataFrame,
        symbol: str,
        interval: str,
        data_type: str = "historical"
    ):
        """
        Save data to local storage or S3.
        
        Args:
            df: DataFrame to save
            symbol: Trading pair symbol
            interval: Kline interval
            data_type: Type of data (historical, live, latest)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if data_type == "historical":
            output_path = f"data/raw/{symbol}_{interval}.parquet"
        else:
            output_path = f"data/live/{symbol}_{interval}_{timestamp}.parquet"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_parquet(output_path, index=False)
        
        logger.info(f"Saved {len(df)} records to {output_path}")
        return output_path
    
    def get_order_book(self, symbol: str = "BTCUSDT", limit: int = 100) -> Dict:
        """
        Get current order book depth.
        
        Args:
            symbol: Trading pair symbol
            limit: Number of orders to fetch (5, 10, 20, 50, 100, 500, 1000)
            
        Returns:
            order_book: Dictionary with bids and asks
        """
        try:
            depth = self.client.get_order_book(symbol=symbol, limit=limit)
            
            return {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'bids': [[float(price), float(qty)] for price, qty in depth['bids']],
                'asks': [[float(price), float(qty)] for price, qty in depth['asks']],
                'bid_volume': sum([float(qty) for _, qty in depth['bids']]),
                'ask_volume': sum([float(qty) for _, qty in depth['asks']])
            }
        except Exception as e:
            logger.error(f"Error fetching order book for {symbol}: {e}")
            return None
    
    def get_recent_trades(self, symbol: str = "BTCUSDT", limit: int = 100) -> pd.DataFrame:
        """
        Get recent trades.
        
        Args:
            symbol: Trading pair symbol
            limit: Number of trades to fetch (max 1000)
            
        Returns:
            df: DataFrame with recent trades
        """
        try:
            trades = self.client.get_recent_trades(symbol=symbol, limit=limit)
            
            df = pd.DataFrame(trades)
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            df['price'] = df['price'].astype(float)
            df['qty'] = df['qty'].astype(float)
            
            return df
        except Exception as e:
            logger.error(f"Error fetching recent trades for {symbol}: {e}")
            return None
    
    def fetch_all_symbols_data(self, interval: str = "1h") -> Dict[str, pd.DataFrame]:
        """
        Fetch data for all configured symbols.
        
        Args:
            interval: Kline interval
            
        Returns:
            data: Dictionary mapping symbol to DataFrame
        """
        data = {}
        
        for symbol in self.symbols:
            logger.info(f"Fetching data for {symbol}...")
            df = self.get_latest_klines(symbol, interval)
            
            if df is not None:
                data[symbol] = df
                self.save_data(df, symbol, interval, "live")
            
            time.sleep(0.5)  # Rate limiting
        
        return data


def fetch_binance_data(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    days_back: int = 90
):
    """
    Fetch historical data from Binance (backward compatibility).
    
    Args:
        symbol: Trading pair symbol
        interval: Kline interval
        days_back: Number of days to fetch
        
    Returns:
        df: DataFrame with historical data
    """
    fetcher = BinanceLiveDataFetcher()
    df = fetcher.fetch_historical_data(symbol, interval, days_back)
    fetcher.save_data(df, symbol, interval, "historical")
    return df


def fetch_live_data(symbols: List[str] = None, interval: str = "1h"):
    """
    Fetch live data for multiple symbols.
    
    Args:
        symbols: List of trading pairs
        interval: Kline interval
        
    Returns:
        data: Dictionary mapping symbol to DataFrame
    """
    fetcher = BinanceLiveDataFetcher(symbols=symbols)
    return fetcher.fetch_all_symbols_data(interval)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Fetch historical data
    logger.info("Fetching historical data...")
    fetch_binance_data()
    
    # Fetch live data
    logger.info("Fetching live data...")
    live_data = fetch_live_data(["BTCUSDT", "ETHUSDT"])
    
    # Get current price
    fetcher = BinanceLiveDataFetcher()
    current_price = fetcher.get_current_price("BTCUSDT")
    logger.info(f"Current BTC price: ${current_price['price']:,.2f}")
