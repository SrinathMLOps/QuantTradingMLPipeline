"""Daily automated prediction script for cron job."""
import logging
import json
from datetime import datetime
from api.predict import LivePricePredictor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_daily_predictions():
    """Run daily predictions for all configured symbols."""
    logger.info("=" * 70)
    logger.info("DAILY CRYPTOCURRENCY PRICE PREDICTIONS")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 70)
    
    # Initialize predictor
    predictor = LivePricePredictor()
    
    # Symbols to predict
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT"]
    
    # Get predictions
    predictions = predictor.predict_multiple_symbols(symbols)
    
    # Display results
    print("\n" + "=" * 70)
    print("TOMORROW'S PRICE PREDICTIONS")
    print("=" * 70)
    
    for symbol, pred in predictions.items():
        print(f"\n{symbol}:")
        print(f"  Current Price:    ${pred['current_price']:>12,.2f}")
        print(f"  Predicted Price:  ${pred['predicted_price']:>12,.2f}")
        print(f"  Expected Return:  {pred['predicted_return_pct']:>12.2f}%")
        print(f"  Direction:        {pred['direction']:>12}")
        print(f"  Confidence:       {pred['confidence']:>12.1%}")
    
    # Get trading signals
    print("\n" + "=" * 70)
    print("TRADING SIGNALS")
    print("=" * 70)
    
    for symbol in symbols:
        signal = predictor.get_trading_signal(symbol, threshold=0.02)
        
        if signal:
            print(f"\n{symbol}:")
            print(f"  Action:           {signal['action']:>12}")
            print(f"  Position Size:    {signal['position_size']:>12.1%}")
            print(f"  Signal Strength:  {signal['signal_strength']:>12.2f}x")
    
    # Save predictions to file
    output_file = f"predictions/daily_{datetime.now().strftime('%Y%m%d')}.json"
    import os
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(predictions, f, indent=2, default=str)
    
    logger.info(f"Predictions saved to {output_file}")
    
    print("\n" + "=" * 70)
    print("PREDICTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    run_daily_predictions()
