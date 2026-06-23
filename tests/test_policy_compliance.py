"""Tests for policy compliance tool."""

from models import PurchaseRequest
from tools.policy_compliance import check_policy_compliance


def test_check_policy_compliance_pol_006_escalation() -> None:
    """Compliance-flagged vendor should emit POL-006 with escalate decision."""
    request = PurchaseRequest(
        request_id="REQ-011",
        requestor="F. Osei",
        cost_center_id="CC-001",
        vendor_name="Vertex Consulting Group",
        vendor_id="V-006",
        category="professional_services",
        item_description="Change management consulting for ERP migration (Phase 2)",
        quantity=1,
        unit_price=35_000.0,
        total_amount=35_000.0,
    )

    result = check_policy_compliance(request)
    assert "error" not in result

    pol_006 = [entry for entry in result["violations"] if entry["policy_id"] == "POL-006"]
    assert len(pol_006) == 1
    assert pol_006[0]["forced_decision"] == "escalate"


def test_check_policy_compliance_clean_request_no_violations() -> None:
    """A compliant request should return an empty violations list."""
    request = PurchaseRequest(
        request_id="REQ-001",
        requestor="M. Okonkwo",
        cost_center_id="CC-001",
        vendor_name="BlueSky Cloud Solutions",
        vendor_id="V-002",
        category="software_licenses",
        item_description="Annual renewal of enterprise cloud storage licenses (500 seats)",
        quantity=500,
        unit_price=48.0,
        total_amount=24_000.0,
    )

    result = check_policy_compliance(request)
    assert "error" not in result
    assert result["violation_count"] == 0
    assert result["violations"] == []


def test_check_policy_compliance_pol_004_catering_prohibition() -> None:
    """Catering requests should include a POL-004 deny violation."""
    request = PurchaseRequest(
        request_id="REQ-009",
        requestor="P. Harrington",
        cost_center_id="CC-005",
        vendor_name="Summit Catering Co.",
        vendor_id="V-017",
        category="catering",
        item_description="Executive leadership offsite lunch service",
        quantity=1,
        unit_price=3_200.0,
        total_amount=3_200.0,
    )

    result = check_policy_compliance(request)
    assert "error" not in result
    pol_004 = [entry for entry in result["violations"] if entry["policy_id"] == "POL-004"]
    assert len(pol_004) == 1
    assert pol_004[0]["forced_decision"] == "deny"


def test_check_policy_compliance_pol_002_range_is_checked() -> None:
    """Requests in the manager-threshold range should still evaluate POL-002."""
    request = PurchaseRequest(
        request_id="REQ-002",
        requestor="T. Beaumont",
        cost_center_id="CC-004",
        vendor_name="Pinnacle Hardware",
        vendor_id="V-005",
        category="hardware",
        item_description="Network switches for data center refresh",
        quantity=12,
        unit_price=3_200.0,
        total_amount=38_400.0,
    )

    result = check_policy_compliance(request)
    assert "error" not in result
    assert "POL-002" in result["checked_policy_ids"]


def test_check_policy_compliance_pol_005_expired_contract_denied() -> None:
    """Expired-contract vendor requests should include a POL-005 deny violation."""
    request = PurchaseRequest(
        request_id="REQ-007",
        requestor="C. Johnson",
        cost_center_id="CC-010",
        vendor_name="Crestview Print and Media",
        vendor_id="V-010",
        category="marketing_materials",
        item_description="Q1 campaign print collateral",
        quantity=1,
        unit_price=5_400.0,
        total_amount=5_400.0,
    )

    result = check_policy_compliance(request)
    assert "error" not in result
    pol_005 = [entry for entry in result["violations"] if entry["policy_id"] == "POL-005"]
    assert len(pol_005) == 1
    assert pol_005[0]["forced_decision"] == "deny"
