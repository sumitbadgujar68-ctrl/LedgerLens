from sqlalchemy import Column, String, Boolean, DateTime, Text, Numeric, ForeignKey, Integer, BigInteger, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.database import Base

class Investigator(Base):
    __tablename__ = "investigators"
    
    investigator_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    cases = relationship("Case", back_populates="investigator")

class Case(Base):
    __tablename__ = "cases"
    
    case_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_number = Column(String(50), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    reported_wallet_address = Column(String(255), nullable=False, index=True)
    reported_transaction_hash = Column(String(255), nullable=True)
    blockchain = Column(String(50), nullable=False, index=True)
    fraud_type = Column(String(100), nullable=False)
    reported_amount = Column(Numeric(30, 8), nullable=True)
    reported_asset = Column(String(50), nullable=True)
    reported_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="active", index=True)
    investigator_id = Column(UUID(as_uuid=True), ForeignKey("investigators.investigator_id"), nullable=False, index=True)
    investigator_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    investigator = relationship("Investigator", back_populates="cases")


class TraceRun(Base):
    __tablename__ = "trace_runs"

    trace_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False, index=True)
    start_wallet_address = Column(String(255), nullable=False, index=True)
    blockchain = Column(String(50), nullable=False, default="ethereum")
    direction = Column(String(20), nullable=False, default="outbound")
    max_hops = Column(Integer, nullable=False, default=3)
    max_branches = Column(Integer, nullable=False, default=25)
    min_amount = Column(Numeric(78, 18), nullable=True)
    asset_filters = Column(JSONB, nullable=True)
    time_range_start = Column(DateTime(timezone=True), nullable=True)
    time_range_end = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="pending", index=True)
    result_status = Column(String(50), nullable=True)
    provider = Column(String(50), nullable=True)
    summary = Column(JSONB, nullable=True, default={})
    errors = Column(JSONB, nullable=True, default=[])
    parameters = Column(JSONB, nullable=True, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    transactions = relationship("TransactionRecord", back_populates="trace_run", foreign_keys="TransactionRecord.trace_id")
    graph = relationship("GraphRecord", back_populates="trace_run", uselist=False, foreign_keys="GraphRecord.trace_id")


class GraphRecord(Base):
    __tablename__ = "graphs"

    graph_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False, index=True)
    trace_id = Column(UUID(as_uuid=True), ForeignKey("trace_runs.trace_id", ondelete="CASCADE"), nullable=True, index=True)
    root_wallet_address = Column(String(255), nullable=False)
    blockchain = Column(String(50), nullable=False, default="ethereum")
    max_hop_depth = Column(Integer, nullable=False, default=0)
    branch_limit = Column(Integer, nullable=True)
    dust_threshold = Column(Numeric(78, 18), nullable=True)
    time_window_start = Column(DateTime(timezone=True), nullable=True)
    time_window_end = Column(DateTime(timezone=True), nullable=True)
    node_count = Column(Integer, nullable=True, default=0)
    edge_count = Column(Integer, nullable=True, default=0)
    graph_data = Column(JSONB, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    trace_run = relationship("TraceRun", back_populates="graph", foreign_keys=[trace_id])


class TransactionRecord(Base):
    __tablename__ = "transactions"

    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False, index=True)
    trace_id = Column(UUID(as_uuid=True), ForeignKey("trace_runs.trace_id", ondelete="SET NULL"), nullable=True, index=True)
    transaction_hash = Column(String(255), nullable=False, index=True)
    blockchain = Column(String(50), nullable=False, index=True)
    block_number = Column(BigInteger, nullable=True)
    block_timestamp = Column(DateTime(timezone=True), nullable=True)
    from_address = Column(String(255), nullable=False, index=True)
    to_address = Column(String(255), nullable=True, index=True)
    asset_symbol = Column(String(50), nullable=True, index=True)
    asset_type = Column(String(50), nullable=True)
    amount = Column(Numeric(78, 18), nullable=False, default=0, index=True)
    decimals = Column(Integer, nullable=False, default=18)
    token_contract_address = Column(String(255), nullable=True)
    transfer_category = Column(String(50), nullable=True)
    transaction_type = Column(String(50), nullable=False, default="transfer")
    status = Column(String(50), nullable=False, default="unknown")
    gas_used = Column(BigInteger, nullable=True)
    max_fee_per_gas = Column(Numeric(78, 18), nullable=True)
    priority_fee_per_gas = Column(Numeric(78, 18), nullable=True)
    total_fee = Column(Numeric(78, 18), nullable=True)
    provider_source = Column(String(100), nullable=False)
    provider_reference = Column(String(512), nullable=False)
    raw_reference = Column(Text, nullable=True)
    discovered_at_hop = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    trace_run = relationship("TraceRun", back_populates="transactions", foreign_keys=[trace_id])

