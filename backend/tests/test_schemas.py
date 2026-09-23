import pytest
from app.models.schemas import CaseCreate, CaseUpdate
from datetime import datetime
from decimal import Decimal

def test_case_create_valid():
    case_data = CaseCreate(
        title="Test Case",
        reported_wallet_address="0xABC123",
        blockchain="ethereum",
        fraud_type="investment_scam",
        reported_amount=Decimal("5000.00"),
        reported_asset="USDT"
    )
    assert case_data.title == "Test Case"
    assert case_data.blockchain == "ethereum"

def test_case_create_invalid_blockchain():
    with pytest.raises(ValueError):
        CaseCreate(
            title="Test Case",
            reported_wallet_address="0xABC123",
            blockchain="invalid_chain",
            fraud_type="investment_scam"
        )

def test_case_create_invalid_fraud_type():
    with pytest.raises(ValueError):
        CaseCreate(
            title="Test Case",
            reported_wallet_address="0xABC123",
            blockchain="ethereum",
            fraud_type="invalid_fraud"
        )

def test_case_update_status():
    case_update = CaseUpdate(status="closed")
    assert case_update.status == "closed"

def test_case_update_invalid_status():
    with pytest.raises(ValueError):
        CaseUpdate(status="invalid_status")
