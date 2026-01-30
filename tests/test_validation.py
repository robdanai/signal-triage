"""
Tests for validation module — sanity checks and data integrity.
"""

import pytest
from decimal import Decimal

from signal_triage.validation import (
    validate_waterfall,
    validate_capital_structure,
    validate_ev_inputs,
    ValidationError,
    ValidationResult,
    graceful_degradation_report,
)


def test_validate_waterfall_success():
    """Test waterfall validation with valid data."""
    tranches = [
        {"name": "Senior", "claim": 100.0, "tier": 1},
        {"name": "Junior", "claim": 50.0, "tier": 2},
    ]
    
    waterfall_result = {
        "recoveries": [
            {"name": "Senior", "claim": Decimal("100.0"), "recovered": Decimal("100.0"), "recovery_pct": Decimal("100.0")},
            {"name": "Junior", "claim": Decimal("50.0"), "recovered": Decimal("50.0"), "recovery_pct": Decimal("100.0")},
        ],
        "fulcrum_security": None,
        "ev_used": Decimal("150.0"),
        "ev_remaining": Decimal("0.0"),
        "apr_violations": [],
    }
    
    result = validate_waterfall(waterfall_result, 150.0, tranches)
    
    assert result.valid is True
    assert len([e for e in result.errors if e.severity == ValidationError.SEVERITY_CRITICAL]) == 0


def test_validate_waterfall_recovery_exceeds_ev():
    """Test waterfall validation when total recovery exceeds EV."""
    waterfall_result = {
        "recoveries": [
            {"name": "Senior", "claim": Decimal("100.0"), "recovered": Decimal("200.0"), "recovery_pct": Decimal("200.0")},
        ],
        "fulcrum_security": "Senior",
        "ev_used": Decimal("200.0"),
        "ev_remaining": Decimal("0.0"),
        "apr_violations": [],
    }
    
    result = validate_waterfall(waterfall_result, 100.0)
    
    assert result.valid is False
    assert any(e.code == "RECOVERY_EXCEEDS_EV" for e in result.errors)


def test_validate_waterfall_recovery_exceeds_claim():
    """Test waterfall validation when recovery exceeds claim."""
    waterfall_result = {
        "recoveries": [
            {"name": "Senior", "claim": Decimal("100.0"), "recovered": Decimal("150.0"), "recovery_pct": Decimal("150.0")},
        ],
        "fulcrum_security": "Senior",
        "ev_used": Decimal("150.0"),
        "ev_remaining": Decimal("0.0"),
        "apr_violations": [],
    }
    
    result = validate_waterfall(waterfall_result, 150.0)
    
    assert result.valid is False
    assert any(e.code == "RECOVERY_EXCEEDS_CLAIM" for e in result.errors)


def test_validate_waterfall_ev_accounting_mismatch():
    """Test waterfall validation when EV accounting doesn't add up."""
    waterfall_result = {
        "recoveries": [
            {"name": "Senior", "claim": Decimal("100.0"), "recovered": Decimal("50.0"), "recovery_pct": Decimal("50.0")},
        ],
        "fulcrum_security": "Senior",
        "ev_used": Decimal("50.0"),
        "ev_remaining": Decimal("60.0"),  # Should be 50.0 if total EV is 100.0
        "apr_violations": [],
    }
    
    result = validate_waterfall(waterfall_result, 100.0)
    
    assert result.valid is False
    assert any(e.code == "EV_ACCOUNTING_MISMATCH" for e in result.errors)


def test_validate_waterfall_apr_violation():
    """Test waterfall validation with APR violation."""
    waterfall_result = {
        "recoveries": [
            {"name": "Senior", "claim": Decimal("100.0"), "recovered": Decimal("50.0"), "recovery_pct": Decimal("50.0")},
            {"name": "Junior", "claim": Decimal("50.0"), "recovered": Decimal("10.0"), "recovery_pct": Decimal("20.0")},
        ],
        "fulcrum_security": "Senior",
        "ev_used": Decimal("60.0"),
        "ev_remaining": Decimal("0.0"),
        "apr_violations": [
            {
                "senior_tranche": "Senior",
                "senior_recovery_pct": "50.0",
                "junior_tranche": "Junior",
                "junior_recovery": "10.0",
                "note": "APR violation",
            }
        ],
    }
    
    result = validate_waterfall(waterfall_result, 60.0)
    
    # APR violations are warnings, not critical errors
    assert result.valid is True
    assert any(e.code == "APR_VIOLATION" and e.severity == ValidationError.SEVERITY_WARNING for e in result.errors)


def test_validate_capital_structure_success():
    """Test capital structure validation with valid data."""
    tranches = [
        {"name": "Senior", "claim": 100.0, "tier": 1},
        {"name": "Junior", "claim": 50.0, "tier": 2},
    ]
    
    result = validate_capital_structure(tranches, expected_total_debt=150.0)
    
    assert result.valid is True


def test_validate_capital_structure_missing_name():
    """Test capital structure validation with missing tranche name."""
    tranches = [
        {"claim": 100.0, "tier": 1},  # Missing name
    ]
    
    result = validate_capital_structure(tranches)
    
    assert result.valid is False
    assert any(e.code == "MISSING_TRANCHE_NAME" for e in result.errors)


def test_validate_capital_structure_missing_claim():
    """Test capital structure validation with missing claim."""
    tranches = [
        {"name": "Senior", "tier": 1},  # Missing claim
    ]
    
    result = validate_capital_structure(tranches)
    
    assert result.valid is False
    assert any(e.code == "MISSING_CLAIM" for e in result.errors)


def test_validate_capital_structure_negative_claim():
    """Test capital structure validation with negative claim."""
    tranches = [
        {"name": "Senior", "claim": -100.0, "tier": 1},
    ]
    
    result = validate_capital_structure(tranches)
    
    assert result.valid is False
    assert any(e.code == "NEGATIVE_CLAIM" for e in result.errors)


def test_validate_capital_structure_duplicate_names():
    """Test capital structure validation with duplicate tranche names."""
    tranches = [
        {"name": "Senior", "claim": 100.0, "tier": 1},
        {"name": "Senior", "claim": 50.0, "tier": 2},  # Duplicate name
    ]
    
    result = validate_capital_structure(tranches)
    
    # Duplicate names are warnings, not critical errors
    assert result.valid is True
    assert any(e.code == "DUPLICATE_TRANCHE_NAME" for e in result.errors)


def test_validate_capital_structure_total_debt_mismatch():
    """Test capital structure validation with total debt mismatch."""
    tranches = [
        {"name": "Senior", "claim": 100.0, "tier": 1},
        {"name": "Junior", "claim": 50.0, "tier": 2},
    ]
    
    result = validate_capital_structure(tranches, expected_total_debt=200.0)  # Should be 150.0
    
    # Total debt mismatch is a warning, not critical
    assert result.valid is True
    assert any(e.code == "TOTAL_DEBT_MISMATCH" for e in result.errors)


def test_validate_capital_structure_empty():
    """Test capital structure validation with no tranches."""
    result = validate_capital_structure([])
    
    assert result.valid is False
    assert any(e.code == "NO_TRANCHES" for e in result.errors)


def test_validate_ev_inputs_success():
    """Test EV validation with valid inputs."""
    result = validate_ev_inputs(
        ev=150.0,
        ebitda=15.0,
        ebitda_multiple=10.0,
        data_source="HARD_DATA"
    )
    
    assert result.valid is True
    assert result.data_quality_flags.get("ev") == "HARD_DATA"


def test_validate_ev_inputs_negative_ev():
    """Test EV validation with negative EV."""
    result = validate_ev_inputs(ev=-100.0)
    
    assert result.valid is False
    assert any(e.code == "INVALID_EV" for e in result.errors)


def test_validate_ev_inputs_unusual_multiple():
    """Test EV validation with unusual EBITDA multiple."""
    result = validate_ev_inputs(
        ev=300.0,
        ebitda=15.0,
        ebitda_multiple=20.0  # Unusually high
    )
    
    # Unusual multiple is a warning, not critical
    assert result.valid is True
    assert any(e.code == "UNUSUAL_EBITDA_MULTIPLE" for e in result.errors)


def test_validate_ev_inputs_calculation_mismatch():
    """Test EV validation when EV doesn't match EBITDA * multiple."""
    result = validate_ev_inputs(
        ev=200.0,  # Should be 150.0 (15 * 10)
        ebitda=15.0,
        ebitda_multiple=10.0
    )
    
    # Calculation mismatch is a warning
    assert result.valid is True
    assert any(e.code == "EV_CALCULATION_MISMATCH" for e in result.errors)


def test_validate_ev_inputs_inferred_data():
    """Test EV validation flags inferred data."""
    result = validate_ev_inputs(
        ev=150.0,
        ebitda=15.0,
        ebitda_multiple=10.0,
        data_source="INFERRED"
    )
    
    assert result.data_quality_flags.get("ev") == "INFERRED"
    assert result.data_quality_flags.get("ebitda") == "INFERRED"
    assert result.data_quality_flags.get("ebitda_multiple") == "INFERRED"


def test_validation_error_to_dict():
    """Test ValidationError serialization."""
    error = ValidationError(
        severity=ValidationError.SEVERITY_CRITICAL,
        code="TEST_ERROR",
        message="Test error message",
        field="test_field",
        actual_value=100.0,
        expected_value=150.0,
    )
    
    error_dict = error.to_dict()
    
    assert error_dict["severity"] == "CRITICAL"
    assert error_dict["code"] == "TEST_ERROR"
    assert error_dict["message"] == "Test error message"
    assert error_dict["field"] == "test_field"
    assert error_dict["actual_value"] == "100.0"
    assert error_dict["expected_value"] == "150.0"


def test_validation_result_to_dict():
    """Test ValidationResult serialization."""
    result = ValidationResult()
    result.add_error(ValidationError(
        severity=ValidationError.SEVERITY_CRITICAL,
        code="TEST_ERROR",
        message="Critical error",
    ))
    result.add_error(ValidationError(
        severity=ValidationError.SEVERITY_WARNING,
        code="TEST_WARNING",
        message="Warning message",
    ))
    result.flag_inferred_data("test_field", "INFERRED")
    
    result_dict = result.to_dict()
    
    assert result_dict["valid"] is False  # Critical error makes it invalid
    assert result_dict["critical_count"] == 1
    assert result_dict["warning_count"] == 1
    assert result_dict["info_count"] == 0
    assert "test_field" in result_dict["data_quality_flags"]


def test_graceful_degradation_report():
    """Test graceful degradation report generation."""
    result = ValidationResult()
    result.add_error(ValidationError(
        severity=ValidationError.SEVERITY_WARNING,
        code="TEST_WARNING",
        message="Test warning message",
    ))
    result.flag_inferred_data("ev", "INFERRED")
    
    report = graceful_degradation_report(result, "Test Component")
    
    assert "Test Component Validation Report" in report
    assert "STATUS: VALID" in report  # Only warnings, no critical errors
    assert "TEST_WARNING" in report
    assert "Data Quality:" in report
    assert "ev: INFERRED" in report
