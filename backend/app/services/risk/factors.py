from collections import defaultdict
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from app.services.entity.attribution_engine import AttributionEngine
from app.services.graph.model import CanonicalGraph
from app.services.patterns.models import PatternFinding, PatternType
from app.services.risk.models import (
    DEFAULT_WEIGHTS,
    RiskFactor,
    RiskFactorEvidence,
    RiskFactorType,
)


class RiskFactorCalculator:
    def __init__(
        self,
        graph: CanonicalGraph,
        patterns: List[PatternFinding],
        attributions: List[Any],
        db_session=None,
        linked_case_count: Optional[int] = None,
    ):
        self.graph = graph
        self.patterns = patterns
        self.attributions = attributions
        self.db_session = db_session
        self.linked_case_count = linked_case_count

        self._patterns_by_wallet: Dict[str, List[PatternFinding]] = defaultdict(list)
        for p in patterns:
            self._patterns_by_wallet[p.wallet_address].append(p)

        self._attributions_by_wallet: Dict[str, List[Any]] = defaultdict(list)
        for a in attributions:
            self._attributions_by_wallet[a.wallet_address].append(a)

    def calculate_all(self, wallet_address: str, include_zero_weight: bool = False) -> List[RiskFactor]:
        factors = []

        factors.append(self._calculate_known_malicious_association(wallet_address))
        factors.append(self._calculate_rapid_onward_transfer(wallet_address))
        factors.append(self._calculate_high_fan_in(wallet_address))
        factors.append(self._calculate_layering_peel_chain(wallet_address))
        factors.append(self._calculate_mixer_interaction(wallet_address))
        factors.append(self._calculate_repeated_case_linkage(wallet_address))

        if include_zero_weight:
            return factors
        return [f for f in factors if f.weight > 0]

    def _calculate_known_malicious_association(self, wallet_address: str) -> RiskFactor:
        weight = DEFAULT_WEIGHTS[RiskFactorType.KNOWN_MALICIOUS_ASSOCIATION]
        evidence = RiskFactorEvidence()
        description = ""
        confidence = Decimal("0.00")

        attributions = self._attributions_by_wallet.get(wallet_address, [])
        malicious_entities = []

        for attr in attributions:
            if attr.candidate_entity and attr.candidate_entity.entity_type in (
                "scam_infrastructure",
                "mixer",
                "darknet_market",
            ):
                malicious_entities.append(attr)
                evidence.attribution_ids.append(str(attr.attribution_id))
                evidence.entity_ids.append(str(attr.candidate_entity_id))
                if attr.candidate_entity:
                    evidence.additional_data[attr.candidate_entity.name] = attr.provenance_level

        if malicious_entities:
            confidence = Decimal("1.00")
            entity_names = [a.candidate_entity.name for a in malicious_entities if a.candidate_entity]
            description = f"Direct attribution to known malicious entities: {', '.join(entity_names)}"
        else:
            weight = 0
            description = "No known malicious entity attribution"

        return RiskFactor(
            factor_type=RiskFactorType.KNOWN_MALICIOUS_ASSOCIATION,
            weight=weight,
            evidence=evidence,
            description=description,
            confidence=confidence,
        )

    def _calculate_rapid_onward_transfer(self, wallet_address: str) -> RiskFactor:
        weight = DEFAULT_WEIGHTS[RiskFactorType.RAPID_ONWARD_TRANSFER]
        evidence = RiskFactorEvidence()
        description = ""
        confidence = Decimal("0.00")

        patterns = self._patterns_by_wallet.get(wallet_address, [])
        rapid_patterns = [p for p in patterns if p.pattern_type == PatternType.RAPID_FORWARDING]

        if rapid_patterns:
            confidence = Decimal("1.00")
            evidence.pattern_ids = [str(p.pattern_id) for p in rapid_patterns if hasattr(p, 'pattern_id')]
            for p in rapid_patterns:
                if p.evidence.get("inbound_tx"):
                    evidence.transaction_hashes.append(p.evidence["inbound_tx"])
                if p.evidence.get("outbound_tx"):
                    evidence.transaction_hashes.append(p.evidence["outbound_tx"])
                time_delta = p.evidence.get("time_delta_seconds", 0)
                description = (
                    f"Rapid forwarding detected: {len(rapid_patterns)} occurrence(s), "
                    f"fastest within {time_delta}s"
                )
        else:
            weight = 0
            description = "No rapid forwarding pattern detected"

        return RiskFactor(
            factor_type=RiskFactorType.RAPID_ONWARD_TRANSFER,
            weight=weight,
            evidence=evidence,
            description=description,
            confidence=confidence,
        )

    def _calculate_high_fan_in(self, wallet_address: str) -> RiskFactor:
        weight = DEFAULT_WEIGHTS[RiskFactorType.HIGH_FAN_IN]
        evidence = RiskFactorEvidence()
        description = ""
        confidence = Decimal("0.00")

        patterns = self._patterns_by_wallet.get(wallet_address, [])
        fan_in_patterns = [p for p in patterns if p.pattern_type == PatternType.HIGH_FAN_IN]

        if fan_in_patterns:
            confidence = Decimal("1.00")
            evidence.pattern_ids = [str(p.pattern_id) for p in fan_in_patterns if hasattr(p, 'pattern_id')]
            for p in fan_in_patterns:
                if p.evidence.get("sender_addresses"):
                    evidence.wallet_addresses.extend(p.evidence["sender_addresses"])
                if p.evidence.get("tx_hashes"):
                    evidence.transaction_hashes.extend(p.evidence["tx_hashes"])
                sender_count = p.metrics.get("sender_count", 0)
                description = f"High fan-in detected: {sender_count} distinct senders"
        else:
            in_edges = [e for e in self.graph.edges if e.target == wallet_address]
            unique_senders = len({e.source for e in in_edges})
            if unique_senders >= 5:
                weight = DEFAULT_WEIGHTS[RiskFactorType.HIGH_FAN_IN]
                confidence = Decimal("0.75")
                evidence.wallet_addresses = list({e.source for e in in_edges})
                evidence.transaction_hashes = [e.transaction_hash for e in in_edges]
                description = f"High fan-in inferred from graph: {unique_senders} distinct senders (no pattern match)"
            else:
                weight = 0
                description = "No high fan-in pattern detected"

        return RiskFactor(
            factor_type=RiskFactorType.HIGH_FAN_IN,
            weight=weight,
            evidence=evidence,
            description=description,
            confidence=confidence,
        )

    def _calculate_layering_peel_chain(self, wallet_address: str) -> RiskFactor:
        weight = DEFAULT_WEIGHTS[RiskFactorType.LAYERING_PEEL_CHAIN]
        evidence = RiskFactorEvidence()
        description = ""
        confidence = Decimal("0.00")

        patterns = self._patterns_by_wallet.get(wallet_address, [])
        peel_patterns = [p for p in patterns if p.pattern_type == PatternType.PEEL_CHAIN]
        cyclic_patterns = [p for p in patterns if p.pattern_type == PatternType.CYCLIC_FLOW]

        relevant_patterns = peel_patterns + cyclic_patterns

        if relevant_patterns:
            confidence = Decimal("1.00")
            evidence.pattern_ids = [str(p.pattern_id) for p in relevant_patterns if hasattr(p, 'pattern_id')]
            for p in relevant_patterns:
                if p.evidence.get("chain"):
                    evidence.wallet_addresses.extend(p.evidence["chain"])
                if p.evidence.get("tx_hashes"):
                    evidence.transaction_hashes.extend(p.evidence["tx_hashes"])
                if p.evidence.get("cycle_path"):
                    evidence.wallet_addresses.extend(p.evidence["cycle_path"])

            if peel_patterns:
                chain_length = peel_patterns[0].evidence.get("chain_length", 0)
                description = f"Peel chain detected: {chain_length} hops"
            else:
                cycle_len = cyclic_patterns[0].evidence.get("cycle_path", [])
                description = f"Cyclic flow detected: {len(cycle_len)} nodes in cycle"
        else:
            weight = 0
            description = "No layering or peel-chain pattern detected"

        return RiskFactor(
            factor_type=RiskFactorType.LAYERING_PEEL_CHAIN,
            weight=weight,
            evidence=evidence,
            description=description,
            confidence=confidence,
        )

    def _calculate_mixer_interaction(self, wallet_address: str) -> RiskFactor:
        weight = DEFAULT_WEIGHTS[RiskFactorType.MIXER_INTERACTION]
        evidence = RiskFactorEvidence()
        description = ""
        confidence = Decimal("0.00")

        mixer_attributions = []
        for attr in self._attributions_by_wallet.get(wallet_address, []):
            if attr.candidate_entity and attr.candidate_entity.entity_type == "mixer":
                mixer_attributions.append(attr)
                evidence.attribution_ids.append(str(attr.attribution_id))
                evidence.entity_ids.append(str(attr.candidate_entity_id))
                if attr.candidate_entity:
                    evidence.additional_data[attr.candidate_entity.name] = attr.provenance_level

        if not mixer_attributions:
            for edge in self.graph.edges:
                if edge.source == wallet_address or edge.target == wallet_address:
                    counterparty = edge.target if edge.source == wallet_address else edge.source
                    for attr in self._attributions_by_wallet.get(counterparty, []):
                        if attr.candidate_entity and attr.candidate_entity.entity_type == "mixer":
                            mixer_attributions.append(attr)
                            evidence.attribution_ids.append(str(attr.attribution_id))
                            evidence.entity_ids.append(str(attr.candidate_entity_id))
                            evidence.wallet_addresses.append(counterparty)

        if mixer_attributions:
            confidence = Decimal("1.00")
            mixer_names = list({a.candidate_entity.name for a in mixer_attributions if a.candidate_entity})
            description = f"Interaction with mixer service(s): {', '.join(mixer_names)}"
        else:
            weight = 0
            description = "No mixer interaction detected"

        return RiskFactor(
            factor_type=RiskFactorType.MIXER_INTERACTION,
            weight=weight,
            evidence=evidence,
            description=description,
            confidence=confidence,
        )

    def _calculate_repeated_case_linkage(self, wallet_address: str) -> RiskFactor:
        weight = DEFAULT_WEIGHTS[RiskFactorType.REPEATED_CASE_LINKAGE]
        evidence = RiskFactorEvidence()
        description = ""
        confidence = Decimal("0.00")

        count = self.linked_case_count
        if count is None:
            count = self._query_repeated_case_count(wallet_address)

        if count is None:
            weight = 0
            description = "Repeated case linkage check skipped (count unavailable)"
        elif count > 1:
            confidence = Decimal("0.80")
            evidence.additional_data["linked_case_count"] = count
            description = f"Wallet appears in {count} previous cases"
        else:
            weight = 0
            description = "No repeated case linkage found"

        return RiskFactor(
            factor_type=RiskFactorType.REPEATED_CASE_LINKAGE,
            weight=weight,
            evidence=evidence,
            description=description,
            confidence=confidence,
        )

    def _query_repeated_case_count(self, wallet_address: str) -> Optional[int]:
        """Synchronous-only fallback.

        Async sessions cannot be queried from this sync code path; callers on an
        async session must pre-fetch the count and pass ``linked_case_count``.
        """
        if self.db_session is None:
            return None
        from sqlalchemy.ext.asyncio import AsyncSession

        if isinstance(self.db_session, AsyncSession):
            return None
        try:
            from sqlalchemy import select, func

            from app.db.models import RiskScoreRecord

            stmt = select(func.count(RiskScoreRecord.risk_score_id)).where(
                RiskScoreRecord.wallet_address == wallet_address
            )
            result = self.db_session.execute(stmt)
            return int(result.scalar() or 0)
        except Exception:
            return None