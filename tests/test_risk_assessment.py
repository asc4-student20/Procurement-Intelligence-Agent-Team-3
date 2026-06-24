"""Tests for risk-assessment tool."""

from tools import risk_assessment
from tools.risk_assessment import assess_risk


def test_assess_risk_compliance_flag_critical() -> None:
    """Compliance-flagged vendor should return critical risk."""
    result = assess_risk("V-006")
    assert result["risk_level"] == "critical"
    assert result["compliance_flag"] is True
    assert "error" not in result


def test_assess_risk_expired_contract_high() -> None:
    """Expired-contract vendor should return high risk."""
    result = assess_risk("V-010")
    assert result["risk_level"] == "high"
    assert result["contract_status"] == "expired"
    assert "error" not in result


def test_assess_risk_no_contract_medium() -> None:
    """Vendor with no contract should return medium risk."""
    result = assess_risk("V-004")
    assert result["risk_level"] == "medium"
    assert result["contract_status"] == "none"
    assert "error" not in result


def test_assess_risk_active_contract_low() -> None:
    """Active-contract vendor without compliance issue should return low risk."""
    result = assess_risk("V-001")
    assert result["risk_level"] == "low"
    assert result["contract_status"] == "active"
    assert result["compliance_flag"] is False
    assert "error" not in result


def test_assess_risk_unknown_vendor_fallback() -> None:
    """Unknown vendor should return deterministic fallback error payload."""
    result = assess_risk("V-999")
    assert result["risk_level"] in {"high", "critical"}
    assert result["error"]["code"] == "vendor_not_found"
    assert result["error"]["vendor_id"] == "V-999"
    assert "fallback" in result["risk_summary"].lower()


def test_assess_risk_data_unavailable_fallback(monkeypatch) -> None:
    """Loader failures should return deterministic vendor_data_unavailable fallback."""

    def _raise_load_error() -> list[dict[str, object]]:
        raise RuntimeError("simulated loader outage")

    monkeypatch.setattr(risk_assessment.loader, "load_vendors", _raise_load_error)
    result = assess_risk("V-001")

    assert result["risk_level"] in {"high", "critical"}
    assert result["error"]["code"] == "vendor_data_unavailable"
    assert result["error"]["vendor_id"] == "V-001"
    assert "escalate" in result["risk_summary"].lower()
