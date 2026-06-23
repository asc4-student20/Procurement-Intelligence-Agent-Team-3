"""Tests for vendor duplication tool."""

from tools.vendor_duplication import check_vendor_duplication


def test_check_vendor_duplication_req_008_conflicts() -> None:
    """REQ-008: NovaPrint office_supplies $28,500 should conflict with V-001 and V-003."""
    result = check_vendor_duplication(
        vendor_id="V-012",
        category="office_supplies",
        total_amount=28_500.0,
    )

    assert result["triggered"] is True
    assert result["contracted_category"] is True
    assert result["threshold_amount"] == 25_000.0
    assert set(result["conflicting_vendor_ids"]) == {"V-001", "V-003"}
    assert "error" not in result
