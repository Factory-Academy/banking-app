"""Tests for risk helper utilities"""
import pytest
from app.utils.risk_helpers import safe_extract_risk_assessment
from app.models.transaction import RiskLevel, TransactionStatus


class TestSafeExtractRiskAssessment:
    """Tests for safe_extract_risk_assessment function"""
    
    def test_extract_with_all_keys_present(self):
        """Test extraction when all keys are present"""
        risk_assessment = {
            "risk_score": 75,
            "risk_level": RiskLevel.HIGH,
            "status": TransactionStatus.HELD,
            "fraud_flags": ["high_amount", "velocity"]
        }
        
        result = safe_extract_risk_assessment(risk_assessment)
        
        assert result["risk_score"] == 75
        assert result["risk_level"] == RiskLevel.HIGH
        assert result["status"] == TransactionStatus.HELD
        assert result["fraud_flags"] == ["high_amount", "velocity"]
    
    def test_extract_with_missing_keys(self):
        """Test extraction when keys are missing (KeyError prevention)"""
        risk_assessment = {}
        
        result = safe_extract_risk_assessment(risk_assessment)
        
        assert result["risk_score"] == 0
        assert result["risk_level"] == RiskLevel.LOW
        assert result["status"] == TransactionStatus.CLEARED
        assert result["fraud_flags"] == []
    
    def test_extract_with_partial_keys(self):
        """Test extraction when only some keys are present"""
        risk_assessment = {
            "risk_score": 45,
            "fraud_flags": ["unusual_time"]
        }
        
        result = safe_extract_risk_assessment(risk_assessment)
        
        assert result["risk_score"] == 45
        assert result["risk_level"] == RiskLevel.LOW  # default
        assert result["status"] == TransactionStatus.CLEARED  # default
        assert result["fraud_flags"] == ["unusual_time"]
    
    def test_extract_with_none_values(self):
        """Test extraction when values are explicitly None"""
        risk_assessment = {
            "risk_score": None,
            "risk_level": None,
            "status": None,
            "fraud_flags": None
        }
        
        result = safe_extract_risk_assessment(risk_assessment)
        
        # None values should be preserved, not replaced with defaults
        assert result["risk_score"] is None
        assert result["risk_level"] is None
        assert result["status"] is None
        assert result["fraud_flags"] is None
    
    def test_extract_preserves_extra_keys(self):
        """Test that extra keys in input don't affect output"""
        risk_assessment = {
            "risk_score": 30,
            "risk_level": RiskLevel.MEDIUM,
            "status": TransactionStatus.CLEARED,
            "fraud_flags": ["first_international"],
            "extra_key": "should_not_appear"
        }
        
        result = safe_extract_risk_assessment(risk_assessment)
        
        # Should only have the expected keys
        assert set(result.keys()) == {"risk_score", "risk_level", "status", "fraud_flags"}
        assert "extra_key" not in result
