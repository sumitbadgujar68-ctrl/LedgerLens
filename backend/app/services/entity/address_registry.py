from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EntityAddress, Entity


class AddressRegistry:
    """Service for looking up entity information by blockchain address."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_entity_by_address(
        self, blockchain: str, address: str
    ) -> EntityAddress | None:
        """
        Look up an entity address record by blockchain and address.
        Returns the EntityAddress record if found, else None.
        """
        stmt = (
            select(EntityAddress)
            .where(EntityAddress.blockchain == blockchain)
            .where(EntityAddress.address == address)
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_entity_by_id(self, entity_id: str) -> Entity | None:
        """
        Look up an entity by its ID.
        Returns the Entity record if found, else None.
        """
        stmt = select(Entity).where(Entity.entity_id == entity_id)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_entity_info(
        self, blockchain: str, address: str
    ) -> tuple[Entity, EntityAddress] | None:
        """
        Get both the Entity and EntityAddress for a given blockchain and address.
        Returns (Entity, EntityAddress) if found, else None.
        """
        entity_address = await self.get_entity_by_address(blockchain, address)
        if entity_address is None:
            return None

        entity = await self.get_entity_by_id(str(entity_address.entity_id))
        if entity is None:
            # This should not happen if the database is consistent
            return None

        return entity, entity_address