"""Main pipeline orchestrator."""
import logging
from ingestion.fetch_data import fetch_binance_data
from features.engineer_features import create_features
from training.train_model import train_xgboost

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_pipeline():
    """Execute the full ML pipeline."""
    logger.info("Starting pipeline...")
    
    # Step 1: Data ingestion
    logger.info("Step 1: Fetching data from Binance...")
    fetch_binance_data()
    
    # Step 2: Feature engineering
    logger.info("Step 2: Engineering features...")
    create_features()
    
    # Step 3: Model training
    logger.info("Step 3: Training model...")
    train_xgboost()
    
    logger.info("Pipeline completed successfully!")


if __name__ == "__main__":
    run_pipeline()
