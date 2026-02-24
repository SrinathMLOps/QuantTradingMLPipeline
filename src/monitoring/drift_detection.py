"""Model drift detection for production monitoring."""
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Tuple
import logging
import json

logger = logging.getLogger(__name__)


class DriftDetector:
    """Detect distribution drift in production data."""
    
    def __init__(
        self,
        train_statistics: Dict,
        threshold_psi: float = 0.2,
        threshold_ks: float = 0.05
    ):
        """
        Initialize drift detector.
        
        Args:
            train_statistics: Training data statistics (means, stds)
            threshold_psi: PSI threshold for drift detection
            threshold_ks: KS test p-value threshold
        """
        self.train_means = train_statistics.get('feature_means', {})
        self.train_stds = train_statistics.get('feature_stds', {})
        self.threshold_psi = threshold_psi
        self.threshold_ks = threshold_ks
        
    def calculate_psi(
        self,
        expected: np.ndarray,
        actual: np.ndarray,
        bins: int = 10
    ) -> float:
        """
        Calculate Population Stability Index (PSI).
        
        PSI < 0.1: No significant change
        0.1 <= PSI < 0.2: Moderate change
        PSI >= 0.2: Significant change (drift detected)
        
        Args:
            expected: Training data distribution
            actual: Production data distribution
            bins: Number of bins for discretization
            
        Returns:
            psi: Population Stability Index
        """
        # Create bins based on expected distribution
        breakpoints = np.percentile(expected, np.linspace(0, 100, bins + 1))
        breakpoints = np.unique(breakpoints)
        
        # Discretize both distributions
        expected_percents = np.histogram(expected, bins=breakpoints)[0] / len(expected)
        actual_percents = np.histogram(actual, bins=breakpoints)[0] / len(actual)
        
        # Avoid division by zero
        expected_percents = np.where(expected_percents == 0, 0.0001, expected_percents)
        actual_percents = np.where(actual_percents == 0, 0.0001, actual_percents)
        
        # Calculate PSI
        psi = np.sum((actual_percents - expected_percents) * 
                     np.log(actual_percents / expected_percents))
        
        return psi
    
    def ks_test(
        self,
        expected: np.ndarray,
        actual: np.ndarray
    ) -> Tuple[float, float]:
        """
        Perform Kolmogorov-Smirnov test.
        
        Args:
            expected: Training data
            actual: Production data
            
        Returns:
            statistic: KS statistic
            p_value: p-value
        """
        statistic, p_value = stats.ks_2samp(expected, actual)
        return statistic, p_value
    
    def detect_feature_drift(
        self,
        production_data: pd.DataFrame,
        training_data: pd.DataFrame = None
    ) -> Dict:
        """
        Detect drift for each feature.
        
        Args:
            production_data: Production feature data
            training_data: Training feature data (optional)
            
        Returns:
            drift_report: Dictionary with drift detection results
        """
        drift_report = {
            'drift_detected': False,
            'features_with_drift': [],
            'feature_metrics': {}
        }
        
        for feature in production_data.columns:
            if feature not in self.train_means:
                logger.warning(f"Feature {feature} not in training statistics")
                continue
            
            prod_values = production_data[feature].values
            
            # Skip if all NaN
            if np.all(np.isnan(prod_values)):
                continue
            
            # Remove NaN values
            prod_values = prod_values[~np.isnan(prod_values)]
            
            if len(prod_values) == 0:
                continue
            
            # Calculate statistics
            prod_mean = np.mean(prod_values)
            prod_std = np.std(prod_values)
            
            train_mean = self.train_means[feature]
            train_std = self.train_stds[feature]
            
            # Z-score for mean shift
            if train_std > 0:
                z_score = abs(prod_mean - train_mean) / train_std
            else:
                z_score = 0
            
            # Mean shift detection (simple method)
            mean_shift_detected = z_score > 2.0
            
            # PSI calculation (if training data provided)
            psi = None
            if training_data is not None and feature in training_data.columns:
                train_values = training_data[feature].dropna().values
                if len(train_values) > 0:
                    psi = self.calculate_psi(train_values, prod_values)
            
            # KS test (if training data provided)
            ks_statistic = None
            ks_p_value = None
            if training_data is not None and feature in training_data.columns:
                train_values = training_data[feature].dropna().values
                if len(train_values) > 0:
                    ks_statistic, ks_p_value = self.ks_test(train_values, prod_values)
            
            # Determine if drift detected
            feature_drift = False
            
            if mean_shift_detected:
                feature_drift = True
                logger.warning(f"Mean shift detected for {feature}: z-score = {z_score:.2f}")
            
            if psi is not None and psi >= self.threshold_psi:
                feature_drift = True
                logger.warning(f"PSI drift detected for {feature}: PSI = {psi:.3f}")
            
            if ks_p_value is not None and ks_p_value < self.threshold_ks:
                feature_drift = True
                logger.warning(f"KS test drift detected for {feature}: p-value = {ks_p_value:.4f}")
            
            # Store metrics
            drift_report['feature_metrics'][feature] = {
                'prod_mean': float(prod_mean),
                'train_mean': float(train_mean),
                'prod_std': float(prod_std),
                'train_std': float(train_std),
                'z_score': float(z_score),
                'psi': float(psi) if psi is not None else None,
                'ks_statistic': float(ks_statistic) if ks_statistic is not None else None,
                'ks_p_value': float(ks_p_value) if ks_p_value is not None else None,
                'drift_detected': feature_drift
            }
            
            if feature_drift:
                drift_report['features_with_drift'].append(feature)
                drift_report['drift_detected'] = True
        
        return drift_report
    
    def log_drift_metrics(self, drift_report: Dict):
        """Log drift metrics to CloudWatch or logging system."""
        if drift_report['drift_detected']:
            logger.warning(
                f"DRIFT DETECTED! {len(drift_report['features_with_drift'])} features affected: "
                f"{', '.join(drift_report['features_with_drift'])}"
            )
        else:
            logger.info("No drift detected. Model is stable.")
        
        # Log detailed metrics
        for feature, metrics in drift_report['feature_metrics'].items():
            if metrics['drift_detected']:
                logger.warning(
                    f"Feature: {feature} | "
                    f"Z-score: {metrics['z_score']:.2f} | "
                    f"PSI: {metrics['psi']:.3f if metrics['psi'] else 'N/A'}"
                )
    
    def should_retrain(self, drift_report: Dict) -> bool:
        """
        Determine if model should be retrained based on drift.
        
        Args:
            drift_report: Drift detection report
            
        Returns:
            should_retrain: Boolean indicating if retraining is needed
        """
        # Retrain if more than 30% of features have drift
        if len(drift_report['features_with_drift']) > 0:
            drift_ratio = len(drift_report['features_with_drift']) / len(drift_report['feature_metrics'])
            
            if drift_ratio > 0.3:
                logger.warning(
                    f"Retraining recommended: {drift_ratio:.1%} of features have drift"
                )
                return True
        
        return False


def load_training_statistics(path: str = "train_statistics.json") -> Dict:
    """Load training statistics from file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Training statistics not found at {path}")
        return {}


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Load training statistics
    train_stats = load_training_statistics()
    
    # Initialize detector
    detector = DriftDetector(train_stats)
    
    # Simulate production data
    prod_data = pd.DataFrame({
        'feature1': np.random.normal(0, 1, 1000),
        'feature2': np.random.normal(0.5, 1.2, 1000)  # Shifted distribution
    })
    
    # Detect drift
    drift_report = detector.detect_feature_drift(prod_data)
    detector.log_drift_metrics(drift_report)
    
    # Check if retraining needed
    if detector.should_retrain(drift_report):
        logger.info("Triggering model retraining...")
