import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum


class ResponseType(str, Enum):
    ANSWER = "answer"
    INSUFFICIENT_DATA = "insufficient_data"
    ERROR = "error"


@dataclass
class SafetyCheckResult:
    allowed: bool
    reason: Optional[str] = None
    response_type: ResponseType = ResponseType.ANSWER
    suggested_response: Optional[str] = None


class HallucinationGuard:
    TX_HASH_PATTERN = re.compile(r"0x[a-fA-F0-9]{64}")
    ADDRESS_PATTERN = re.compile(r"(?<![a-fA-F0-9])0x[a-fA-F0-9]{40}(?![a-fA-F0-9])")
    ENTITY_CLAIM_PATTERN = re.compile(
        r"Entity\s+(?:named\s+|:\s*)?([A-Za-z0-9_\-\.&]+)", re.IGNORECASE
    )
    PATTERN_CLAIM_PATTERN = re.compile(
        r"Pattern\s+(?:named\s+|:\s*)?([a-z_]+)", re.IGNORECASE
    )
    RISK_SCORE_PATTERN = re.compile(
        r"(?:is\s+|:\s+)(\d+)|score\s+(\d+)", re.IGNORECASE
    )
    EVIDENCE_CLAIM_PATTERN = re.compile(
        r"Evidence\s+(?:reference\s+|:\s*)?([A-Za-z0-9_\-]+)", re.IGNORECASE
    )

    known_fact_prefixes = [
        "Transaction ",
        "Address ",
        "Entity ",
        "Pattern ",
        "Risk score ",
        "Evidence ",
    ]

    def check_response(
        self, response: str, available_context: Dict[str, Any]
    ) -> SafetyCheckResult:
        problems: List[str] = []

        for tx_hash in self.TX_HASH_PATTERN.findall(response):
            if not self._tx_hash_exists(tx_hash, available_context):
                problems.append(f"Unverified transaction hash: {tx_hash}")

        for addr in self.ADDRESS_PATTERN.findall(response):
            if not self._address_exists(addr, available_context):
                problems.append(f"Unverified address: {addr}")

        for claim in self._extract_claims(response):
            problem = self._verify_prefixed_claim(claim, available_context)
            if problem:
                problems.append(problem)

        if problems:
            return SafetyCheckResult(
                allowed=False,
                reason="; ".join(problems),
                response_type=ResponseType.INSUFFICIENT_DATA,
                suggested_response=(
                    "I don't have sufficient verified data to confirm these claims. "
                    "The available case data does not contain evidence supporting them."
                ),
            )
        return SafetyCheckResult(allowed=True)

    def _extract_claims(self, response: str) -> List[str]:
        claims: List[str] = []
        for line in response.split("\n"):
            line = line.strip()
            for prefix in self.known_fact_prefixes:
                if prefix in line:
                    start = line.find(prefix)
                    end = line.find(".", start)
                    if end == -1:
                        end = len(line)
                    claims.append(line[start : end + 1].strip())
        return claims

    def _verify_prefixed_claim(
        self, claim: str, context: Dict[str, Any]
    ) -> Optional[str]:
        claim_lower = claim.lower()
        if claim_lower.startswith("entity"):
            return self._verify_entity_claim(claim, context)
        if claim_lower.startswith("pattern"):
            return self._verify_pattern_claim(claim, context)
        if claim_lower.startswith("risk score"):
            return self._verify_risk_claim(claim, context)
        if claim_lower.startswith("evidence"):
            return self._verify_evidence_claim(claim, context)
        return None

    def _tx_hash_exists(self, tx_hash: str, context: Dict[str, Any]) -> bool:
        target = tx_hash.lower()
        for t in context.get("transactions", []):
            if t.get("transaction_hash", "").lower() == target:
                return True
        return False

    def _get_valid_addresses(self, context: Dict[str, Any]) -> set:
        addresses: set = set()
        for t in context.get("transactions", []):
            if t.get("from_address"):
                addresses.add(t["from_address"].lower())
            if t.get("to_address"):
                addresses.add(t["to_address"].lower())
        for a in context.get("attributions", []):
            if a.get("wallet_address"):
                addresses.add(a["wallet_address"].lower())
        for p in context.get("patterns", []):
            if p.get("wallet_address"):
                addresses.add(p["wallet_address"].lower())
        for r in context.get("risk_scores", []):
            if r.get("wallet_address"):
                addresses.add(r["wallet_address"].lower())
        case = context.get("case", {})
        if isinstance(case, dict) and case.get("reported_wallet_address"):
            addresses.add(case["reported_wallet_address"].lower())
        graph = context.get("graph")
        if graph is not None and hasattr(graph, "nodes"):
            for node in graph.nodes:
                node_id = getattr(node, "id", None)
                if node_id:
                    addresses.add(node_id.lower())
        return addresses

    def _address_exists(self, address: str, context: Dict[str, Any]) -> bool:
        return address.lower() in self._get_valid_addresses(context)

    def _verify_entity_claim(
        self, claim: str, context: Dict[str, Any]
    ) -> Optional[str]:
        match = self.ENTITY_CLAIM_PATTERN.search(claim)
        if not match:
            return None
        claimed_name = match.group(1).lower()
        for a in context.get("attributions", []):
            entity = a.get("entity")
            if entity and entity.get("name", "").lower() == claimed_name:
                return None
        return f"Unverified entity: {match.group(1)}"

    def _verify_pattern_claim(
        self, claim: str, context: Dict[str, Any]
    ) -> Optional[str]:
        match = self.PATTERN_CLAIM_PATTERN.search(claim)
        if not match:
            return None
        claimed_type = match.group(1).lower()
        for p in context.get("patterns", []):
            if p.get("pattern_type", "").lower() == claimed_type:
                return None
        return f"Unverified pattern: {match.group(1)}"

    def _verify_risk_claim(
        self, claim: str, context: Dict[str, Any]
    ) -> Optional[str]:
        score_match = self.RISK_SCORE_PATTERN.search(claim)
        if not score_match:
            return None
        score_str = score_match.group(1) or score_match.group(2)
        if not score_str:
            return None
        claimed_score = int(score_str)
        addr_match = self.ADDRESS_PATTERN.search(claim)
        if addr_match:
            target_addr = addr_match.group(0).lower()
            for r in context.get("risk_scores", []):
                if r.get("wallet_address", "").lower() == target_addr:
                    if r.get("score") == claimed_score:
                        return None
                    return (
                        f"Unverified risk score: {claimed_score} claimed for "
                        f"{target_addr}, expected {r.get('score')}"
                    )
            return f"Unverified risk score: no risk record for {target_addr}"
        for r in context.get("risk_scores", []):
            if r.get("score") == claimed_score:
                return None
        return f"Unverified risk score: {claimed_score}"

    def _verify_evidence_claim(
        self, claim: str, context: Dict[str, Any]
    ) -> Optional[str]:
        match = self.EVIDENCE_CLAIM_PATTERN.search(claim)
        if not match:
            return None
        claimed_ref = match.group(1)
        for e in context.get("evidence", []):
            if e.get("reference_id") == claimed_ref or e.get("evidence_id") == claimed_ref:
                return None
        return f"Unverified evidence reference: {claimed_ref}"


class InsufficientDataHandler:
    @staticmethod
    def generate_response(question: str, missing_data: List[str]) -> str:
        if "risk" in question.lower():
            return (
                "I cannot provide a risk explanation because the risk scores have not been calculated "
                "for this case, or the specific wallet's risk data is unavailable. "
                "Please run the risk analysis first, or ensure the trace includes the wallet in question."
            )
        if "pattern" in question.lower():
            return (
                "I cannot identify patterns because pattern detection has not been run on this trace, "
                "or the trace data is insufficient for pattern analysis."
            )
        if any(k in question.lower() for k in ("attribution", "vasp", "entity")):
            return (
                "I cannot provide entity attribution because the VASP attribution analysis has not been "
                "completed for this trace, or the entity registry does not contain matching addresses."
            )
        if "summar" in question.lower():
            return (
                "I cannot generate a case summary because the trace data is incomplete or unavailable. "
                "Please run a trace first to populate the case with transaction data."
            )
        missing_str = ", ".join(missing_data) if missing_data else "the requested data"
        return (
            f"I don't have sufficient data to answer this question. Missing: {missing_str}. "
            "Please ensure the relevant analysis (trace, patterns, attribution, risk) has been completed."
        )

    @staticmethod
    def check_data_availability(context: Dict[str, Any], required: List[str]) -> List[str]:
        missing: List[str] = []
        for req in required:
            if req == "transactions" and not context.get("transactions"):
                missing.append("transaction data (run a trace)")
            elif req == "patterns" and not context.get("patterns"):
                missing.append("pattern detections (run pattern analysis)")
            elif req == "attributions" and not context.get("attributions"):
                missing.append("VASP/entity attributions (run attribution analysis)")
            elif req == "risk" and not context.get("risk_scores"):
                missing.append("risk scores (run risk analysis)")
            elif req == "graph" and not context.get("graph"):
                missing.append("transaction graph (run trace with graph output)")
            elif req == "evidence" and not context.get("evidence"):
                missing.append("investigator evidence (pin transactions/notes)")
        return missing
