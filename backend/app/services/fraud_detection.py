from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any
from abc import ABC, abstractmethod
from app.models.transaction import Transaction, TransactionStatus, RiskLevel
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
    """Flag transactions over $10,000"""
    
    def __init__(self):
        super().__init__("high_amount", 30)
    
    def evaluate(self, transaction: Transaction, account_history: List[Transaction]) -> bool:
        return Decimal(str(transaction.amount)) > Decimal("10000")


class VelocityRule(FraudRule):
    """Flag more than 5 transactions within 1 hour"""
    
    def __init__(self):
        super().__init__("high_velocity", 40)
    
    def evaluate(self, transaction: Transaction, account_history: List[Transaction]) -> bool:
        one_hour_ago = transaction.timestamp - timedelta(hours=1)
        recent_transactions = [
            t for t in account_history
            if t.timestamp > one_hour_ago and t.timestamp <= transaction.timestamp
        ]
        return len(recent_transactions) > 5


class GeographicAnomalyRule(FraudRule):
    """Flag transactions in different country within 4 hours"""
    
    def __init__(self):
        super().__init__("geographic_anomaly", 50)
    
    def evaluate(self, transaction: Transaction, account_history: List[Transaction]) -> bool:
        if not account_history:
            return False
        
        four_hours_ago = transaction.timestamp - timedelta(hours=4)
        recent_transactions = [
            t for t in account_history
            if t.timestamp > four_hours_ago and t.timestamp < transaction.timestamp
        ]
        
        for prev_txn in recent_transactions:
            if prev_txn.location_country != transaction.location_country:
                # Check if physically impossible distance
                if transaction.latitude and transaction.longitude and prev_txn.latitude and prev_txn.longitude:
                    distance = self._calculate_distance(
                        prev_txn.latitude, prev_txn.longitude,
                        transaction.latitude, transaction.longitude
                    )
                    # If more than 500km apart, flag it
                    if distance > 500:
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
    """Flag transactions between 2 AM - 5 AM local time"""
    
    def __init__(self):
        super().__init__("unusual_time", 20)
    
    def evaluate(self, transaction: Transaction, account_history: List[Transaction]) -> bool:
        hour = transaction.timestamp.hour
        return 2 <= hour < 5


class FirstInternationalRule(FraudRule):
    """Flag first international transaction for account"""
    
    def __init__(self):
        super().__init__("first_international", 25)
    
    def evaluate(self, transaction: Transaction, account_history: List[Transaction]) -> bool:
        if transaction.location_country == "US":
            return False
        
        # Check if this is first international transaction
        international_history = [
            t for t in account_history
            if t.location_country != "US"
        ]
        
        return len(international_history) == 0


class AmountDeviationRule(FraudRule):
    """Flag transactions >3x the account's average"""
    
    def __init__(self):
        super().__init__("amount_deviation", 35)
    
    def evaluate(self, transaction: Transaction, account_history: List[Transaction]) -> bool:
        if not account_history or len(account_history) < 3:
            return False
        
        avg_amount = sum(Decimal(str(t.amount)) for t in account_history) / len(account_history)
        current_amount = Decimal(str(transaction.amount))
        
        return current_amount > (avg_amount * 3)


class FraudDetectionService:
    """Service for detecting fraudulent transactions"""
    
    def __init__(self):
        self.rules: List[FraudRule] = [
            HighAmountRule(),
            VelocityRule(),
            GeographicAnomalyRule(),
            UnusualTimeRule(),
            FirstInternationalRule(),
            AmountDeviationRule()
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
        
        # Determine risk level and status
        if total_score >= 70:
            risk_level = RiskLevel.HIGH
            status = TransactionStatus.HELD
        elif total_score >= 40:
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
