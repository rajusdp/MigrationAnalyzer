"""
Database models
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Text, DECIMAL, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.utils.database import Base


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(String(50), nullable=False, default="end_user")  # end_user, sales, admin
    b2c_object_id = Column(String(255), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    submissions = relationship("Submission", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="actor")


class Submission(Base):
    """Submission model"""
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="New")  # New, Contacted, In Negotiation, Closed Won, Closed Lost
    sales_comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="submissions")
    answers = relationship("Answer", back_populates="submission", cascade="all, delete-orphan")
    estimate = relationship("Estimate", back_populates="submission", uselist=False)


class Answer(Base):
    """Form answers model - flexible JSONB storage"""
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    field_key = Column(String(100), nullable=False)
    value = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    submission = relationship("Submission", back_populates="answers")


class Estimate(Base):
    """Cost and effort estimates model"""
    __tablename__ = "estimates"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), unique=True, nullable=False)
    cost = Column(DECIMAL(12, 2), nullable=False)
    effort_weeks = Column(DECIMAL(4, 1), nullable=False)
    timeline_json = Column(JSON, nullable=True)  # Detailed timeline breakdown
    breakdown_json = Column(JSON, nullable=True)  # Cost breakdown details
    pdf_blob_url = Column(Text, nullable=True)  # Azure Blob Storage URL
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    submission = relationship("Submission", back_populates="estimate")


class AuditLog(Base):
    """Audit trail model for compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    entity = Column(String(100), nullable=False)  # submission, user, estimate
    action = Column(String(50), nullable=False)   # create, update, delete, view
    entity_id = Column(Integer, nullable=False)
    diff = Column(JSON, nullable=False)           # Changes made
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    actor = relationship("User", back_populates="audit_logs")
