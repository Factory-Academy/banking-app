"""Helper utilities for risk assessment operations"""
from typing import Dict, Any, List
from app.models.transaction import RiskLevel, TransactionStatus


def safe_extract_risk_assessment(risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely extract risk assessment fields with defaults to prevent KeyError.
    
    Args:
        risk_assessment: Dictionary containing risk assessment results
    
    Returns:
        Dictionary with risk_score, risk_level, status, and fraud_flags
        using safe defaults if keys are missing
    """
    return {
        "risk_score": risk_assessment.get("risk_score", 0),
        "risk_level": risk_assessment.get("risk_level", RiskLevel.LOW),
        "status": risk_assessment.get("status", TransactionStatus.CLEARED),
        "fraud_flags": risk_assessment.get("fraud_flags", [])
    }
