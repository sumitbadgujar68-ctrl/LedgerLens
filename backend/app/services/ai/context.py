from typing import Any, Dict, List, Optional
from uuid import UUID

from app.services.graph.model import CanonicalGraph


class ContextManager:
    MAX_CONTEXT_TOKENS = 8000
    RESERVED_TOKENS = 1000

    PRIORITY_ORDER = [
        "case_metadata",
        "transactions",
        "patterns",
        "attributions",
        "risk_factors",
        "evidence",
    ]

    def __init__(self, max_tokens: int = MAX_CONTEXT_TOKENS):
        self.max_tokens = max_tokens
        self.available_tokens = max_tokens - self.RESERVED_TOKENS

    def estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)

    def build_context(
        self,
        case_data: Dict[str, Any],
        graph: Optional[CanonicalGraph] = None,
        patterns: Optional[List[Dict[str, Any]]] = None,
        attributions: Optional[List[Dict[str, Any]]] = None,
        risk_scores: Optional[List[Dict[str, Any]]] = None,
        evidence: Optional[List[Dict[str, Any]]] = None,
        transactions: Optional[List[Dict[str, Any]]] = None,
        trace_runs: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        context_parts = {}

        if case_data:
            context_parts["case_metadata"] = self._format_case_metadata(case_data)

        if transactions:
            context_parts["transactions"] = self._format_transactions(transactions)

        if patterns:
            context_parts["patterns"] = self._format_patterns(patterns)

        if attributions:
            context_parts["attributions"] = self._format_attributions(attributions)

        if risk_scores:
            context_parts["risk_factors"] = self._format_risk_factors(risk_scores)

        if evidence:
            context_parts["evidence"] = self._format_evidence(evidence)

        if trace_runs:
            context_parts["trace_runs"] = self._format_trace_runs(trace_runs)

        if graph:
            context_parts["graph_summary"] = self._format_graph_summary(graph)

        truncated = self._truncate_to_budget(context_parts)
        return truncated

    def _format_case_metadata(self, case: Dict[str, Any]) -> str:
        lines = [
            f"Case: {case.get('case_number', 'Unknown')}",
            f"Title: {case.get('title', 'Unknown')}",
            f"Blockchain: {case.get('blockchain', 'Unknown')}",
            f"Fraud Type: {case.get('fraud_type', 'Unknown')}",
            f"Reported Wallet: {case.get('reported_wallet_address', 'Unknown')}",
            f"Reported Amount: {case.get('reported_amount', 'Unknown')} {case.get('reported_asset', '')}",
            f"Status: {case.get('status', 'Unknown')}",
        ]
        if case.get("investigator_notes"):
            lines.append(f"Investigator Notes: {case['investigator_notes']}")
        return "\n".join(lines)

    def _format_transactions(self, transactions: List[Dict[str, Any]], max_items: int = 20) -> str:
        lines = [f"Transactions ({len(transactions)} total, showing first {min(max_items, len(transactions))}):"]
        for i, tx in enumerate(transactions[:max_items]):
            lines.append(
                f"  {i+1}. {tx.get('transaction_hash', 'Unknown')} | "
                f"{tx.get('from_address', 'Unknown')} -> {tx.get('to_address', 'Unknown')} | "
                f"{tx.get('amount', 'Unknown')} {tx.get('asset_symbol', '')} | "
                f"Hop: {tx.get('discovered_at_hop', 'Unknown')} | "
                f"Block: {tx.get('block_number', 'Unknown')} | "
                f"Type: {tx.get('transaction_type', 'Unknown')}"
            )
        if len(transactions) > max_items:
            lines.append(f"  ... and {len(transactions) - max_items} more transactions")
        return "\n".join(lines)

    def _format_patterns(self, patterns: List[Dict[str, Any]]) -> str:
        lines = [f"Detected Patterns ({len(patterns)} total):"]
        for p in patterns:
            lines.append(
                f"  - {p.get('pattern_type', 'Unknown')} at {p.get('wallet_address', 'Unknown')} "
                f"(confidence: {p.get('confidence', 'Unknown')}): {p.get('description', 'No description')}"
            )
            if p.get("evidence"):
                ev = p["evidence"]
                if ev.get("tx_hashes") or ev.get("transaction_hashes"):
                    txs = ev.get("tx_hashes") or ev.get("transaction_hashes", [])
                    lines.append(f"    Transactions: {', '.join(txs[:5])}")
        return "\n".join(lines)

    def _format_attributions(self, attributions: List[Dict[str, Any]]) -> str:
        lines = [f"VASP/Entity Attributions ({len(attributions)} total):"]
        for a in attributions:
            entity = a.get("entity", {})
            lines.append(
                f"  - {a.get('wallet_address', 'Unknown')} -> "
                f"{entity.get('name', 'Unknown')} ({entity.get('entity_type', 'Unknown')}) | "
                f"Provenance: {a.get('provenance_level', 'Unknown')} | "
                f"Confidence: {a.get('confidence', 'Unknown')} | "
                f"Method: {a.get('attribution_method', 'Unknown')}"
            )
        return "\n".join(lines)

    def _format_risk_factors(self, risk_scores: List[Dict[str, Any]]) -> str:
        lines = [f"Risk Scores ({len(risk_scores)} total):"]
        for r in risk_scores:
            lines.append(
                f"  - {r.get('wallet_address', 'Unknown')}: Score {r.get('score', 'Unknown')}/100 "
                f"({r.get('risk_category', 'Unknown').upper()}) | "
                f"Version: {r.get('scoring_version', 'Unknown')}"
            )
            factors = r.get("factors", [])
            for f in factors:
                if isinstance(f, dict) and f.get("weight", 0) > 0:
                    lines.append(
                        f"    +{f.get('weight', 0)} {f.get('factor_type', 'Unknown').replace('_', ' ').title()}: "
                        f"{f.get('description', 'No description')}"
                    )
        return "\n".join(lines)

    def _format_evidence(self, evidence: List[Dict[str, Any]]) -> str:
        lines = [f"Pinned Evidence ({len(evidence)} total):"]
        for e in evidence:
            lines.append(
                f"  - {e.get('evidence_type', 'Unknown')} ({e.get('reference_id', 'Unknown')}): "
                f"{e.get('investigator_note', 'No note')}"
            )
        return "\n".join(lines)

    def _format_trace_runs(self, trace_runs: List[Dict[str, Any]]) -> str:
        lines = [f"Trace Runs ({len(trace_runs)} total):"]
        for t in trace_runs:
            lines.append(
                f"  - Trace {t.get('trace_id', 'Unknown')}: "
                f"Start={t.get('start_wallet_address', 'Unknown')} | "
                f"Status={t.get('status', 'Unknown')} | "
                f"Hops={t.get('max_hops', 'Unknown')} | "
                f"Summary={t.get('summary', {})}"
            )
        return "\n".join(lines)

    def _format_graph_summary(self, graph: CanonicalGraph) -> str:
        return (
            f"Graph: {graph.node_count} nodes, {graph.edge_count} edges, "
            f"max depth={graph.max_hop_depth}, root={graph.root_wallet_address}"
        )

    def _truncate_to_budget(self, context_parts: Dict[str, str]) -> Dict[str, str]:
        result = {}
        used_tokens = 0
        marker = "\n[TRUNCATED]"
        marker_tokens = self.estimate_tokens(marker)

        for key in self.PRIORITY_ORDER:
            if key not in context_parts:
                continue
            content = context_parts[key]
            tokens = self.estimate_tokens(content)
            if used_tokens + tokens <= self.available_tokens:
                result[key] = content
                used_tokens += tokens
            else:
                remaining = self.available_tokens - used_tokens - marker_tokens
                if remaining > 100:
                    truncated = content[:remaining * 4]
                    result[key] = truncated + marker
                    used_tokens = self.available_tokens
                break

        return result