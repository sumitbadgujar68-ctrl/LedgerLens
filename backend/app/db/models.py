from sqlalchemy import Column, String, Boolean, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
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
