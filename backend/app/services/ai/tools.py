from typing import Any, Callable, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai.grounding import GroundingLayer


class ToolRegistry:
    def __init__(self, db: AsyncSession):
        self.grounding = GroundingLayer(db)
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, description: str, func: Callable, parameters: Dict[str, Any]) -> None:
        self._tools[name] = {
            "name": name,
            "description": description,
            "function": func,
            "parameters": parameters,
        }

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": name,
                "description": tool["description"],
                "parameters": tool["parameters"],
            }
            for name, tool in self._tools.items()
        ]

    def get_openai_functions(self) -> List[Dict[str, Any]]:
        functions = []
        for name, tool in self._tools.items():
            functions.append({
                "name": name,
                "description": tool["description"],
                "parameters": tool["parameters"],
            })
        return functions


def create_tool_registry(db: AsyncSession) -> ToolRegistry:
    registry = ToolRegistry(db)
    grounding = registry.grounding

    registry.register(
        name="get_case",
        description="Retrieve case metadata by case ID",
        func=grounding.get_case,
        parameters={
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "format": "uuid", "description": "Case UUID"}
            },
            "required": ["case_id"],
        },
    )

    registry.register(
        name="get_graph",
        description="Retrieve the canonical transaction graph for a case or trace",
        func=grounding.get_graph,
        parameters={
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "format": "uuid", "description": "Case UUID"},
                "trace_id": {"type": "string", "format": "uuid", "description": "Optional trace UUID"}
            },
            "required": ["case_id"],
        },
    )

    registry.register(
        name="get_patterns",
        description="Retrieve detected patterns for a case, optionally filtered by trace or wallet",
        func=grounding.get_patterns,
        parameters={
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "format": "uuid", "description": "Case UUID"},
                "trace_id": {"type": "string", "format": "uuid", "description": "Optional trace UUID"},
                "wallet_address": {"type": "string", "description": "Optional wallet address to filter"}
            },
            "required": ["case_id"],
        },
    )

    registry.register(
        name="get_attributions",
        description="Retrieve VASP/entity attributions for a case, optionally filtered by trace or wallet",
        func=grounding.get_attributions,
        parameters={
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "format": "uuid", "description": "Case UUID"},
                "trace_id": {"type": "string", "format": "uuid", "description": "Optional trace UUID"},
                "wallet_address": {"type": "string", "description": "Optional wallet address to filter"}
            },
            "required": ["case_id"],
        },
    )

    registry.register(
        name="get_risk",
        description="Retrieve risk scores for a case, optionally filtered by trace or wallet",
        func=grounding.get_risk_scores,
        parameters={
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "format": "uuid", "description": "Case UUID"},
                "trace_id": {"type": "string", "format": "uuid", "description": "Optional trace UUID"},
                "wallet_address": {"type": "string", "description": "Optional wallet address to filter"}
            },
            "required": ["case_id"],
        },
    )

    registry.register(
        name="get_evidence",
        description="Retrieve investigator-pinned evidence for a case",
        func=grounding.get_evidence,
        parameters={
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "format": "uuid", "description": "Case UUID"}
            },
            "required": ["case_id"],
        },
    )

    registry.register(
        name="get_transactions",
        description="Retrieve transactions for a case, optionally filtered by trace",
        func=grounding.get_transactions,
        parameters={
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "format": "uuid", "description": "Case UUID"},
                "trace_id": {"type": "string", "format": "uuid", "description": "Optional trace UUID"},
                "limit": {"type": "integer", "description": "Maximum number of transactions", "default": 100}
            },
            "required": ["case_id"],
        },
    )

    registry.register(
        name="get_trace_runs",
        description="Retrieve all trace runs for a case",
        func=grounding.get_trace_runs,
        parameters={
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "format": "uuid", "description": "Case UUID"}
            },
            "required": ["case_id"],
        },
    )

    return registry