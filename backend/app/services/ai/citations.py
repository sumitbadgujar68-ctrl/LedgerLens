from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID


@dataclass
class Citation:
    type: str
    reference_id: str
    summary: str
    detail: Optional[str] = None
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "reference_id": self.reference_id,
            "summary": self.summary,
            "detail": self.detail,
            "confidence": self.confidence,
        }


class CitationGenerator:
    CITATION_TYPES = {
        "transaction": "Transaction",
        "pattern": "Pattern Detection",
        "attribution": "Entity Attribution",
        "risk_factor": "Risk Factor",
        "evidence": "Investigator Evidence",
        "case": "Case Metadata",
    }

    def __init__(self):
        self._citation_cache: Dict[str, Citation] = {}

    def create_transaction_citation(self, transaction: Dict[str, Any]) -> Citation:
        ref_id = transaction.get("transaction_id") or transaction.get("transaction_hash")
        return Citation(
            type="transaction",
            reference_id=ref_id,
            summary=f"Transaction {transaction.get('transaction_hash', 'Unknown')} "
                    f"({transaction.get('amount', 'Unknown')} {transaction.get('asset_symbol', '')})",
            detail=(
                f"From: {transaction.get('from_address', 'Unknown')} -> "
                f"To: {transaction.get('to_address', 'Unknown')} | "
                f"Block: {transaction.get('block_number', 'Unknown')} | "
                f"Hop: {transaction.get('discovered_at_hop', 'Unknown')}"
            ),
        )

    def create_pattern_citation(self, pattern: Dict[str, Any]) -> Citation:
        ref_id = pattern.get("pattern_id")
        return Citation(
            type="pattern",
            reference_id=ref_id,
            summary=f"{pattern.get('pattern_type', 'Unknown').replace('_', ' ').title()} at "
                    f"{pattern.get('wallet_address', 'Unknown')}",
            detail=pattern.get("description", "No description"),
            confidence=float(pattern.get("confidence", 1.0)),
        )

    def create_attribution_citation(self, attribution: Dict[str, Any]) -> Citation:
        ref_id = attribution.get("attribution_id")
        entity = attribution.get("entity", {})
        return Citation(
            type="attribution",
            reference_id=ref_id,
            summary=f"{entity.get('name', 'Unknown')} ({entity.get('entity_type', 'Unknown')}) "
                    f"at {attribution.get('wallet_address', 'Unknown')}",
            detail=(
                f"Provenance: {attribution.get('provenance_level', 'Unknown')} | "
                f"Method: {attribution.get('attribution_method', 'Unknown')} | "
                f"Confidence: {attribution.get('confidence', 'Unknown')}"
            ),
            confidence=float(attribution.get("confidence", 1.0)),
        )

    def create_risk_factor_citation(self, risk_score: Dict[str, Any], factor_type: str) -> Citation:
        ref_id = risk_score.get("risk_score_id")
        factor_data = next(
            (f for f in risk_score.get("factors", []) if f.get("factor_type") == factor_type),
            None,
        )
        weight = factor_data.get("weight", 0) if factor_data else 0
        return Citation(
            type="risk_factor",
            reference_id=ref_id,
            summary=f"{factor_type.replace('_', ' ').title()} (+{weight}) for "
                    f"{risk_score.get('wallet_address', 'Unknown')}",
            detail=factor_data.get("description", "No description") if factor_data else "No detail",
        )

    def create_evidence_citation(self, evidence: Dict[str, Any]) -> Citation:
        ref_id = evidence.get("evidence_id")
        return Citation(
            type="evidence",
            reference_id=ref_id,
            summary=f"Investigator evidence: {evidence.get('evidence_type', 'Unknown')} "
                    f"({evidence.get('reference_id', 'Unknown')})",
            detail=evidence.get("investigator_note", "No note"),
        )

    def create_case_citation(self, case: Dict[str, Any]) -> Citation:
        ref_id = case.get("case_id")
        return Citation(
            type="case",
            reference_id=ref_id,
            summary=f"Case {case.get('case_number', 'Unknown')}: {case.get('title', 'Unknown')}",
            detail=f"Blockchain: {case.get('blockchain', 'Unknown')} | "
                   f"Fraud Type: {case.get('fraud_type', 'Unknown')}",
        )

    def validate_citation(self, citation: Citation, available_data: Dict[str, List[Dict[str, Any]]]) -> bool:
        if citation.type == "transaction":
            transactions = available_data.get("transactions", [])
            return any(t.get("transaction_id") == citation.reference_id or
                       t.get("transaction_hash") == citation.reference_id for t in transactions)
        elif citation.type == "pattern":
            patterns = available_data.get("patterns", [])
            return any(p.get("pattern_id") == citation.reference_id for p in patterns)
        elif citation.type == "attribution":
            attributions = available_data.get("attributions", [])
            return any(a.get("attribution_id") == citation.reference_id for a in attributions)
        elif citation.type == "risk_factor":
            risk_scores = available_data.get("risk_scores", [])
            return any(r.get("risk_score_id") == citation.reference_id for r in risk_scores)
        elif citation.type == "evidence":
            evidence = available_data.get("evidence", [])
            return any(e.get("evidence_id") == citation.reference_id for e in evidence)
        elif citation.type == "case":
            return True
        return False

    def filter_valid_citations(self, citations: List[Citation], available_data: Dict[str, List[Dict[str, Any]]]) -> List[Citation]:
        return [c for c in citations if self.validate_citation(c, available_data)]