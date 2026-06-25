"""Run the agent against all 15 sample requests and compare to expected outcomes."""

import asyncio
import json
from pathlib import Path

from agent import evaluate_purchase_request
from models import PurchaseRequest


async def main() -> None:
    requests_data = json.loads(
        Path("mock_data/requests.json").read_text(encoding="utf-8")
    )

    results = {"approve": 0, "deny": 0, "escalate": 0, "mismatch": 0}

    for req_data in requests_data:
        expected = req_data["expected_outcome"]
        request = PurchaseRequest(**{
            k: v for k, v in req_data.items()
            if k not in {"expected_outcome", "outcome_reason"}
        })
        result = await evaluate_purchase_request(request)
        decision = result.decision

        is_match = decision == expected or expected == "ambiguous"
        match = "PASS" if is_match else "FAIL"
        results[decision] += 1
        if not is_match:
            results["mismatch"] += 1

        print(f"{match} {req_data['request_id']}: expected={expected}, got={decision}")
        print(f"  Rationale: {result.rationale[:80]}...")
        print()

    print(
        f"\nSummary: approve={results['approve']} deny={results['deny']} "
        f"escalate={results['escalate']} mismatches={results['mismatch']}"
    )


asyncio.run(main())
