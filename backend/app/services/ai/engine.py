import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from openai import AsyncOpenAI

from app.config import settings
from app.services.ai.citations import CitationGenerator, Citation
from app.services.ai.context import ContextManager
from app.services.ai.grounding import GroundingLayer
from app.services.ai.safety import HallucinationGuard, InsufficientDataHandler, ResponseType, SafetyCheckResult
from app.services.ai.tools import ToolRegistry, create_tool_registry

logger = logging.getLogger("ledgerlens.ai.copilot")


class CaseNotFoundError(Exception):
    def __init__(self, case_id):
        self.case_id = case_id
        super().__init__(f"Case {case_id} not found")


class ProviderNotConfiguredError(Exception):
    pass


class ProviderError(Exception):
    pass


SYSTEM_PROMPT = """You are the LedgerLens AI Investigation Copilot.

Your role is to assist investigators by answering questions, summarizing cases, and explaining findings — ALL grounded strictly in the provided case data.

CORE RULES:
1. ONLY use information from the provided case context (transactions, patterns, attributions, risk scores, evidence, graph)
2. Every factual claim MUST be supported by a citation to the underlying data
3. Distinguish clearly between:
   - ON-CHAIN FACTS (directly observed blockchain transactions)
   - DERIVED FINDINGS (patterns detected by deterministic algorithms)
   - ATTRIBUTION CLAIMS (entity/VASP matches with confidence levels)
   - RISK ASSESSMENTS (explainable scores with factor breakdowns)
4. NEVER invent transaction hashes, addresses, entities, patterns, or risk values
5. If evidence is insufficient, explicitly say "I don't have sufficient data to answer this" and explain what's missing
6. Use the available tools to retrieve additional data when needed
7. Your responses will be validated against the case data — hallucinations will be caught

CITATION FORMAT:
When referencing data, include inline citations like [Citation: transaction_id=abc, type=transaction] or reference the citation objects provided.

AVAILABLE TOOLS:
- get_case: Retrieve case metadata
- get_graph: Retrieve transaction graph
- get_patterns: Retrieve detected patterns
- get_attributions: Retrieve VASP/entity attributions
- get_risk: Retrieve risk scores with factor breakdowns
- get_evidence: Retrieve investigator-pinned evidence
- get_transactions: Retrieve transactions
- get_trace_runs: Retrieve trace run history

Be precise, professional, and helpful. The investigator relies on your accuracy."""


class CopilotEngine:
    def __init__(self, db):
        self.db = db
        self.grounding = GroundingLayer(db)
        self.tools = create_tool_registry(db)
        self.context_manager = ContextManager()
        self.citation_generator = CitationGenerator()
        self.hallucination_guard = HallucinationGuard()
        self.insufficient_data_handler = InsufficientDataHandler()
        
        if settings.openai_api_key:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        else:
            self.client = None
            logger.warning("OpenAI API key not configured — Copilot will return insufficient-data responses")

    async def ask(
        self,
        case_id: UUID,
        question: str,
        trace_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        context = await self._build_context(case_id, trace_id)

        if not self.client:
            raise ProviderNotConfiguredError("LLM provider not configured")

        missing = self.insufficient_data_handler.check_data_availability(context, ["transactions"])
        if missing:
            return self._insufficient_data_response(
                self.insufficient_data_handler.generate_response(question, missing),
                context
            )

        citations = await self._generate_citations(context)
        tools = self.tools.get_openai_functions()

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": self._format_user_message(question, context, citations)},
        ]

        try:
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=settings.openai_max_tokens,
                temperature=settings.openai_temperature,
            )
        except Exception as e:
            logger.exception("OpenAI API error")
            raise ProviderError(f"LLM service error: {str(e)}") from e

        message = response.choices[0].message
        tool_calls = message.tool_calls

        if tool_calls:
            for tool_call in tool_calls:
                tool_result = await self._execute_tool(tool_call, case_id, trace_id)
                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [{"id": tool_call.id, "type": "function", "function": {"name": tool_call.function.name, "arguments": tool_call.function.arguments}}]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result)
                })
            
            try:
                response = await self.client.chat.completions.create(
                    model=settings.openai_model,
                    messages=messages,
                    max_tokens=settings.openai_max_tokens,
                    temperature=settings.openai_temperature,
                )
                message = response.choices[0].message
            except Exception as e:
                logger.exception("OpenAI API error on follow-up")
                raise ProviderError(f"LLM service error: {str(e)}") from e

        answer = message.content or ""
        
        available_data = self._context_to_available_data(context)
        safety_check = self.hallucination_guard.check_response(answer, available_data)
        if not safety_check.allowed:
            logger.warning(f"Hallucination detected: {safety_check.reason}")
            answer = safety_check.suggested_response or self.insufficient_data_handler.generate_response(question, [])

        used_citations = self._extract_citations_from_answer(answer, citations)
        used_citations = self.citation_generator.filter_valid_citations(used_citations, available_data)

        return {
            "answer": answer,
            "citations": [c.to_dict() for c in used_citations],
            "confidence": 0.95 if used_citations else 0.5,
            "type": ResponseType.ANSWER.value,
        }

    async def summarize(self, case_id: UUID, trace_id: Optional[UUID] = None) -> Dict[str, Any]:
        question = "Provide a comprehensive summary of this investigation case, including the initial reported wallet, key transaction paths, detected patterns, entity attributions, risk assessments, and pinned evidence."
        return await self.ask(case_id, question, trace_id)

    async def explain_risk(self, case_id: UUID, wallet_address: str, trace_id: Optional[UUID] = None) -> Dict[str, Any]:
        question = f"Explain the risk score for wallet {wallet_address}. Break down each contributing factor with its evidence and weight."
        return await self.ask(case_id, question, trace_id)

    async def _build_context(
        self,
        case_id: UUID,
        trace_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        case_data = await self.grounding.get_case(case_id)
        if not case_data:
            raise CaseNotFoundError(case_id)

        trace_id = trace_id or (await self._get_latest_trace_id(case_id))

        graph = await self.grounding.get_graph(case_id, trace_id)
        patterns = await self.grounding.get_patterns(case_id, trace_id)
        attributions = await self.grounding.get_attributions(case_id, trace_id)
        risk_scores = await self.grounding.get_risk_scores(case_id, trace_id)
        evidence = await self.grounding.get_evidence(case_id)
        transactions = await self.grounding.get_transactions(case_id, trace_id, limit=50)
        trace_runs = await self.grounding.get_trace_runs(case_id)

        return {
            "case": case_data,
            "graph": graph,
            "patterns": patterns,
            "attributions": attributions,
            "risk_scores": risk_scores,
            "evidence": evidence,
            "transactions": transactions,
            "trace_runs": trace_runs,
        }

    async def _get_latest_trace_id(self, case_id: UUID) -> Optional[UUID]:
        from app.db.models import TraceRun
        from sqlalchemy import select
        result = await self.db.execute(
            select(TraceRun)
            .where(TraceRun.case_id == case_id)
            .order_by(TraceRun.created_at.desc())
            .limit(1)
        )
        trace = result.scalar_one_or_none()
        return trace.trace_id if trace else None

    def _format_user_message(self, question: str, context: Dict[str, Any], citations: List[Citation]) -> str:
        ctx = self.context_manager.build_context(
            case_data=context.get("case"),
            graph=context.get("graph"),
            patterns=context.get("patterns"),
            attributions=context.get("attributions"),
            risk_scores=context.get("risk_scores"),
            evidence=context.get("evidence"),
            transactions=context.get("transactions"),
            trace_runs=context.get("trace_runs"),
        )
        
        citation_refs = "\n".join([f"[{i}] {c.summary}" for i, c in enumerate(citations)])
        
        return f"""Case Context:
{self._format_context_for_prompt(ctx)}

Available Citations:
{citation_refs}

Question: {question}

Answer using only the above context. Cite sources inline using [0], [1], etc. corresponding to the Available Citations list."""

    def _format_context_for_prompt(self, context: Dict[str, str]) -> str:
        parts = []
        for key, value in context.items():
            if value:
                parts.append(f"=== {key.upper()} ===\n{value}")
        return "\n\n".join(parts)

    async def _generate_citations(self, context: Dict[str, Any]) -> List[Citation]:
        citations = []
        case = context.get("case")
        if case:
            citations.append(self.citation_generator.create_case_citation(case))

        for tx in context.get("transactions", [])[:20]:
            citations.append(self.citation_generator.create_transaction_citation(tx))

        for pattern in context.get("patterns", []):
            citations.append(self.citation_generator.create_pattern_citation(pattern))

        for attr in context.get("attributions", []):
            citations.append(self.citation_generator.create_attribution_citation(attr))

        for risk in context.get("risk_scores", []):
            for factor in risk.get("factors", []):
                if factor.get("weight", 0) > 0:
                    citations.append(self.citation_generator.create_risk_factor_citation(risk, factor.get("factor_type")))

        for ev in context.get("evidence", []):
            citations.append(self.citation_generator.create_evidence_citation(ev))

        return citations

    def _context_to_available_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "case": context.get("case", {}),
            "graph": context.get("graph"),
            "transactions": context.get("transactions", []),
            "patterns": context.get("patterns", []),
            "attributions": context.get("attributions", []),
            "risk_scores": context.get("risk_scores", []),
            "evidence": context.get("evidence", []),
        }

    def _extract_citations_from_answer(self, answer: str, all_citations: List[Citation]) -> List[Citation]:
        import re
        citation_indices = set()
        for match in re.finditer(r'\[(\d+)\]', answer):
            try:
                idx = int(match.group(1))
                if 0 <= idx < len(all_citations):
                    citation_indices.add(idx)
            except ValueError:
                pass
        return [all_citations[i] for i in sorted(citation_indices)]

    async def _execute_tool(self, tool_call, case_id: UUID, trace_id: Optional[UUID]) -> Dict[str, Any]:
        tool_name = tool_call.function.name
        tool = self.tools.get_tool(tool_name)
        if not tool:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            args = json.loads(tool_call.function.arguments)
            args["case_id"] = UUID(case_id) if isinstance(case_id, str) else case_id
            if trace_id:
                args["trace_id"] = UUID(trace_id) if isinstance(trace_id, str) else trace_id
            result = await tool["function"](**args)
            return {"result": result}
        except Exception as e:
            logger.exception(f"Tool {tool_name} execution failed")
            return {"error": str(e)}

    def _insufficient_data_response(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        return {
            "answer": message,
            "citations": [],
            "confidence": 0.0,
            "type": ResponseType.INSUFFICIENT_DATA.value,
        }


def get_copilot_engine(db) -> CopilotEngine:
    return CopilotEngine(db)