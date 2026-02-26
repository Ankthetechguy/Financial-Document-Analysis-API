"""
SQLAlchemy models for financial analysis data
"""
from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from database import Base
import uuid


class AnalysisTask(Base):
    """Model for storing analysis task information"""
    __tablename__ = "analysis_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    query = Column(Text, nullable=False)
    
    # Task status: pending, processing, completed, failed
    status = Column(String(50), default="pending", nullable=False)
    
    # Results
    analysis_result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Task duration in seconds
    duration_seconds = Column(Float, nullable=True)
    
    # Celery task ID for tracking
    celery_task_id = Column(String(255), nullable=True, unique=True)
    
    def __repr__(self):
        return f"<AnalysisTask(id={self.id}, status={self.status}, file={self.file_name})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "file_name": self.file_name,
            "query": self.query,
            "status": self.status,
            "analysis_result": self.analysis_result,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
        }


class UserAnalysisHistory(Base):
    """Model for tracking user analysis history"""
    __tablename__ = "user_analysis_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=True)  # Can be None for anonymous users
    analysis_task_id = Column(String(36), nullable=False)
    
    # Document metadata
    document_name = Column(String(255), nullable=False)
    document_type = Column(String(100), nullable=True)
    document_size = Column(Integer, nullable=True)  # in bytes
    
    # Analysis metadata
    analysis_type = Column(String(100), nullable=False, default="investment")
    key_findings = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<UserAnalysisHistory(id={self.id}, user={self.user_id}, task={self.analysis_task_id})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "analysis_task_id": self.analysis_task_id,
            "document_name": self.document_name,
            "document_type": self.document_type,
            "document_size": self.document_size,
            "analysis_type": self.analysis_type,
            "key_findings": self.key_findings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AnalysisMetrics(Base):
    """Model for storing metrics about analysis performance"""
    __tablename__ = "analysis_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_task_id = Column(String(36), nullable=False)
    
    # Performance metrics
    processing_time_ms = Column(Float, nullable=True)
    document_pages = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    
    # Model information
    model_used = Column(String(100), nullable=True)
    
    # Cost tracking (if applicable)
    estimated_cost_usd = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<AnalysisMetrics(id={self.id}, task={self.analysis_task_id})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "analysis_task_id": self.analysis_task_id,
            "processing_time_ms": self.processing_time_ms,
            "document_pages": self.document_pages,
            "tokens_used": self.tokens_used,
            "model_used": self.model_used,
            "estimated_cost_usd": self.estimated_cost_usd,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
