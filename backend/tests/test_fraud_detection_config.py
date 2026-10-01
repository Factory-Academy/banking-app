"""Tests for fraud detection configuration dataclass."""
import pytest
from decimal import Decimal
from dataclasses import FrozenInstanceError
from app.config.fraud_detection_config import FraudDetectionConfig, get_fraud_config


class TestFraudDetectionConfigDefaults:
    """Test default configuration values."""
    
    def test_default_high_amount_threshold(self):
        config = FraudDetectionConfig()
        assert config.high_amount_threshold == Decimal("10000")
    
    def test_default_velocity_settings(self):
        config = FraudDetectionConfig()
        assert config.velocity_max_transactions == 5
        assert config.velocity_time_window_hours == 1
    
    def test_default_geographic_settings(self):
        config = FraudDetectionConfig()
        assert config.geographic_time_window_hours == 4
        assert config.geographic_distance_threshold_km == 500.0
    
    def test_default_unusual_time_settings(self):
        config = FraudDetectionConfig()
        assert config.unusual_time_start_hour == 2
        assert config.unusual_time_end_hour == 5
    
    def test_default_home_country_code(self):
        config = FraudDetectionConfig()
        assert config.home_country_code == "US"
    
    def test_default_amount_deviation_settings(self):
        config = FraudDetectionConfig()
        assert config.amount_deviation_multiplier == 3
        assert config.amount_deviation_min_transactions == 3
    
    def test_default_risk_thresholds(self):
        config = FraudDetectionConfig()
        assert config.high_risk_threshold == 70
        assert config.medium_risk_threshold == 40
    
    def test_default_risk_points(self):
        config = FraudDetectionConfig()
        assert config.high_amount_points == 30
        assert config.velocity_points == 40
        assert config.geographic_anomaly_points == 50
        assert config.unusual_time_points == 20
        assert config.first_international_points == 25
        assert config.amount_deviation_points == 35


class TestFraudDetectionConfigImmutability:
    """Test that config is immutable (frozen)."""
    
    def test_cannot_modify_high_amount_threshold(self):
        config = FraudDetectionConfig()
        with pytest.raises(FrozenInstanceError):
            config.high_amount_threshold = Decimal("20000")
    
    def test_cannot_modify_velocity_max_transactions(self):
        config = FraudDetectionConfig()
        with pytest.raises(FrozenInstanceError):
            config.velocity_max_transactions = 10
    
    def test_cannot_modify_risk_thresholds(self):
        config = FraudDetectionConfig()
        with pytest.raises(FrozenInstanceError):
            config.high_risk_threshold = 100
    
    def test_cannot_modify_home_country_code(self):
        config = FraudDetectionConfig()
        with pytest.raises(FrozenInstanceError):
            config.home_country_code = "GB"


class TestFraudDetectionConfigValidation:
    """Test configuration validation logic."""
    
    def test_negative_high_amount_threshold_raises_error(self):
        with pytest.raises(ValueError, match="high_amount_threshold must be positive"):
            FraudDetectionConfig(high_amount_threshold=Decimal("-100"))
    
    def test_zero_high_amount_threshold_raises_error(self):
        with pytest.raises(ValueError, match="high_amount_threshold must be positive"):
            FraudDetectionConfig(high_amount_threshold=Decimal("0"))
    
    def test_negative_velocity_max_transactions_raises_error(self):
        with pytest.raises(ValueError, match="velocity_max_transactions must be positive"):
            FraudDetectionConfig(velocity_max_transactions=-1)
    
    def test_zero_velocity_max_transactions_raises_error(self):
        with pytest.raises(ValueError, match="velocity_max_transactions must be positive"):
            FraudDetectionConfig(velocity_max_transactions=0)
    
    def test_negative_velocity_time_window_raises_error(self):
        with pytest.raises(ValueError, match="velocity_time_window_hours must be positive"):
            FraudDetectionConfig(velocity_time_window_hours=-1)
    
    def test_negative_geographic_time_window_raises_error(self):
        with pytest.raises(ValueError, match="geographic_time_window_hours must be positive"):
            FraudDetectionConfig(geographic_time_window_hours=-1)
    
    def test_negative_geographic_distance_threshold_raises_error(self):
        with pytest.raises(ValueError, match="geographic_distance_threshold_km must be positive"):
            FraudDetectionConfig(geographic_distance_threshold_km=-100.0)
    
    def test_invalid_unusual_time_start_hour_negative(self):
        with pytest.raises(ValueError, match="unusual_time_start_hour must be between 0 and 23"):
            FraudDetectionConfig(unusual_time_start_hour=-1)
    
    def test_invalid_unusual_time_start_hour_too_large(self):
        with pytest.raises(ValueError, match="unusual_time_start_hour must be between 0 and 23"):
            FraudDetectionConfig(unusual_time_start_hour=24)
    
    def test_invalid_unusual_time_end_hour_negative(self):
        with pytest.raises(ValueError, match="unusual_time_end_hour must be between 0 and 24"):
            FraudDetectionConfig(unusual_time_end_hour=-1)
    
    def test_invalid_unusual_time_end_hour_too_large(self):
        with pytest.raises(ValueError, match="unusual_time_end_hour must be between 0 and 24"):
            FraudDetectionConfig(unusual_time_end_hour=25)
    
    def test_unusual_time_start_equal_to_end_raises_error(self):
        with pytest.raises(ValueError, match="unusual_time_start_hour must be less than unusual_time_end_hour"):
            FraudDetectionConfig(unusual_time_start_hour=5, unusual_time_end_hour=5)
    
    def test_unusual_time_start_greater_than_end_raises_error(self):
        with pytest.raises(ValueError, match="unusual_time_start_hour must be less than unusual_time_end_hour"):
            FraudDetectionConfig(unusual_time_start_hour=10, unusual_time_end_hour=5)
    
    def test_amount_deviation_multiplier_too_low_raises_error(self):
        with pytest.raises(ValueError, match="amount_deviation_multiplier must be greater than 1"):
            FraudDetectionConfig(amount_deviation_multiplier=1)
    
    def test_amount_deviation_multiplier_negative_raises_error(self):
        with pytest.raises(ValueError, match="amount_deviation_multiplier must be greater than 1"):
            FraudDetectionConfig(amount_deviation_multiplier=-1)
    
    def test_amount_deviation_min_transactions_zero_raises_error(self):
        with pytest.raises(ValueError, match="amount_deviation_min_transactions must be at least 1"):
            FraudDetectionConfig(amount_deviation_min_transactions=0)
    
    def test_amount_deviation_min_transactions_negative_raises_error(self):
        with pytest.raises(ValueError, match="amount_deviation_min_transactions must be at least 1"):
            FraudDetectionConfig(amount_deviation_min_transactions=-1)
    
    def test_high_risk_threshold_less_than_medium_raises_error(self):
        with pytest.raises(ValueError, match="high_risk_threshold must be greater than medium_risk_threshold"):
            FraudDetectionConfig(high_risk_threshold=40, medium_risk_threshold=70)
    
    def test_high_risk_threshold_equal_to_medium_raises_error(self):
        with pytest.raises(ValueError, match="high_risk_threshold must be greater than medium_risk_threshold"):
            FraudDetectionConfig(high_risk_threshold=50, medium_risk_threshold=50)
    
    def test_negative_medium_risk_threshold_raises_error(self):
        with pytest.raises(ValueError, match="medium_risk_threshold must be positive"):
            FraudDetectionConfig(medium_risk_threshold=-10)
    
    def test_negative_high_amount_points_raises_error(self):
        with pytest.raises(ValueError, match="high_amount_points must be non-negative"):
            FraudDetectionConfig(high_amount_points=-10)
    
    def test_negative_velocity_points_raises_error(self):
        with pytest.raises(ValueError, match="velocity_points must be non-negative"):
            FraudDetectionConfig(velocity_points=-20)
    
    def test_negative_geographic_anomaly_points_raises_error(self):
        with pytest.raises(ValueError, match="geographic_anomaly_points must be non-negative"):
            FraudDetectionConfig(geographic_anomaly_points=-30)
    
    def test_negative_unusual_time_points_raises_error(self):
        with pytest.raises(ValueError, match="unusual_time_points must be non-negative"):
            FraudDetectionConfig(unusual_time_points=-5)
    
    def test_negative_first_international_points_raises_error(self):
        with pytest.raises(ValueError, match="first_international_points must be non-negative"):
            FraudDetectionConfig(first_international_points=-15)
    
    def test_negative_amount_deviation_points_raises_error(self):
        with pytest.raises(ValueError, match="amount_deviation_points must be non-negative"):
            FraudDetectionConfig(amount_deviation_points=-25)


class TestFraudDetectionConfigCustomValues:
    """Test that custom configuration values can be set."""
    
    def test_custom_high_amount_threshold(self):
        config = FraudDetectionConfig(high_amount_threshold=Decimal("50000"))
        assert config.high_amount_threshold == Decimal("50000")
    
    def test_custom_velocity_settings(self):
        config = FraudDetectionConfig(
            velocity_max_transactions=10,
            velocity_time_window_hours=2
        )
        assert config.velocity_max_transactions == 10
        assert config.velocity_time_window_hours == 2
    
    def test_custom_geographic_settings(self):
        config = FraudDetectionConfig(
            geographic_time_window_hours=6,
            geographic_distance_threshold_km=1000.0
        )
        assert config.geographic_time_window_hours == 6
        assert config.geographic_distance_threshold_km == 1000.0
    
    def test_custom_unusual_time_settings(self):
        config = FraudDetectionConfig(
            unusual_time_start_hour=0,
            unusual_time_end_hour=6
        )
        assert config.unusual_time_start_hour == 0
        assert config.unusual_time_end_hour == 6
    
    def test_custom_home_country_code(self):
        config = FraudDetectionConfig(home_country_code="GB")
        assert config.home_country_code == "GB"
    
    def test_custom_amount_deviation_settings(self):
        config = FraudDetectionConfig(
            amount_deviation_multiplier=5,
            amount_deviation_min_transactions=10
        )
        assert config.amount_deviation_multiplier == 5
        assert config.amount_deviation_min_transactions == 10
    
    def test_custom_risk_thresholds(self):
        config = FraudDetectionConfig(
            high_risk_threshold=100,
            medium_risk_threshold=50
        )
        assert config.high_risk_threshold == 100
        assert config.medium_risk_threshold == 50
    
    def test_custom_risk_points(self):
        config = FraudDetectionConfig(
            high_amount_points=50,
            velocity_points=60,
            geographic_anomaly_points=70,
            unusual_time_points=30,
            first_international_points=40,
            amount_deviation_points=45
        )
        assert config.high_amount_points == 50
        assert config.velocity_points == 60
        assert config.geographic_anomaly_points == 70
        assert config.unusual_time_points == 30
        assert config.first_international_points == 40
        assert config.amount_deviation_points == 45
    
    def test_zero_risk_points_allowed(self):
        config = FraudDetectionConfig(
            high_amount_points=0,
            velocity_points=0,
            geographic_anomaly_points=0
        )
        assert config.high_amount_points == 0
        assert config.velocity_points == 0
        assert config.geographic_anomaly_points == 0


class TestGetFraudConfig:
    """Test the get_fraud_config function."""
    
    def test_get_fraud_config_returns_config_instance(self):
        config = get_fraud_config()
        assert isinstance(config, FraudDetectionConfig)
    
    def test_get_fraud_config_returns_same_instance(self):
        config1 = get_fraud_config()
        config2 = get_fraud_config()
        assert config1 is config2
    
    def test_get_fraud_config_has_default_values(self):
        config = get_fraud_config()
        assert config.high_amount_threshold == Decimal("10000")
        assert config.velocity_max_transactions == 5
        assert config.high_risk_threshold == 70


class TestFraudDetectionConfigEdgeCases:
    """Test edge cases for configuration values."""
    
    def test_unusual_time_boundary_values_valid(self):
        config = FraudDetectionConfig(
            unusual_time_start_hour=0,
            unusual_time_end_hour=24
        )
        assert config.unusual_time_start_hour == 0
        assert config.unusual_time_end_hour == 24
    
    def test_unusual_time_single_hour_valid(self):
        config = FraudDetectionConfig(
            unusual_time_start_hour=3,
            unusual_time_end_hour=4
        )
        assert config.unusual_time_start_hour == 3
        assert config.unusual_time_end_hour == 4
    
    def test_very_high_amount_threshold(self):
        config = FraudDetectionConfig(high_amount_threshold=Decimal("1000000"))
        assert config.high_amount_threshold == Decimal("1000000")
    
    def test_very_high_velocity_max_transactions(self):
        config = FraudDetectionConfig(velocity_max_transactions=1000)
        assert config.velocity_max_transactions == 1000
    
    def test_very_high_geographic_distance_threshold(self):
        config = FraudDetectionConfig(geographic_distance_threshold_km=50000.0)
        assert config.geographic_distance_threshold_km == 50000.0
    
    def test_amount_deviation_multiplier_decimal_values(self):
        # Multiplier should work with integers greater than 1
        config = FraudDetectionConfig(amount_deviation_multiplier=2)
        assert config.amount_deviation_multiplier == 2
    
    def test_amount_deviation_min_transactions_one(self):
        config = FraudDetectionConfig(amount_deviation_min_transactions=1)
        assert config.amount_deviation_min_transactions == 1
