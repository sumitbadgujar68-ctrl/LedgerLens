from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.models import EntityAddress, Entity, VaspAttributionRecord
from app.services.entity.address_registry import AddressRegistry


class AttributionEngine:
    """Service for attributing blockchain addresses to known entities."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.address_registry = AddressRegistry(db_session)

    async def attribute_address(
        self,
        wallet_address: str,
        blockchain: str,
        case_id: UUID,
        trace_id: UUID,
    ) -> VaspAttributionRecord | None:
        """
        Attribute a blockchain address to a known entity using the address registry.
        Returns a VaspAttributionRecord instance (not yet persisted) if attribution is found,
        otherwise returns None.
        """
        # Step 1: Look up the address in the registry
        entity_address = await self.address_registry.get_entity_by_address(
            blockchain, wallet_address
        )
        if entity_address is None:
            return None

        # Step 2: Get the entity
        entity = await self.address_registry.get_entity_by_id(
            str(entity_address.entity_id)
        )
        if entity is None:
            # This should not happen if the database is consistent
            return None

        # Step 3: Build the attribution record
        attribution = VaspAttributionRecord(
            case_id=case_id,
            trace_id=trace_id,
            wallet_address=wallet_address,
            candidate_entity_id=entity_address.entity_id,
            candidate_entity=entity,
            provenance_level="DIRECT",  # Exact registry match is considered DIRECT
            confidence=entity_address.confidence,
            attribution_method="registry_exact_match",
            evidence={
                "match_type": "exact",
                "address": wallet_address,
                "blockchain": blockchain,
                "entity_address_id": str(entity_address.address_id),
                "entity_id": str(entity_address.entity_id),
                "entity_name": entity.name,
                "label": entity_address.label,
                "category": entity_address.category,
                "source": entity_address.source,
                "source_url": entity_address.source_url,
                "confidence": float(entity_address.confidence),
            },
            source=entity_address.source,
        )
        return attribution

    async def persist_attribution(
        self, attribution: VaspAttributionRecord
    ) -> VaspAttributionRecord:
        """
        Persist an attribution record to the database.
        Returns the persisted attribution record.
        """
        self.db_session.add(attribution)
        await self.db_session.flush()
        return attribution