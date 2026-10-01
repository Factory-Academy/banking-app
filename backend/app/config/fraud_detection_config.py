"""Fraud detection configuration using dataclasses.

This module centralizes all fraud detection rule thresholds and parameters
that were previously scattered across the fraud detection service module.
"""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class FraudDetectionConfig:
    """Configuration for fraud detection rules and thresholds.
    
    This dataclass is immutable (frozen=True) to prevent accidental modification
    of configuration values at runtime.
    
    Attributes:
        high_amount_threshold: Transaction amount threshold for high amount rule (USD)
        velocity_max_transactions: Maximum transactions allowed in velocity window
        velocity_time_window_hours: Time window for velocity rule (hours)
        geographic_time_window_hours: Time window for geographic anomaly rule (hours)
        geographic_distance_threshold_km: Distance threshold for geographic rule (km)
        unusual_time_start_hour: Start hour for unusual time rule (24-hour format)
        unusual_time_end_hour: End hour for unusual time rule (24-hour format)
        home_country_code: Default home country code for international rule
        amount_deviation_multiplier: Multiplier for amount deviation rule
        amount_deviation_min_transactions: Minimum transactions needed for deviation calculation
        high_risk_threshold: Risk score threshold for HIGH risk level
        medium_risk_threshold: Risk score threshold for MEDIUM risk level
        high_amount_points: Risk points awarded by high amount rule
        velocity_points: Risk points awarded by velocity rule
        geographic_anomaly_points: Risk points awarded by geographic anomaly rule
        unusual_time_points: Risk points awarded by unusual time rule
        first_international_points: Risk points awarded by first international rule
        amount_deviation_points: Risk points awarded by amount deviation rule
    """
    
    # Rule thresholds
    high_amount_threshold: Decimal = Decimal("10000")
    velocity_max_transactions: int = 5
    velocity_time_window_hours: int = 1
    geographic_time_window_hours: int = 4
    geographic_distance_threshold_km: float = 500.0
    unusual_time_start_hour: int = 2
    unusual_time_end_hour: int = 5
    home_country_code: str = "US"
    amount_deviation_multiplier: int = 3
    amount_deviation_min_transactions: int = 3
    
    # Risk level thresholds
    high_risk_threshold: int = 70
    medium_risk_threshold: int = 40
    
    # Risk points per rule
    high_amount_points: int = 30
    velocity_points: int = 40
    geographic_anomaly_points: int = 50
    unusual_time_points: int = 20
    first_international_points: int = 25
    amount_deviation_points: int = 35
    
    def __post_init__(self):
        """Validate configuration values after initialization."""
        if self.high_amount_threshold <= 0:
            raise ValueError("high_amount_threshold must be positive")
        
        if self.velocity_max_transactions <= 0:
            raise ValueError("velocity_max_transactions must be positive")
        
        if self.velocity_time_window_hours <= 0:
            raise ValueError("velocity_time_window_hours must be positive")
        
        if self.geographic_time_window_hours <= 0:
            raise ValueError("geographic_time_window_hours must be positive")
        
        if self.geographic_distance_threshold_km <= 0:
            raise ValueError("geographic_distance_threshold_km must be positive")
        
        if not (0 <= self.unusual_time_start_hour < 24):
            raise ValueError("unusual_time_start_hour must be between 0 and 23")
        
        if not (0 <= self.unusual_time_end_hour <= 24):
            raise ValueError("unusual_time_end_hour must be between 0 and 24")
        
        if self.unusual_time_start_hour >= self.unusual_time_end_hour:
            raise ValueError("unusual_time_start_hour must be less than unusual_time_end_hour")
        
        if self.amount_deviation_multiplier <= 1:
            raise ValueError("amount_deviation_multiplier must be greater than 1")
        
        if self.amount_deviation_min_transactions < 1:
            raise ValueError("amount_deviation_min_transactions must be at least 1")
        
        if self.high_risk_threshold <= self.medium_risk_threshold:
            raise ValueError("high_risk_threshold must be greater than medium_risk_threshold")
        
        if self.medium_risk_threshold <= 0:
            raise ValueError("medium_risk_threshold must be positive")
        
        # Validate all points are non-negative
        for field_name in [
            "high_amount_points",
            "velocity_points",
            "geographic_anomaly_points",
            "unusual_time_points",
            "first_international_points",
            "amount_deviation_points",
        ]:
            value = getattr(self, field_name)
            if value < 0:
                raise ValueError(f"{field_name} must be non-negative")


# Global default configuration instance
_default_config = FraudDetectionConfig()


def get_fraud_config() -> FraudDetectionConfig:
    """Get the current fraud detection configuration.
    
    Returns:
        FraudDetectionConfig: The fraud detection configuration instance
    """
    return _default_config
