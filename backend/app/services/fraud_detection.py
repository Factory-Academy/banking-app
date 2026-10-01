from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any
from abc import ABC, abstractmethod
from app.models.transaction import Transaction, TransactionStatus, RiskLevel
from app.config.fraud_detection_config import FraudDetectionConfig, get_fraud_config
from math import radians, sin, cos, sqrt, atan2


class FraudRule(ABC):
    """Base class for fraud detection rules"""
    
    def __init__(self, name: str, risk_points: int):
        self.name = name
        self.risk_points = risk_points
    
    @abstractmethod
    def evaluate(self, transaction: Transaction, account_history: List[Transaction]) -> bool:
        """Returns True if rule is triggered"""
        pass


class HighAmountRule(FraudRule):
    """Flag transactions over the configured threshold"""
    
    def __init__(self, config: FraudDetectionConfig = None):
        self.config = config or get_fraud_config()
        super().__init__("high_amount", self.config.high_amount_points)
    
    def evaluate(self, transaction: Transaction, account_history: List[Transaction]) -> bool:
        return Decimal(str(transaction.amount)) > self.config.high_amount_threshold


class VelocityRule(FraudRule):
    """Flag excessive transactions within configured time window"""
    
    def __init__(self, config: FraudDetectionConfig = None):
        self.config = config or get_fraud_config()
        super().__init__("high_velocity", self.config.velocity_points)
    
    def evaluate(self, transaction: Transaction, account_history: List[Transaction]) -> bool:
        time_window_ago = transaction.timestamp - timedelta(hours=self.config.velocity_time_window_hours)
        recent_transactions = [
            t for t in account_history
            if t.timestamp > time_window_ago and t.timestamp <= transaction.timestamp
        ]
        return len(recent_transactions) > self.config.velocity_max_transactions


class GeographicAnomalyRule(FraudRule):
    """Flag transactions in different country within configured time window"""
    
    def __init__(self, config: FraudDetectionConfig = None):
        self.config = config or get_fraud_config()
        super().__init__("geographic_anomaly", self.config.geographic_anomaly_points)
    
    def evaluate(self, transaction: Transaction, account_history: List[Transaction]) -> bool:
        if not account_history:
            return False
        
        time_window_ago = transaction.timestamp - timedelta(hours=self.config.geographic_time_window_hours)
        recent_transactions = [
            t for t in account_history
            if t.timestamp > time_window_ago and t.timestamp < transaction.timestamp
        ]
        
        for prev_txn in recent_transactions:
            if prev_txn.location_country != transaction.location_country:
                # Check if physically impossible distance
                if transaction.latitude and transaction.longitude and prev_txn.latitude and prev_txn.longitude:
                    distance = self._calculate_distance(
                        prev_txn.latitude, prev_txn.longitude,
                        transaction.latitude, transaction.longitude
                    )
                    # If more than threshold distance apart, flag it
                    if distance > self.config.geographic_distance_threshold_km:
                        return True
                else:
                    # No coordinates, just check country difference
                    return True
        return False
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in km using Haversine formula"""
        R = 6371  # Earth radius in km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c


class UnusualTimeRule(FraudRule):
    """Flag transactions during configured unusual hours"""
    
    def __init__(self, config: FraudDetectionConfig = None):
        self.config = config or get_fraud_config()
        super().__init__("unusual_time", self.config.unusual_time_points)
    
    def evaluate(self, transaction: Transaction, account_history: List[Transaction]) -> bool:
        hour = transaction.timestamp.hour
        return self.config.unusual_time_start_hour <= hour < self.config.unusual_time_end_hour


class FirstInternationalRule(FraudRule):
    """Flag first international transaction for account"""
    
    def __init__(self, config: FraudDetectionConfig = None):
        self.config = config or get_fraud_config()
        super().__init__("first_international", self.config.first_international_points)
    
    def evaluate(self, transaction: Transaction, account_history: List[Transaction]) -> bool:
        if transaction.location_country == self.config.home_country_code:
            return False
        
        # Check if this is first international transaction
        international_history = [
            t for t in account_history
            if t.location_country != self.config.home_country_code
        ]
        
        return len(international_history) == 0


class AmountDeviationRule(FraudRule):
    """Flag transactions exceeding configured multiplier of account average"""
    
    def __init__(self, config: FraudDetectionConfig = None):
        self.config = config or get_fraud_config()
        super().__init__("amount_deviation", self.config.amount_deviation_points)
    
    def evaluate(self, transaction: Transaction, account_history: List[Transaction]) -> bool:
        if not account_history or len(account_history) < self.config.amount_deviation_min_transactions:
            return False
        
        avg_amount = sum(Decimal(str(t.amount)) for t in account_history) / len(account_history)
        current_amount = Decimal(str(transaction.amount))
        
        return current_amount > (avg_amount * self.config.amount_deviation_multiplier)


class FraudDetectionService:
    """Service for detecting fraudulent transactions"""
    
    def __init__(self, config: FraudDetectionConfig = None):
        self.config = config or get_fraud_config()
        self.rules: List[FraudRule] = [
            HighAmountRule(self.config),
            VelocityRule(self.config),
            GeographicAnomalyRule(self.config),
            UnusualTimeRule(self.config),
            FirstInternationalRule(self.config),
            AmountDeviationRule(self.config)
        ]
    
    def analyze_transaction(
        self,
        transaction: Transaction,
        account_history: List[Transaction]
    ) -> Dict[str, Any]:
        """
        Analyze a transaction and return risk assessment
        
        Returns:
            dict with risk_score, risk_level, status, and fraud_flags
        """
        total_score = 0
        flags = []
        
        for rule in self.rules:
            if rule.evaluate(transaction, account_history):
                total_score += rule.risk_points
                flags.append(rule.name)
        
        # Determine risk level and status using config thresholds
        if total_score >= self.config.high_risk_threshold:
            risk_level = RiskLevel.HIGH
            status = TransactionStatus.HELD
        elif total_score >= self.config.medium_risk_threshold:
            risk_level = RiskLevel.MEDIUM
            status = TransactionStatus.CLEARED
        else:
            risk_level = RiskLevel.LOW
            status = TransactionStatus.CLEARED
        
        return {
            "risk_score": total_score,
            "risk_level": risk_level,
            "status": status,
            "fraud_flags": flags
        }
