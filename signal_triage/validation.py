"""
Validation Layer for Signal Triage — Sanity Checks & Data Integrity.

Institutional Restructuring Desk: Every waterfall, capital structure, and recovery
analysis must pass validation before being presented to senior partners. This module
implements critical sanity checks to ensure data integrity and flag inferred assumptions.

Validation Rules:
1. Total Recovery cannot exceed Enterprise Value
2. Capital Structure must sum correctly (no double counting)
3. Recovery percentages must be in [0, 100] range
4. Fulcrum security must be properly identified
5. APR violations are flagged
6. Missing data is explicitly marked as "INFERRED"

Usage:
    from signal_triage.validation import validate_waterfall, validate_capital_structure
    
    validation_result = validate_waterfall(waterfall_result, ev)
    if not validation_result["valid"]:
        print(validation_result["errors"])
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

QUANT = Decimal("0.01")


def _to_decimal(x: float | int | Decimal | None) -> Decimal:
    """Convert numeric value to Decimal for exact arithmetic."""
    if x is None:
        return Decimal("0")
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))


class ValidationError:
    """Structured validation error with severity levels."""
    
    SEVERITY_CRITICAL = "CRITICAL"  # Blocks analysis
    SEVERITY_WARNING = "WARNING"    # Flags concern but allows analysis
    SEVERITY_INFO = "INFO"          # Informational notice
    
    def __init__(
        self,
        severity: str,
        code: str,
        message: str,
        field: Optional[str] = None,
        actual_value: Any = None,
        expected_value: Any = None,
    ):
        self.severity = severity
        self.code = code
        self.message = message
        self.field = field
        self.actual_value = actual_value
        self.expected_value = expected_value
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "field": self.field,
            "actual_value": str(self.actual_value) if self.actual_value is not None else None,
            "expected_value": str(self.expected_value) if self.expected_value is not None else None,
        }
    
    def __repr__(self) -> str:
        return f"[{self.severity}] {self.code}: {self.message}"


class ValidationResult:
    """Result of validation with errors, warnings, and data quality flags."""
    
    def __init__(self):
        self.errors: list[ValidationError] = []
        self.data_quality_flags: dict[str, str] = {}  # field -> "INFERRED" | "HARD_DATA"
        self.valid = True
    
    def add_error(self, error: ValidationError) -> None:
        """Add validation error."""
        self.errors.append(error)
        if error.severity == ValidationError.SEVERITY_CRITICAL:
            self.valid = False
    
    def flag_inferred_data(self, field: str, source: str = "INFERRED") -> None:
        """Mark field as inferred vs hard data."""
        self.data_quality_flags[field] = source
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "valid": self.valid,
            "errors": [e.to_dict() for e in self.errors],
            "data_quality_flags": self.data_quality_flags,
            "critical_count": sum(1 for e in self.errors if e.severity == ValidationError.SEVERITY_CRITICAL),
            "warning_count": sum(1 for e in self.errors if e.severity == ValidationError.SEVERITY_WARNING),
            "info_count": sum(1 for e in self.errors if e.severity == ValidationError.SEVERITY_INFO),
        }
    
    def __repr__(self) -> str:
        status = "VALID" if self.valid else "INVALID"
        error_summary = f"{len([e for e in self.errors if e.severity == ValidationError.SEVERITY_CRITICAL])} critical, " \
                       f"{len([e for e in self.errors if e.severity == ValidationError.SEVERITY_WARNING])} warnings"
        return f"ValidationResult(status={status}, {error_summary})"


def validate_waterfall(
    waterfall_result: dict[str, Any],
    ev: float | Decimal,
    tranches: Optional[list[dict[str, Any]]] = None,
) -> ValidationResult:
    """
    Validate waterfall analysis results for data integrity and sanity.
    
    Checks:
    1. Total recovery does not exceed EV
    2. Recovery percentages are in [0, 100] range
    3. EV accounting: ev_used + ev_remaining == ev
    4. Fulcrum security is properly identified
    5. APR violations are detected
    6. Each tranche recovery is <= claim
    
    Args:
        waterfall_result: Output from recovery_engine.run_waterfall()
        ev: Enterprise value used in waterfall
        tranches: Optional original tranches for cross-validation
    
    Returns:
        ValidationResult with errors, warnings, and data quality flags
    """
    result = ValidationResult()
    ev_d = _to_decimal(ev)
    
    # Extract waterfall components
    recoveries = waterfall_result.get("recoveries", [])
    ev_used = _to_decimal(waterfall_result.get("ev_used", 0))
    ev_remaining = _to_decimal(waterfall_result.get("ev_remaining", 0))
    fulcrum = waterfall_result.get("fulcrum_security")
    apr_violations = waterfall_result.get("apr_violations", [])
    
    # Check 1: EV accounting (ev_used + ev_remaining should equal ev)
    ev_total = ev_used + ev_remaining
    if abs(ev_total - ev_d) > Decimal("0.01"):  # Allow 1 cent rounding
        result.add_error(ValidationError(
            severity=ValidationError.SEVERITY_CRITICAL,
            code="EV_ACCOUNTING_MISMATCH",
            message=f"EV accounting error: ev_used ({ev_used}) + ev_remaining ({ev_remaining}) = {ev_total} != ev ({ev_d})",
            field="ev_accounting",
            actual_value=ev_total,
            expected_value=ev_d,
        ))
    
    # Check 2: Total recovery does not exceed EV
    total_recovered = sum(_to_decimal(r.get("recovered", 0)) for r in recoveries)
    if total_recovered > ev_d + Decimal("0.01"):  # Allow 1 cent rounding
        result.add_error(ValidationError(
            severity=ValidationError.SEVERITY_CRITICAL,
            code="RECOVERY_EXCEEDS_EV",
            message=f"Total recovery ({total_recovered}) exceeds enterprise value ({ev_d})",
            field="total_recovery",
            actual_value=total_recovered,
            expected_value=ev_d,
        ))
    
    # Check 3: Validate each tranche recovery
    for i, rec in enumerate(recoveries):
        tranche_name = rec.get("name", f"Tranche {i+1}")
        claim = _to_decimal(rec.get("claim", 0))
        recovered = _to_decimal(rec.get("recovered", 0))
        recovery_pct = _to_decimal(rec.get("recovery_pct", 0))
        
        # Recovery cannot exceed claim
        if recovered > claim + Decimal("0.01"):
            result.add_error(ValidationError(
                severity=ValidationError.SEVERITY_CRITICAL,
                code="RECOVERY_EXCEEDS_CLAIM",
                message=f"{tranche_name}: Recovery ({recovered}) exceeds claim ({claim})",
                field=f"tranches[{i}].recovered",
                actual_value=recovered,
                expected_value=claim,
            ))
        
        # Recovery percentage must be in [0, 100]
        if recovery_pct < 0 or recovery_pct > Decimal("100.01"):
            result.add_error(ValidationError(
                severity=ValidationError.SEVERITY_CRITICAL,
                code="INVALID_RECOVERY_PCT",
                message=f"{tranche_name}: Recovery percentage ({recovery_pct}%) out of valid range [0, 100]",
                field=f"tranches[{i}].recovery_pct",
                actual_value=recovery_pct,
            ))
        
        # Check recovery percentage calculation
        if claim > 0:
            expected_pct = (recovered / claim * Decimal("100")).quantize(QUANT, rounding=ROUND_HALF_UP)
            if abs(recovery_pct - expected_pct) > Decimal("0.1"):
                result.add_error(ValidationError(
                    severity=ValidationError.SEVERITY_WARNING,
                    code="RECOVERY_PCT_MISMATCH",
                    message=f"{tranche_name}: Recovery percentage ({recovery_pct}%) does not match calculated value ({expected_pct}%)",
                    field=f"tranches[{i}].recovery_pct",
                    actual_value=recovery_pct,
                    expected_value=expected_pct,
                ))
    
    # Check 4: Fulcrum security validation
    if not fulcrum:
        result.add_error(ValidationError(
            severity=ValidationError.SEVERITY_WARNING,
            code="FULCRUM_NOT_IDENTIFIED",
            message="Fulcrum security not identified; all tranches may be par or zero recovery",
            field="fulcrum_security",
        ))
    else:
        # Verify fulcrum is a valid tranche name
        tranche_names = [r.get("name", "") for r in recoveries]
        if fulcrum not in tranche_names:
            result.add_error(ValidationError(
                severity=ValidationError.SEVERITY_WARNING,
                code="INVALID_FULCRUM",
                message=f"Fulcrum security '{fulcrum}' not found in tranches list",
                field="fulcrum_security",
                actual_value=fulcrum,
            ))
    
    # Check 5: APR violations
    if apr_violations:
        for violation in apr_violations:
            result.add_error(ValidationError(
                severity=ValidationError.SEVERITY_WARNING,
                code="APR_VIOLATION",
                message=f"Absolute Priority Rule violation: {violation.get('note', 'APR violation detected')}",
                field="apr_violations",
            ))
    
    # Check 6: Cross-validate with input tranches if provided
    if tranches:
        if len(recoveries) != len(tranches):
            result.add_error(ValidationError(
                severity=ValidationError.SEVERITY_WARNING,
                code="TRANCHE_COUNT_MISMATCH",
                message=f"Number of recoveries ({len(recoveries)}) does not match input tranches ({len(tranches)})",
                field="tranches",
            ))
        
        # Validate claims match
        for i, (rec, tranche) in enumerate(zip(recoveries, tranches)):
            rec_claim = _to_decimal(rec.get("claim", 0))
            input_claim = _to_decimal(tranche.get("claim", 0))
            if abs(rec_claim - input_claim) > Decimal("0.01"):
                result.add_error(ValidationError(
                    severity=ValidationError.SEVERITY_WARNING,
                    code="CLAIM_MISMATCH",
                    message=f"Tranche {i}: Claim in recovery ({rec_claim}) does not match input ({input_claim})",
                    field=f"tranches[{i}].claim",
                    actual_value=rec_claim,
                    expected_value=input_claim,
                ))
    
    return result


def validate_capital_structure(
    tranches: list[dict[str, Any]],
    expected_total_debt: Optional[float | Decimal] = None,
) -> ValidationResult:
    """
    Validate capital structure for integrity and completeness.
    
    Checks:
    1. All tranches have required fields (name, claim)
    2. Claims are non-negative
    3. Priority/tier is consistent (no gaps, duplicates)
    4. Total debt matches expected (if provided)
    5. No duplicate tranche names
    
    Args:
        tranches: List of tranches with name, claim, optional tier/priority
        expected_total_debt: Optional expected total debt for validation
    
    Returns:
        ValidationResult with errors and data quality flags
    """
    result = ValidationResult()
    
    if not tranches:
        result.add_error(ValidationError(
            severity=ValidationError.SEVERITY_CRITICAL,
            code="NO_TRANCHES",
            message="Capital structure contains no tranches",
            field="tranches",
        ))
        return result
    
    total_claims = Decimal("0")
    tranche_names = set()
    tiers = []
    
    for i, tranche in enumerate(tranches):
        name = tranche.get("name")
        claim = tranche.get("claim")
        tier = tranche.get("tier") or tranche.get("priority")
        
        # Check required fields
        if not name:
            result.add_error(ValidationError(
                severity=ValidationError.SEVERITY_CRITICAL,
                code="MISSING_TRANCHE_NAME",
                message=f"Tranche {i}: Missing required field 'name'",
                field=f"tranches[{i}].name",
            ))
        else:
            # Check for duplicate names
            if name in tranche_names:
                result.add_error(ValidationError(
                    severity=ValidationError.SEVERITY_WARNING,
                    code="DUPLICATE_TRANCHE_NAME",
                    message=f"Duplicate tranche name: '{name}'",
                    field=f"tranches[{i}].name",
                ))
            tranche_names.add(name)
        
        if claim is None:
            result.add_error(ValidationError(
                severity=ValidationError.SEVERITY_CRITICAL,
                code="MISSING_CLAIM",
                message=f"Tranche '{name}': Missing required field 'claim'",
                field=f"tranches[{i}].claim",
            ))
        else:
            claim_d = _to_decimal(claim)
            if claim_d < 0:
                result.add_error(ValidationError(
                    severity=ValidationError.SEVERITY_CRITICAL,
                    code="NEGATIVE_CLAIM",
                    message=f"Tranche '{name}': Claim cannot be negative ({claim_d})",
                    field=f"tranches[{i}].claim",
                    actual_value=claim_d,
                ))
            total_claims += claim_d
        
        if tier is not None:
            tiers.append((tier, name))
    
    # Check total debt
    if expected_total_debt is not None:
        expected_d = _to_decimal(expected_total_debt)
        if abs(total_claims - expected_d) > Decimal("0.01"):
            result.add_error(ValidationError(
                severity=ValidationError.SEVERITY_WARNING,
                code="TOTAL_DEBT_MISMATCH",
                message=f"Total claims ({total_claims}) do not match expected total debt ({expected_d})",
                field="total_claims",
                actual_value=total_claims,
                expected_value=expected_d,
            ))
    
    # Check tier consistency (if tiers are used)
    if tiers:
        tier_values = sorted(set(t[0] for t in tiers))
        # Check for gaps in tier numbering (optional warning)
        if tier_values and tier_values[-1] - tier_values[0] + 1 > len(tier_values):
            result.add_error(ValidationError(
                severity=ValidationError.SEVERITY_INFO,
                code="TIER_GAPS",
                message=f"Priority tiers have gaps: {tier_values}",
                field="tiers",
            ))
    
    return result


def validate_ev_inputs(
    ev: float | Decimal,
    ebitda: Optional[float | Decimal] = None,
    ebitda_multiple: Optional[float | Decimal] = None,
    data_source: str = "INFERRED",
) -> ValidationResult:
    """
    Validate enterprise value and related inputs.
    
    Checks:
    1. EV is positive
    2. If EBITDA and multiple provided, verify EV = EBITDA * multiple
    3. Flag if data is inferred vs hard data
    4. Sanity check on EBITDA multiple range (typically 3-15x for distressed)
    
    Args:
        ev: Enterprise value
        ebitda: Optional EBITDA
        ebitda_multiple: Optional EBITDA multiple
        data_source: "HARD_DATA" | "INFERRED" | "ESTIMATED"
    
    Returns:
        ValidationResult with errors and data quality flags
    """
    result = ValidationResult()
    ev_d = _to_decimal(ev)
    
    # Check EV is positive
    if ev_d <= 0:
        result.add_error(ValidationError(
            severity=ValidationError.SEVERITY_CRITICAL,
            code="INVALID_EV",
            message=f"Enterprise value must be positive (got {ev_d})",
            field="ev",
            actual_value=ev_d,
        ))
    
    # Flag data quality
    result.flag_inferred_data("ev", data_source)
    
    # If EBITDA and multiple provided, cross-validate
    if ebitda is not None and ebitda_multiple is not None:
        ebitda_d = _to_decimal(ebitda)
        multiple_d = _to_decimal(ebitda_multiple)
        
        result.flag_inferred_data("ebitda", data_source)
        result.flag_inferred_data("ebitda_multiple", data_source)
        
        # Sanity check on multiple (3x-15x typical for distressed)
        if multiple_d < Decimal("2") or multiple_d > Decimal("20"):
            result.add_error(ValidationError(
                severity=ValidationError.SEVERITY_WARNING,
                code="UNUSUAL_EBITDA_MULTIPLE",
                message=f"EBITDA multiple ({multiple_d}x) outside typical distressed range [3x, 15x]",
                field="ebitda_multiple",
                actual_value=multiple_d,
            ))
        
        # Verify EV = EBITDA * multiple
        if ebitda_d > 0:
            calculated_ev = ebitda_d * multiple_d
            if abs(calculated_ev - ev_d) > Decimal("0.01"):
                result.add_error(ValidationError(
                    severity=ValidationError.SEVERITY_WARNING,
                    code="EV_CALCULATION_MISMATCH",
                    message=f"EV ({ev_d}) does not match EBITDA ({ebitda_d}) * multiple ({multiple_d}) = {calculated_ev}",
                    field="ev",
                    actual_value=ev_d,
                    expected_value=calculated_ev,
                ))
    
    return result


def graceful_degradation_report(
    validation_result: ValidationResult,
    component: str = "Analysis",
) -> str:
    """
    Generate a human-readable report for graceful degradation when data is missing/inferred.
    
    Args:
        validation_result: ValidationResult from validation functions
        component: Name of component being validated (e.g., "Waterfall", "Capital Structure")
    
    Returns:
        Formatted report string for display in UI
    """
    lines = [f"--- {component} Validation Report ---"]
    
    if validation_result.valid:
        lines.append("STATUS: VALID (all critical checks passed)")
    else:
        lines.append("STATUS: INVALID (critical errors detected)")
    
    # Summary
    result_dict = validation_result.to_dict()
    lines.append(
        f"Errors: {result_dict['critical_count']} critical, "
        f"{result_dict['warning_count']} warnings, "
        f"{result_dict['info_count']} info"
    )
    
    # Data quality flags
    if validation_result.data_quality_flags:
        lines.append("\nData Quality:")
        for field, source in validation_result.data_quality_flags.items():
            lines.append(f"  - {field}: {source}")
    
    # Errors
    if validation_result.errors:
        lines.append("\nIssues:")
        for error in validation_result.errors:
            lines.append(f"  [{error.severity}] {error.code}: {error.message}")
    
    lines.append("--- End Report ---")
    return "\n".join(lines)
