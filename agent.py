"""Procurement pre-screening agent orchestration and recommendation synthesis."""

from __future__ import annotations

import os
import re
from typing import Any, Callable, Literal

from dotenv import load_dotenv
from pydantic_ai import Agent

from models import ProcurementRecommendation, PurchaseRequest
from tools.budget import check_budget
from tools.policy_compliance import check_policy_compliance
from tools.risk_assessment import assess_risk
from tools.vendor_duplication import check_vendor_duplication

Decision = Literal["approve", "deny", "escalate"]
DIRECTOR_APPROVAL_THRESHOLD = 50_000.0
NEAR_THRESHOLD_PERCENT = 0.05
TIGHT_BUDGET_THRESHOLD_PERCENT = 0.20

SYSTEM_PROMPT = """
You are a procurement pre-screening assistant.

You must follow these constraints:
- Use only the provided request and tool evidence.
- Do not invent facts.
- Return output that conforms to ProcurementRecommendation.
- Decision must be exactly one of: approve, deny, escalate.
- Rationale must be non-empty and concise.
- Final decision priority is mandatory: escalate > deny > approve.
- If any tool returns an escalate signal, the final decision is always escalate.
- If any tool returns an error payload, explicitly reference the error in rationale and escalate.
- If the request amount is within 5% of the director approval threshold, escalate.
- If remaining budget after purchase is below 20% of the quarterly budget, escalate and flag low remaining budget.
- If evidence has errors or uncertainty, escalation takes precedence.
- Keep request_id unchanged from the provided input.
- Return a confidence score between 0.0 and 1.0 inclusive.
- Confidence scoring rubric:
    - 1.0: only one check fired and its outcome is unambiguous (for example, sole catering prohibition).
    - 0.8-0.9: two or more checks fired and all agree.
    - 0.5-0.7: checks fired but at least one is borderline (near a threshold).
    - Below 0.5: the decision is not clear; escalate.

Rationale template requirements (mandatory):
- The rationale must be 2 to 4 complete sentences.
- The rationale must name the specific check(s) that drove the decision
    (budget check, vendor duplication check, policy compliance check, risk assessment check).
- The rationale must include relevant context such as amounts, vendor names, and/or policy IDs.
- Do not use bullet points.
""".strip()


def _count_fired_checks(
    budget_result: dict[str, Any],
    duplication_result: dict[str, Any],
    policy_result: dict[str, Any],
    risk_result: dict[str, Any],
) -> int:
    """Count how many check categories emitted a non-trivial finding."""
    fired = 0

    if budget_result.get("error") or not bool(budget_result.get("within_budget", True)):
        fired += 1
    if duplication_result.get("error") or bool(duplication_result.get("triggered", False)):
        fired += 1
    if policy_result.get("error") or bool(policy_result.get("violations", [])):
        fired += 1

    risk_error = risk_result.get("error")
    risk_level = str(risk_result.get("risk_level", "")).strip().lower()
    if risk_error or risk_level in {"high", "critical"}:
        fired += 1

    return fired


def _compute_confidence(
    budget_result: dict[str, Any],
    duplication_result: dict[str, Any],
    policy_result: dict[str, Any],
    risk_result: dict[str, Any],
    escalate_signals: list[str],
    deny_signals: list[str],
) -> float:
    """Compute deterministic confidence score from evidence patterns."""
    signal_text = " ".join(escalate_signals + deny_signals).lower()
    has_error = "error" in signal_text
    has_conflict = bool(escalate_signals) and bool(deny_signals)
    has_borderline = (
        "within 5% of the director approval threshold" in signal_text
        or "low remaining budget after purchase" in signal_text
    )

    if has_error or has_conflict:
        return 0.4

    if has_borderline:
        return 0.6

    fired_checks = _count_fired_checks(
        budget_result,
        duplication_result,
        policy_result,
        risk_result,
    )

    if fired_checks == 1:
        return 1.0
    if fired_checks >= 2:
        return 0.85
    return 0.85


def _load_env() -> None:
    """Load environment variables and align key names for model providers."""
    load_dotenv()

    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    if openai_key and not os.getenv("OPENAI_API_KEY"):
        # Project requirement requests OPENAI_API_KEY via dotenv; map it so
        # Anthropic transport can still authenticate in this environment.
        os.environ["OPENAI_API_KEY"] = openai_key


_load_env()

procurement_agent = Agent(
    "openai:gpt-4o-mini",
    output_type=ProcurementRecommendation,
    system_prompt=SYSTEM_PROMPT,
)


@procurement_agent.tool_plain
def budget_check_tool(cost_center_id: str, requested_amount: float) -> dict[str, Any]:
    """Run budget availability evaluation for a request amount and cost center."""
    return check_budget(cost_center_id=cost_center_id, requested_amount=requested_amount)


@procurement_agent.tool_plain
def vendor_duplication_tool(
    vendor_id: str,
    category: str,
    total_amount: float,
) -> dict[str, Any]:
    """Run POL-001 single-source conflict detection for the selected vendor."""
    return check_vendor_duplication(
        vendor_id=vendor_id,
        category=category,
        total_amount=total_amount,
    )


@procurement_agent.tool_plain
def policy_compliance_tool(request: PurchaseRequest) -> dict[str, Any]:
    """Run policy checks and return any deny/escalate policy violations."""
    return check_policy_compliance(request=request)


@procurement_agent.tool_plain
def risk_assessment_tool(vendor_id: str) -> dict[str, Any]:
    """Run vendor risk assessment for compliance and contract exposure."""
    return assess_risk(vendor_id=vendor_id)


def _safe_tool_call(
    tool_name: str,
    func: Callable[..., dict[str, Any]],
    *args: Any,
    **kwargs: Any,
) -> dict[str, Any]:
    """Call a tool and convert unexpected exceptions into structured errors."""
    try:
        result = func(*args, **kwargs)
    except Exception as exc:  # pragma: no cover - defensive fallback
        return {
            "error": f"{tool_name} failed with exception: {exc}",
            "tool": tool_name,
        }

    if "error" in result and result.get("error"):
        result["tool"] = tool_name
    return result


def _error_message(error_value: Any) -> str:
    """Normalize error payloads into a single message string for rationale synthesis."""
    if isinstance(error_value, dict):
        error_type = str(error_value.get("type", "error")).strip()
        message = str(error_value.get("message", "")).strip()
        stage = str(error_value.get("stage", "")).strip()
        pieces = [piece for piece in [error_type, stage, message] if piece]
        return " | ".join(pieces) if pieces else "unknown tool error"
    return str(error_value)


def _extract_policy_ids(text: str) -> list[str]:
    """Extract normalized policy IDs from free-form signal text."""
    return sorted(set(re.findall(r"POL-\d{3}", text)))


def _build_template_rationale(
    request: PurchaseRequest,
    decision: Decision,
    budget_result: dict[str, Any],
    duplication_result: dict[str, Any],
    policy_result: dict[str, Any],
    risk_result: dict[str, Any],
    escalate_signals: list[str],
    deny_signals: list[str],
) -> str:
    """Build a deterministic rationale that satisfies the project template."""
    driving_checks: list[str] = []

    if budget_result.get("error") or not bool(budget_result.get("within_budget", True)):
        driving_checks.append("budget check")
    if duplication_result.get("error") or bool(duplication_result.get("triggered", False)):
        driving_checks.append("vendor duplication check")
    if policy_result.get("error") or bool(policy_result.get("violations", [])):
        driving_checks.append("policy compliance check")

    risk_error = risk_result.get("error")
    risk_level = str(risk_result.get("risk_level", "")).strip().lower()
    if risk_error or risk_level in {"high", "critical"}:
        driving_checks.append("risk assessment check")

    if not driving_checks:
        driving_checks = [
            "budget check",
            "vendor duplication check",
            "policy compliance check",
            "risk assessment check",
        ]

    unique_checks = ", ".join(dict.fromkeys(driving_checks))

    signal_text = " ".join(escalate_signals + deny_signals)
    policy_ids = _extract_policy_ids(signal_text)
    policy_id_text = ", ".join(policy_ids) if policy_ids else "no policy ID"

    amount_text = f"${request.total_amount:,.2f}"
    vendor_text = request.vendor_name
    risk_text = risk_level if risk_level else "unknown"

    sentence_1 = (
        f"The {decision} recommendation is driven by the {unique_checks}."
    )
    sentence_2 = (
        f"The request for {vendor_text} totals {amount_text}, with policy context {policy_id_text}."
    )

    error_signals = [signal for signal in escalate_signals if "error" in signal.lower()]
    sentence_4 = ""
    tight_budget_signal = next(
        (
            signal
            for signal in escalate_signals
            if "low remaining budget after purchase" in signal.lower()
        ),
        "",
    )

    if decision == "approve":
        sentence_3 = (
            f"These checks did not produce escalation or denial triggers requiring a different outcome, "
            f"and the current risk assessment level is {risk_text}."
        )
    elif decision == "deny":
        sentence_3 = (
            f"The evidence supports denial because blocking conditions from the named checks remain unresolved, "
            "and procurement should require a corrected request before approval."
        )
    else:
        if tight_budget_signal:
            sentence_3 = (
                "The evidence supports escalation because post-purchase remaining budget falls below 20% "
                "of the quarterly allocation and needs finance review."
            )
            sentence_4 = tight_budget_signal
        else:
            sentence_3 = (
                "The evidence supports escalation because higher-risk or error conditions were detected and "
                "must be reviewed by a human procurement officer."
            )
            sentence_4 = ""

    sentences = [sentence_1, sentence_2, sentence_3]
    if sentence_4:
        sentences.append(sentence_4)
    if error_signals:
        sentences.append(f"Error context: {error_signals[0]}.")

    return " ".join(sentences).strip()


def _rationale_meets_template(rationale: str, request: PurchaseRequest) -> bool:
    """Validate rationale against required template constraints."""
    text = rationale.strip()
    if not text:
        return False

    if "\n-" in text or "\n*" in text or "•" in text:
        return False

    sentences = [
        segment.strip()
        for segment in re.split(r"(?<=[.!?])\s+", text)
        if segment.strip()
    ]
    if len(sentences) < 2 or len(sentences) > 4:
        return False

    lowered = text.lower()
    check_terms = [
        "budget check",
        "vendor duplication check",
        "policy compliance check",
        "risk assessment check",
    ]
    if not any(term in lowered for term in check_terms):
        return False

    has_amount = bool(re.search(r"\$\s?\d", text))
    has_vendor = request.vendor_name.lower() in lowered
    has_policy_id = bool(re.search(r"POL-\d{3}", text))
    if not (has_amount or has_vendor or has_policy_id):
        return False

    return True


def _derive_decision_and_signals(
    request: PurchaseRequest,
    budget_result: dict[str, Any],
    duplication_result: dict[str, Any],
    policy_result: dict[str, Any],
    risk_result: dict[str, Any],
) -> tuple[Decision, list[str], list[str]]:
    """Compute deterministic decision using escalate > deny > approve precedence."""
    escalate_signals: list[str] = []
    deny_signals: list[str] = []

    if budget_result.get("error"):
        escalate_signals.append(
            f"Budget check error: {_error_message(budget_result['error'])}"
        )
    elif not bool(budget_result.get("within_budget", True)):
        overage = float(budget_result.get("overage", 0.0))
        deny_signals.append(f"Budget overage detected: ${overage:,.2f}.")

    if duplication_result.get("error"):
        escalate_signals.append(
            "Vendor duplication check error: "
            f"{_error_message(duplication_result['error'])}"
        )
    elif bool(duplication_result.get("triggered", False)):
        deny_signals.append(str(duplication_result.get("reason", "POL-001 trigger detected.")))

    if policy_result.get("error"):
        escalate_signals.append(
            f"Policy compliance error: {_error_message(policy_result['error'])}"
        )
    else:
        violations = policy_result.get("violations", [])
        for violation in violations:
            policy_id = str(violation.get("policy_id", "POL-UNKNOWN"))
            description = str(violation.get("rule_description", "Policy violation."))
            forced_decision = str(violation.get("forced_decision", "")).strip().lower()

            if forced_decision == "escalate":
                escalate_signals.append(f"{policy_id}: {description}")
            elif forced_decision == "deny":
                deny_signals.append(f"{policy_id}: {description}")

    risk_error = risk_result.get("error")
    if risk_error:
        error_message = _error_message(risk_error)
        escalate_signals.append(f"Risk assessment error: {error_message}")
    else:
        risk_level = str(risk_result.get("risk_level", "")).strip().lower()
        risk_summary = str(risk_result.get("risk_summary", "")).strip()

        if risk_level == "critical":
            signal = f"Risk level is {risk_level}."
            if risk_summary:
                signal = f"{signal} {risk_summary}"
            escalate_signals.append(signal)

    # Near-threshold requests are escalated for director visibility.
    near_threshold_floor = DIRECTOR_APPROVAL_THRESHOLD * (1.0 - NEAR_THRESHOLD_PERCENT)
    if near_threshold_floor <= request.total_amount < DIRECTOR_APPROVAL_THRESHOLD:
        escalate_signals.append(
            (
                "Request amount is within 5% of the director approval threshold "
                f"(${DIRECTOR_APPROVAL_THRESHOLD:,.2f}); escalate for director review."
            )
        )

    remaining_budget = float(budget_result.get("remaining_budget", 0.0))
    quarterly_budget = float(budget_result.get("quarterly_budget", 0.0))
    if (
        not budget_result.get("error")
        and bool(budget_result.get("within_budget", True))
        and not deny_signals
        and quarterly_budget > 0.0
    ):
        post_purchase_remaining = max(0.0, remaining_budget - request.total_amount)
        post_purchase_ratio = post_purchase_remaining / quarterly_budget
        if post_purchase_ratio < TIGHT_BUDGET_THRESHOLD_PERCENT:
            escalate_signals.append(
                (
                    "Low remaining budget after purchase: "
                    f"${post_purchase_remaining:,.2f} "
                    f"({post_purchase_ratio:.1%} of quarterly budget), below 20% threshold."
                )
            )

    if escalate_signals:
        decision: Decision = "escalate"
    elif deny_signals:
        decision = "deny"
    else:
        decision = "approve"

    if decision == "approve" and not deny_signals and not escalate_signals:
        deny_signals.append("All four checks completed without blocking findings.")

    return decision, escalate_signals, deny_signals


def _build_prompt(
    request: PurchaseRequest,
    decision: Decision,
    budget_result: dict[str, Any],
    duplication_result: dict[str, Any],
    policy_result: dict[str, Any],
    risk_result: dict[str, Any],
    escalate_signals: list[str],
    deny_signals: list[str],
) -> str:
    """Build evidence-grounded prompt for structured recommendation generation."""
    return (
        "Generate a ProcurementRecommendation JSON object using the evidence below.\n"
        f"request_id: {request.request_id}\n"
        f"precomputed_decision: {decision}\n"
        "You MUST keep decision equal to precomputed_decision.\n"
        "Do not override precomputed_decision; escalate always overrides deny and approve.\n"
        "Rationale must follow the template: 2 to 4 complete sentences, no bullet points, "
        "name specific checks that drove the decision, and include relevant amounts, vendor names, "
        "or policy IDs.\n\n"
        "Provide confidence as a float from 0.0 to 1.0 using the rubric in the system prompt.\n\n"
        f"budget_result: {budget_result}\n"
        f"duplication_result: {duplication_result}\n"
        f"policy_result: {policy_result}\n"
        f"risk_result: {risk_result}\n"
        f"escalate_signals: {escalate_signals}\n"
        f"deny_signals: {deny_signals}\n"
    )


async def evaluate_purchase_request(request: PurchaseRequest) -> ProcurementRecommendation:
    """Evaluate a purchase request and return a deterministic recommendation."""
    budget_result = _safe_tool_call(
        "check_budget",
        check_budget,
        request.cost_center_id,
        request.total_amount,
    )
    duplication_result = _safe_tool_call(
        "check_vendor_duplication",
        check_vendor_duplication,
        request.vendor_id,
        request.category,
        request.total_amount,
    )
    policy_result = _safe_tool_call(
        "check_policy_compliance",
        check_policy_compliance,
        request,
    )
    risk_result = _safe_tool_call(
        "assess_risk",
        assess_risk,
        request.vendor_id,
    )

    decision, escalate_signals, deny_signals = _derive_decision_and_signals(
        request,
        budget_result,
        duplication_result,
        policy_result,
        risk_result,
    )

    confidence = _compute_confidence(
        budget_result,
        duplication_result,
        policy_result,
        risk_result,
        escalate_signals,
        deny_signals,
    )

    if confidence < 0.5 and decision != "escalate":
        decision = "escalate"
        escalate_signals.append(
            "Confidence below 0.5 indicates unclear decision; escalate for human review."
        )

    prompt = _build_prompt(
        request,
        decision,
        budget_result,
        duplication_result,
        policy_result,
        risk_result,
        escalate_signals,
        deny_signals,
    )

    fallback_rationale = _build_template_rationale(
        request,
        decision,
        budget_result,
        duplication_result,
        policy_result,
        risk_result,
        escalate_signals,
        deny_signals,
    )

    try:
        llm_result = await procurement_agent.run(prompt)
        recommendation = llm_result.output
        recommendation.request_id = request.request_id
        recommendation.decision = decision
        recommendation.confidence = confidence

        tight_budget_triggered = any(
            "low remaining budget after purchase" in signal.lower()
            for signal in escalate_signals
        )

        if tight_budget_triggered and "remaining budget" not in recommendation.rationale.lower():
            recommendation.rationale = fallback_rationale
        elif not _rationale_meets_template(recommendation.rationale, request):
            recommendation.rationale = fallback_rationale
        return recommendation
    except Exception as exc:  # pragma: no cover - defensive fallback
        return ProcurementRecommendation(
            request_id=request.request_id,
            decision="escalate",
            rationale=(
                f"Agent generation failed: {exc}. "
                f"Returning safe escalation. {fallback_rationale}"
            ).strip(),
            confidence=0.4,
        )
