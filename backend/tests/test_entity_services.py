from unittest.mock import AsyncMock, MagicMock
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.db.models import Entity, EntityAddress, VaspAttributionRecord
from app.services.entity.address_registry import AddressRegistry
from app.services.entity.attribution_engine import AttributionEngine


@pytest.fixture
def mock_db_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def sample_entity():
    return Entity(
        entity_id=uuid4(),
        name="Binance",
        entity_type="exchange",
        jurisdiction="International",
        website="https://binance.com",
        verification_level="verified",
    )


@pytest.fixture
def sample_entity_address(sample_entity):
    return EntityAddress(
        address_id=uuid4(),
        entity_id=sample_entity.entity_id,
        blockchain="ethereum",
        address="0x28c6c06298d514db089934071355e5743bf21d60",
        label="Binance 14 (Hot Wallet)",
        category="exchange_hot_wallet",
        source="etherscan_verified",
        source_url="https://etherscan.io/accounts/label/binance",
        confidence=1.0,
    )


@pytest.mark.asyncio
async def test_address_registry_get_entity_by_address_found(
    mock_db_session, sample_entity, sample_entity_address
):
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_entity_address
    mock_db_session.execute.return_value = mock_result

    registry = AddressRegistry(mock_db_session)

    # Act
    result = await registry.get_entity_by_address(
        "ethereum", "0x28c6c06298d514db089934071355e5743bf21d60"
    )

    # Assert
    assert result == sample_entity_address
    mock_db_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_address_registry_get_entity_by_address_not_found(
    mock_db_session,
):
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    registry = AddressRegistry(mock_db_session)

    # Act
    result = await registry.get_entity_by_address(
        "ethereum", "0x0000000000000000000000000000000000000000"
    )

    # Assert
    assert result is None
    mock_db_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_address_registry_get_entity_by_id_found(
    mock_db_session, sample_entity
):
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_entity
    mock_db_session.execute.return_value = mock_result

    registry = AddressRegistry(mock_db_session)

    # Act
    result = await registry.get_entity_by_id(str(sample_entity.entity_id))

    # Assert
    assert result == sample_entity
    mock_db_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_address_registry_get_entity_by_id_not_found(
    mock_db_session,
):
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    registry = AddressRegistry(mock_db_session)

    # Act
    result = await registry.get_entity_by_id(str(uuid4()))

    # Assert
    assert result is None
    mock_db_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_address_registry_get_entity_info_found(
    mock_db_session, sample_entity, sample_entity_address
):
    # Arrange
    # Mock the two calls: first for EntityAddress, then for Entity
    mock_result_address = MagicMock()
    mock_result_address.scalar_one_or_none.return_value = sample_entity_address
    mock_result_entity = MagicMock()
    mock_result_entity.scalar_one_or_none.return_value = sample_entity

    # We need to mock the execute method to return different results on consecutive calls
    mock_db_session.execute.side_effect = [
        mock_result_address,
        mock_result_entity,
    ]

    registry = AddressRegistry(mock_db_session)

    # Act
    result = await registry.get_entity_info(
        "ethereum", "0x28c6c06298d514db089934071355e5743bf21d60"
    )

    # Assert
    assert result == (sample_entity, sample_entity_address)
    assert mock_db_session.execute.call_count == 2


@pytest.mark.asyncio
async def test_address_registry_get_entity_info_address_not_found(
    mock_db_session,
):
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    registry = AddressRegistry(mock_db_session)

    # Act
    result = await registry.get_entity_info(
        "ethereum", "0x0000000000000000000000000000000000000000"
    )

    # Assert
    assert result is None
    mock_db_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_attribution_engine_attribute_address_found(
    mock_db_session, sample_entity, sample_entity_address
):
    # Arrange
    case_id = uuid4()
    trace_id = uuid4()
    wallet_address = "0x28c6c06298d514db089934071355e5743bf21d60"
    blockchain = "ethereum"

    # Mock the address registry's get_entity_by_address to return our sample
    mock_address_result = MagicMock()
    mock_address_result.scalar_one_or_none.return_value = sample_entity_address

    # Mock the address registry's get_entity_by_id to return our sample entity
    mock_entity_result = MagicMock()
    mock_entity_result.scalar_one_or_none.return_value = sample_entity

    mock_db_session.execute.side_effect = [
        mock_address_result,  # for get_entity_by_address
        mock_entity_result,   # for get_entity_by_id
    ]

    attribution_engine = AttributionEngine(mock_db_session)

    # Act
    result = await attribution_engine.attribute_address(
        wallet_address, blockchain, case_id, trace_id
    )

    # Assert
    assert result is not None
    assert isinstance(result, VaspAttributionRecord)
    assert result.wallet_address == wallet_address
    assert result.case_id == case_id
    assert result.trace_id == trace_id
    assert result.candidate_entity_id == sample_entity_address.entity_id
    assert result.provenance_level == "DIRECT"
    assert result.attribution_method == "registry_exact_match"
    assert result.confidence == sample_entity_address.confidence
    assert result.source == sample_entity_address.source
    assert result.evidence["match_type"] == "exact"
    assert result.evidence["entity_name"] == sample_entity.name

    # Verify that the execute method was called twice
    assert mock_db_session.execute.call_count == 2


@pytest.mark.asyncio
async def test_attribution_engine_attribute_address_not_found(
    mock_db_session,
):
    # Arrange
    case_id = uuid4()
    trace_id = uuid4()
    wallet_address = "0x0000000000000000000000000000000000000000"
    blockchain = "ethereum"

    # Mock the address registry's get_entity_by_address to return None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    attribution_engine = AttributionEngine(mock_db_session)

    # Act
    result = await attribution_engine.attribute_address(
        wallet_address, blockchain, case_id, trace_id
    )

    # Assert
    assert result is None
    mock_db_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_attribution_engine_persist_attribution(
    mock_db_session,
):
    # Arrange
    attribution = VaspAttributionRecord(
        case_id=uuid4(),
        trace_id=uuid4(),
        wallet_address="0x28c6c06298d514db089934071355e5743bf21d60",
        candidate_entity_id=uuid4(),
        provenance_level="DIRECT",
        confidence=1.0,
        attribution_method="registry_exact_match",
        evidence={},
        source="etherscan_verified",
    )

    attribution_engine = AttributionEngine(mock_db_session)

    # Act
    result = await attribution_engine.persist_attribution(attribution)

    # Assert
    assert result == attribution
    mock_db_session.add.assert_called_once_with(attribution)
    mock_db_session.flush.assert_awaited_once()