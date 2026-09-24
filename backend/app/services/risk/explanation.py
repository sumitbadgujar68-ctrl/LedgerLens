from typing import List
from uuid import UUID

from app.services.risk.engine import RiskEngine
from app.services.risk.models import RiskExplanation


async def generate_risk_explanation(
    db,
    case_id: UUID,
    trace_id: UUID,
    wallet_address: str,
) -> RiskExplanation:
    engine = RiskEngine(db)
    explanation = await engine.get_risk_explanation(case_id, trace_id, wallet_address)
    return explanation


def format_risk_summary(explanation: RiskExplanation) -> str:
    lines = [
        f"Risk Assessment for {explanation.wallet_address}",
        "=" * 50,
        f"Total Score: {explanation.total_score}/100",
        f"Risk Category: {explanation.risk_category.value.upper()}",
        f"Scoring Version: {explanation.scoring_version}",
        f"Calculated: {explanation.calculated_at.isoformat()}",
        "",
        "Factor Breakdown:",
    ]

    for i, factor in enumerate(explanation.factor_explanations, 1):
        lines.append(f"  {i}. {factor}")

    lines.extend([
        "",
        "Methodology:",
        "  This risk score is calculated using deterministic, explainable factors.",
        "  Each factor references specific on-chain evidence (transactions, patterns, attributions).",
        "  This is not a machine learning model - all weights and logic are versioned and auditable.",
    ])

    return "\n".join(lines)