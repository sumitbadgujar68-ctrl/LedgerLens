"""Phase 6 — investigation report generation service.

Aggregates verified case/trace/graph/risk/pattern/entity/attribution/evidence
data into structured report data covering the 14 documented report sections
(docs/ROADMAP.md Phase 6 deliverables; MASTER_BOOTSTRAP.md Module 11).

Guarantees:
- Deterministic output for identical inputs (ordered sections, sorted lists).
- No fabrication: unavailable sources are marked explicitly with a reason;
  empty findings are reported as empty findings with a note.
- Provenance preserved: every item retains its underlying identifiers
  (transaction_hash, pattern_id, attribution_id, risk_score_id, evidence_id,
  trace_id).
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from app.services.ai.grounding import GroundingLayer

logger = logging.getLogger("ledgerlens.reporting")

VALID_REPORT_TYPES = ("summary", "detailed", "evidence_export")
VALID_FORMATS = ("pdf", "json", "html")

TRANSACTION_FETCH_LIMIT = 500

# Ordered inventory of the 14 documented report sections.
SECTION_ORDER: Tuple[str, ...] = (
    "case_information",
    "initial_reported_wallet",
    "investigation_methodology",
    "transaction_timeline",
    "graph_summary",
    "intermediary_wallets",
    "destination_entities",
    "vasp_attribution_results",
    "risk_analysis",
    "detected_patterns",
    "evidence_references",
    "investigator_notes",
    "limitations_and_disclaimers",
    "generated_timestamp",
)

SECTION_TITLES: Dict[str, str] = {
    "case_information": "Case Information",
    "initial_reported_wallet": "Initial Reported Wallet",
    "investigation_methodology": "Investigation Methodology",
    "transaction_timeline": "Transaction Timeline",
    "graph_summary": "Graph Summary",
    "intermediary_wallets": "Intermediary Wallets",
    "destination_entities": "Destination Entities",
    "vasp_attribution_results": "VASP Attribution Results",
    "risk_analysis": "Risk Analysis",
    "detected_patterns": "Detected Patterns",
    "evidence_references": "Evidence References",
    "investigator_notes": "Investigator Notes",
    "limitations_and_disclaimers": "Limitations and Disclaimers",
    "generated_timestamp": "Generated Timestamp",
}

# Section inventory per documented report type (DATA_MODEL.md report_type check).
REPORT_TYPE_SECTIONS: Dict[str, Tuple[str, ...]] = {
    "detailed": SECTION_ORDER,
    "summary": (
        "case_information",
        "initial_reported_wallet",
        "investigation_methodology",
        "graph_summary",
        "risk_analysis",
        "detected_patterns",
        "limitations_and_disclaimers",
        "generated_timestamp",
    ),
    "evidence_export": (
        "case_information",
        "initial_reported_wallet",
        "transaction_timeline",
        "evidence_references",
        "investigator_notes",
        "limitations_and_disclaimers",
        "generated_timestamp",
    ),
}

# Documented disclaimers (docs/MASTER_BOOTSTRAP.md 5.7/5.8, docs/KNOWN_LIMITATIONS.md).
DISCLAIMERS: Tuple[str, ...] = (
    "This report is investigative intelligence for authorized investigators "
    "and does not constitute a legal conclusion.",
    "All findings require human investigator verification before any action is taken.",
    "Data reflects records available at generation time from the configured "
    "blockchain provider; provider gaps, rate limits, or chain reorganizations "
    "may affect completeness.",
    "Entity and VASP attributions are probabilistic matches with explicit "
    "confidence levels and are not definitive identifications.",
    "Risk scores are explainable assessments derived from deterministic rules "
    "and are not accusations of wrongdoing.",
    "No transaction, attribution, risk, pattern, or evidence record in this "
    "report was invented by the reporting system; unavailable data is marked "
    "explicitly as unavailable.",
)


class ReportCaseNotFoundError(Exception):
    """Raised when the requested case does not exist."""

    def __init__(self, case_id):
        self.case_id = case_id
        super().__init__(f"Case {case_id} not found")


class InvalidReportTypeError(ValueError):
    """Raised when a report type outside the documented enum is requested."""


class ReportGenerator:
    """Builds structured report data from verified case data sources.

    Read-only: never writes to the database. Persistence and export formats
    are handled by later Phase 6 stages.
    """

    def __init__(self, db):
        self.db = db
        self.grounding = GroundingLayer(db)
        self._source_cache: Dict[str, Any] = {}

    async def generate(
        self,
        case_id: UUID,
        report_type: str = "detailed",
        report_format: str = "json",
        generated_at: Optional[datetime] = None,
        generated_by: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Generate structured report data for a case.

        Raises ReportCaseNotFoundError when the case does not exist and
        InvalidReportTypeError for undocumented report types/formats.
        """
        if report_type not in VALID_REPORT_TYPES:
            raise InvalidReportTypeError(
                f"Invalid report type {report_type!r}; "
                f"expected one of {', '.join(VALID_REPORT_TYPES)}"
            )
        if report_format not in VALID_FORMATS:
            raise InvalidReportTypeError(
                f"Invalid report format {report_format!r}; "
                f"expected one of {', '.join(VALID_FORMATS)}"
            )

        case = await self.grounding.get_case(case_id)
        if not case:
            raise ReportCaseNotFoundError(case_id)

        if generated_at is None:
            generated_at = datetime.now(timezone.utc)

        self._source_cache = {"case_id": case_id}
        section_keys = REPORT_TYPE_SECTIONS[report_type]
        sections = [await self._build_section(key, case, generated_at) for key in section_keys]

        return {
            "case_id": str(case.get("case_id") or case_id),
            "case_number": case.get("case_number"),
            "title": case.get("title"),
            "report_type": report_type,
            "format": report_format,
            "generated_at": generated_at.isoformat(),
            "generated_by": str(generated_by) if generated_by else None,
            "sections": sections,
            "unavailable_sections": [s["key"] for s in sections if not s["available"]],
        }

    # ------------------------------------------------------------------
    # Source fetching (cached; evidence fetch failures — e.g. when
    # migration 004 has not been applied yet — are represented
    # explicitly as unavailable instead of raising).
    # ------------------------------------------------------------------

    async def _source(self, name: str) -> Any:
        if name in self._source_cache:
            return self._source_cache[name]
        value = await getattr(self, f"_fetch_{name}")()
        self._source_cache[name] = value
        return value

    async def _fetch_trace_runs(self) -> List[Dict[str, Any]]:
        case_id = self._source_cache["case_id"]
        return await self.grounding.get_trace_runs(case_id)

    async def _fetch_graph(self) -> Any:
        case_id = self._source_cache["case_id"]
        return await self.grounding.get_graph(case_id, None)

    async def _fetch_patterns(self) -> List[Dict[str, Any]]:
        case_id = self._source_cache["case_id"]
        return await self.grounding.get_patterns(case_id, None)

    async def _fetch_attributions(self) -> List[Dict[str, Any]]:
        case_id = self._source_cache["case_id"]
        return await self.grounding.get_attributions(case_id, None)

    async def _fetch_risk_scores(self) -> List[Dict[str, Any]]:
        case_id = self._source_cache["case_id"]
        return await self.grounding.get_risk_scores(case_id, None)

    async def _fetch_transactions(self) -> List[Dict[str, Any]]:
        case_id = self._source_cache["case_id"]
        return await self.grounding.get_transactions(
            case_id, None, limit=TRANSACTION_FETCH_LIMIT
        )

    async def _fetch_evidence(self) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """Return (items, reason). Items are None when the store is unavailable."""
        case_id = self._source_cache["case_id"]
        try:
            return await self.grounding.get_evidence(case_id), None
        except Exception as exc:  # known unprovisioned evidence store
            logger.warning("Evidence store unavailable for case %s: %s", case_id, exc)
            return None, f"Evidence store unavailable: {exc}"

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    async def _build_section(
        self, key: str, case: Dict[str, Any], generated_at: datetime
    ) -> Dict[str, Any]:
        builder = getattr(self, f"_section_{key}")
        return await builder(case, generated_at)

    @staticmethod
    def _section(
        key: str, *, available: bool, data: Any = None,
        reason: Optional[str] = None, note: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "key": key,
            "title": SECTION_TITLES[key],
            "available": available,
            "data": data,
            "reason": reason,
            "note": note,
        }

    async def _section_case_information(
        self, case: Dict[str, Any], generated_at: datetime
    ) -> Dict[str, Any]:
        data = {
            "case_id": case.get("case_id"),
            "case_number": case.get("case_number"),
            "title": case.get("title"),
            "blockchain": case.get("blockchain"),
            "fraud_type": case.get("fraud_type"),
            "status": case.get("status"),
            "reported_amount": case.get("reported_amount"),
            "reported_asset": case.get("reported_asset"),
            "reported_date": case.get("reported_date"),
            "created_at": case.get("created_at"),
            "updated_at": case.get("updated_at"),
        }
        return self._section("case_information", available=True, data=data)

    async def _section_initial_reported_wallet(
        self, case: Dict[str, Any], generated_at: datetime
    ) -> Dict[str, Any]:
        wallet = case.get("reported_wallet_address")
        if not wallet:
            return self._section(
                "initial_reported_wallet",
                available=False,
                reason="Case has no reported wallet address recorded",
            )
        data = {
            "wallet_address": wallet,
            "reported_transaction_hash": case.get("reported_transaction_hash"),
        }
        return self._section("initial_reported_wallet", available=True, data=data)

    async def _section_investigation_methodology(
        self, case: Dict[str, Any], generated_at: datetime
    ) -> Dict[str, Any]:
        trace_runs = await self._source("trace_runs")
        if not trace_runs:
            return self._section(
                "investigation_methodology",
                available=False,
                reason="No trace runs recorded for this case (run a trace first)",
            )
        runs = [
            {
                "trace_id": r.get("trace_id"),
                "start_wallet_address": r.get("start_wallet_address"),
                "blockchain": r.get("blockchain"),
                "direction": r.get("direction"),
                "max_hops": r.get("max_hops"),
                "max_branches": r.get("max_branches"),
                "status": r.get("status"),
                "result_status": r.get("result_status"),
                "created_at": r.get("created_at"),
                "completed_at": r.get("completed_at"),
            }
            for r in trace_runs
        ]
        latest = runs[0]
        description = (
            f"Funds were traced {latest.get('direction')} from "
            f"{latest.get('start_wallet_address')} on {latest.get('blockchain')} "
            f"up to {latest.get('max_hops')} hop(s) with at most "
            f"{latest.get('max_branches')} branches per hop using deterministic "
            f"breadth-first exploration of on-chain transfers. "
            f"{len(runs)} trace run(s) are recorded for this case."
        )
        data = {
            "description": description,
            "trace_run_count": len(runs),
            "trace_runs": runs,
        }
        return self._section("investigation_methodology", available=True, data=data)

    async def _section_transaction_timeline(
        self, case: Dict[str, Any], generated_at: datetime
    ) -> Dict[str, Any]:
        transactions = await self._source("transactions")
        ordered = sorted(
            transactions,
            key=lambda t: (
                t.get("block_timestamp") is None,
                t.get("block_timestamp") or "",
                t.get("transaction_hash") or "",
            ),
        )
        items = [
            {
                "transaction_hash": t.get("transaction_hash"),
                "block_number": t.get("block_number"),
                "block_timestamp": t.get("block_timestamp"),
                "from_address": t.get("from_address"),
                "to_address": t.get("to_address"),
                "amount": t.get("amount"),
                "asset_symbol": t.get("asset_symbol"),
                "transaction_type": t.get("transaction_type"),
                "status": t.get("status"),
                "discovered_at_hop": t.get("discovered_at_hop"),
            }
            for t in ordered
        ]
        complete = len(transactions) < TRANSACTION_FETCH_LIMIT
        note = None
        if not items:
            note = "No transactions recorded for this case (run a trace first)"
        elif not complete:
            note = (
                f"Timeline includes the {TRANSACTION_FETCH_LIMIT} most recent "
                "transactions; earlier transactions are available via the trace record"
            )
        data = {
            "count": len(items),
            "complete": complete,
            "transactions": items,
        }
        return self._section("transaction_timeline", available=True, data=data, note=note)

    async def _section_graph_summary(
        self, case: Dict[str, Any], generated_at: datetime
    ) -> Dict[str, Any]:
        graph = await self._source("graph")
        if graph is None:
            return self._section(
                "graph_summary",
                available=False,
                reason="No transaction graph generated for this case (run a trace first)",
            )
        data = {
            "root_wallet_address": graph.root_wallet_address,
            "blockchain": graph.blockchain,
            "node_count": graph.node_count,
            "edge_count": graph.edge_count,
            "max_hop_depth": graph.max_hop_depth,
        }
        return self._section("graph_summary", available=True, data=data)

    async def _section_intermediary_wallets(
        self, case: Dict[str, Any], generated_at: datetime
    ) -> Dict[str, Any]:
        transactions = await self._source("transactions")
        initial = (case.get("reported_wallet_address") or "").lower()
        sent_counts: Dict[str, int] = {}
        received_counts: Dict[str, int] = {}
        first_seen_hop: Dict[str, Optional[int]] = {}
        for t in transactions:
            frm = (t.get("from_address") or "").lower()
            to = (t.get("to_address") or "").lower()
            if frm:
                sent_counts[frm] = sent_counts.get(frm, 0) + 1
            if to:
                received_counts[to] = received_counts.get(to, 0) + 1
                hop = t.get("discovered_at_hop")
                current = first_seen_hop.get(to)
                if current is None or (hop is not None and hop < current):
                    if hop is not None:
                        first_seen_hop[to] = hop
        intermediary_addresses = sorted(
            (set(sent_counts) & set(received_counts)) - {initial}
        )
        wallets = [
            {
                "address": addr,
                "first_seen_hop": first_seen_hop.get(addr),
                "received_count": received_counts.get(addr, 0),
                "sent_count": sent_counts.get(addr, 0),
            }
            for addr in intermediary_addresses
        ]
        note = None
        if not wallets:
            note = "No intermediary wallets identified in the recorded transactions"
        data = {"count": len(wallets), "wallets": wallets}
        return self._section("intermediary_wallets", available=True, data=data, note=note)

    async def _section_destination_entities(
        self, case: Dict[str, Any], generated_at: datetime
    ) -> Dict[str, Any]:
        transactions = await self._source("transactions")
        attributions = await self._source("attributions")
        attribution_by_address = self._attribution_index(attributions)

        received_counts: Dict[str, int] = {}
        received_by_asset: Dict[str, Dict[str, Decimal]] = {}
        unparsed_amounts = 0
        for t in transactions:
            to = (t.get("to_address") or "").lower()
            frm = (t.get("from_address") or "").lower()
            if not to or to == frm:
                continue
            received_counts[to] = received_counts.get(to, 0) + 1
            asset = t.get("asset_symbol") or "unknown"
            totals = received_by_asset.setdefault(to, {})
            try:
                totals[asset] = totals.get(asset, Decimal("0")) + Decimal(
                    str(t.get("amount") or "0")
                )
            except (InvalidOperation, ValueError):
                unparsed_amounts += 1

        source_addresses = {
            (t.get("from_address") or "").lower() for t in transactions
        } - {""}
        destination_addresses = sorted(
            addr for addr in received_counts if addr not in source_addresses
        )

        entities = []
        for addr in destination_addresses:
            attribution = attribution_by_address.get(addr)
            entity = None
            if attribution:
                entity = {
                    "attribution_id": attribution.get("attribution_id"),
                    "entity": attribution.get("entity"),
                    "provenance_level": attribution.get("provenance_level"),
                    "confidence": attribution.get("confidence"),
                }
            totals = received_by_asset.get(addr, {})
            entities.append(
                {
                    "address": addr,
                    "received_count": received_counts.get(addr, 0),
                    "received_by_asset": {
                        asset: str(amount)
                        for asset, amount in sorted(totals.items())
                    },
                    "entity": entity,
                }
            )
        note = None
        if not entities:
            note = "No destination addresses identified in the recorded transactions"
        elif unparsed_amounts:
            note = (
                f"{unparsed_amounts} transaction amount(s) could not be parsed; "
                "per-asset totals exclude them"
            )
        data = {"count": len(entities), "entities": entities}
        return self._section("destination_entities", available=True, data=data, note=note)

    async def _section_vasp_attribution_results(
        self, case: Dict[str, Any], generated_at: datetime
    ) -> Dict[str, Any]:
        attributions = await self._source("attributions")
        items = [
            {
                "attribution_id": a.get("attribution_id"),
                "wallet_address": a.get("wallet_address"),
                "entity": a.get("entity"),
                "provenance_level": a.get("provenance_level"),
                "confidence": a.get("confidence"),
                "attribution_method": a.get("attribution_method"),
                "source": a.get("source"),
                "attributed_at": a.get("attributed_at"),
                "evidence": a.get("evidence"),
            }
            for a in sorted(
                attributions,
                key=lambda x: (x.get("wallet_address") or "", x.get("attribution_id") or ""),
            )
        ]
        note = None
        if not items:
            note = "No VASP/entity attributions recorded for this case"
        data = {"count": len(items), "attributions": items}
        return self._section(
            "vasp_attribution_results", available=True, data=data, note=note
        )

    async def _section_risk_analysis(
        self, case: Dict[str, Any], generated_at: datetime
    ) -> Dict[str, Any]:
        risk_scores = await self._source("risk_scores")
        items = [
            {
                "risk_score_id": r.get("risk_score_id"),
                "wallet_address": r.get("wallet_address"),
                "score": r.get("score"),
                "risk_category": r.get("risk_category"),
                "scoring_version": r.get("scoring_version"),
                "calculated_at": r.get("calculated_at"),
                "factors": r.get("factors"),
            }
            for r in sorted(
                risk_scores,
                key=lambda x: (x.get("wallet_address") or "", x.get("risk_score_id") or ""),
            )
        ]
        note = None
        if not items:
            note = "No risk scores calculated for this case (run risk analysis first)"
        data = {"count": len(items), "risk_scores": items}
        return self._section("risk_analysis", available=True, data=data, note=note)

    async def _section_detected_patterns(
        self, case: Dict[str, Any], generated_at: datetime
    ) -> Dict[str, Any]:
        patterns = await self._source("patterns")
        items = [
            {
                "pattern_id": p.get("pattern_id"),
                "pattern_type": p.get("pattern_type"),
                "wallet_address": p.get("wallet_address"),
                "confidence": p.get("confidence"),
                "description": p.get("description"),
                "evidence": p.get("evidence"),
                "detected_at": p.get("detected_at"),
            }
            for p in sorted(
                patterns,
                key=lambda x: (x.get("wallet_address") or "", x.get("pattern_id") or ""),
            )
        ]
        note = None
        if not items:
            note = "No patterns detected for this case (run pattern analysis first)"
        data = {"count": len(items), "patterns": items}
        return self._section("detected_patterns", available=True, data=data, note=note)

    async def _section_evidence_references(
        self, case: Dict[str, Any], generated_at: datetime
    ) -> Dict[str, Any]:
        evidence, reason = await self._source("evidence")
        if evidence is None:
            return self._section(
                "evidence_references", available=False, reason=reason
            )
        items = [
            {
                "evidence_id": e.get("evidence_id"),
                "evidence_type": e.get("evidence_type"),
                "reference_id": e.get("reference_id"),
                "investigator_note": e.get("investigator_note"),
                "investigator_id": e.get("investigator_id"),
                "pinned_at": e.get("pinned_at"),
            }
            for e in sorted(
                evidence,
                key=lambda x: (x.get("pinned_at") or "", x.get("evidence_id") or ""),
            )
        ]
        note = None
        if not items:
            note = "No investigator evidence pinned for this case"
        data = {"count": len(items), "evidence": items}
        return self._section("evidence_references", available=True, data=data, note=note)

    async def _section_investigator_notes(
        self, case: Dict[str, Any], generated_at: datetime
    ) -> Dict[str, Any]:
        notes = case.get("investigator_notes")
        if not notes:
            return self._section(
                "investigator_notes",
                available=False,
                reason="No investigator notes recorded for this case",
            )
        data = {"case_notes": notes}
        return self._section("investigator_notes", available=True, data=data)

    async def _section_limitations_and_disclaimers(
        self, case: Dict[str, Any], generated_at: datetime
    ) -> Dict[str, Any]:
        data = {"disclaimers": list(DISCLAIMERS)}
        return self._section("limitations_and_disclaimers", available=True, data=data)

    async def _section_generated_timestamp(
        self, case: Dict[str, Any], generated_at: datetime
    ) -> Dict[str, Any]:
        data = {"generated_at": generated_at.isoformat()}
        return self._section("generated_timestamp", available=True, data=data)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _attribution_index(attributions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Index attributions by wallet address, highest confidence wins.

        Ties break on attribution_id for determinism.
        """
        index: Dict[str, Dict[str, Any]] = {}
        for attribution in attributions:
            address = (attribution.get("wallet_address") or "").lower()
            if not address:
                continue
            current = index.get(address)
            if current is None:
                index[address] = attribution
                continue
            if ReportGenerator._confidence_key(attribution) > ReportGenerator._confidence_key(
                current
            ):
                index[address] = attribution
        return index

    @staticmethod
    def _confidence_key(attribution: Dict[str, Any]) -> Tuple[Decimal, str]:
        try:
            confidence = Decimal(str(attribution.get("confidence") or "-1"))
        except (InvalidOperation, ValueError):
            confidence = Decimal("-1")
        return confidence, attribution.get("attribution_id") or ""


def get_report_generator(db) -> ReportGenerator:
    return ReportGenerator(db)
