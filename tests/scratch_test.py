import asyncio
import os

# Allow agent import in test environments without real model credentials.
os.environ.setdefault("OPENAI_API_KEY", "test-key")

from agent import evaluate_purchase_request
from models import PurchaseRequest

# REQ-001: straightforward approve
req01 = PurchaseRequest(
    request_id="REQ-001",
    requestor="j.smith@fedex.com",
    cost_center_id="CC-001",
    vendor_name="BlueSky Cloud Solutions",
    vendor_id="V-002",
    category="software_licenses",
    item_description="Standard office paper and toner",
    quantity=1,
    unit_price=1250.00,
    total_amount=1250.00,
)
req02 = PurchaseRequest(
    request_id="REQ-009",
    requestor="j.smith@fedex.com",
    cost_center_id="CC-005",
    vendor_name="Summit Catering Co.",
    vendor_id="V-017",
    category="catering",
    item_description="Standard office paper and toner",
    quantity=1,
    unit_price=1250.00,
    total_amount=1250.00,
)
req03 = PurchaseRequest(
    request_id="REQ-011",
    requestor="F. Osei",
    cost_center_id="CC-001",
    vendor_name="Vertex Consulting Group",
    vendor_id="V-006",
    category="professional_services",
    item_description="Change management consulting for ERP migration (Phase 2)",
    quantity=1,
    unit_price=35000.00,
    total_amount=35000.00,
)
req04 = PurchaseRequest(
    request_id="REQ-014",
    requestor="J. McAllister",
    cost_center_id="CC-006",
    vendor_name="Orion Data Systems",
    vendor_id="V-016",
    category="hardware",
    item_description="Replacement server infrastructure for Memphis air hub (full rack)",
    quantity=1,
    unit_price=47500.00,
    total_amount=47500.00,
)

# escalate REQ-011 (Vertex Consulting, compliance flag): escalation driven by a risk tool finding
# req = PurchaseRequest(
#     request_id="REQ-011",
#     requestor="F. Osei",
#     cost_center_id="CC-001",
#     vendor_name="Vertex Consulting Group",
#     vendor_id="V-006",
#     category="professional_services",
#     item_description="Change management consulting for ERP migration (Phase 2)",
#     quantity=1,
#     unit_price=35000.00,
#     total_amount=35000.00,
# )

async def main():
    requests = [req01, req02, req03, req04]

    for req in requests:
        result = await evaluate_purchase_request(req)
        print(f"request_id: {result.request_id}")
        print(f"decision: {result.decision}")
        print(f"rationale: {result.rationale}")


if __name__ == "__main__":
    asyncio.run(main())