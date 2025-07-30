"""
Audit logging endpoints
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.utils.database import get_db
from app.utils.security import verify_token, require_admin
from app.models import AuditLog, User
from app.models.schemas import (
    AuditEventSchema,
    AuditLogResponse,
    BaseResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=BaseResponse)
async def log_audit_event(
    audit_data: AuditEventSchema,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Log audit event for compliance"""
    try:
        audit_log = AuditLog(
            actor_id=current_user.get("user_id"),
            entity=audit_data.entity,
            action=audit_data.action,
            entity_id=audit_data.entity_id,
            diff=audit_data.diff,
            ip_address=audit_data.ip_address,
            user_agent=audit_data.user_agent
        )
        
        db.add(audit_log)
        await db.commit()
        
        logger.info(
            f"Audit log created: User {current_user.get('user_id')} "
            f"{audit_data.action} {audit_data.entity} {audit_data.entity_id}"
        )
        
        return BaseResponse(success=True, message="Audit event logged successfully")
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to log audit event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log audit event"
        )


@router.get("/", response_model=List[AuditLogResponse])
async def get_audit_logs(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_admin),
    entity: Optional[str] = Query(None, description="Filter by entity type"),
    action: Optional[str] = Query(None, description="Filter by action"),
    entity_id: Optional[int] = Query(None, description="Filter by entity ID"),
    actor_id: Optional[int] = Query(None, description="Filter by actor ID"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return")
):
    """Get audit logs with filtering (admin only)"""
    try:
        query = select(AuditLog).order_by(AuditLog.timestamp.desc())
        
        # Apply filters
        if entity:
            query = query.where(AuditLog.entity == entity)
        
        if action:
            query = query.where(AuditLog.action == action)
        
        if entity_id:
            query = query.where(AuditLog.entity_id == entity_id)
        
        if actor_id:
            query = query.where(AuditLog.actor_id == actor_id)
        
        if start_date:
            query = query.where(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.where(AuditLog.timestamp <= end_date)
        
        # Apply limit
        query = query.limit(limit)
        
        result = await db.execute(query)
        audit_logs = result.scalars().all()
        
        return [AuditLogResponse.from_orm(log) for log in audit_logs]
        
    except Exception as e:
        logger.error(f"Failed to get audit logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        )


@router.get("/entity/{entity_type}/{entity_id}", response_model=List[AuditLogResponse])
async def get_entity_audit_trail(
    entity_type: str,
    entity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Get complete audit trail for a specific entity"""
    try:
        query = select(AuditLog).where(
            AuditLog.entity == entity_type,
            AuditLog.entity_id == entity_id
        ).order_by(AuditLog.timestamp.desc())
        
        result = await db.execute(query)
        audit_logs = result.scalars().all()
        
        return [AuditLogResponse.from_orm(log) for log in audit_logs]
        
    except Exception as e:
        logger.error(f"Failed to get audit trail for {entity_type} {entity_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit trail"
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_audit_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_admin),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """Get audit statistics for the last N days"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get total count
        total_query = select(AuditLog).where(AuditLog.timestamp >= start_date)
        total_result = await db.execute(total_query)
        total_logs = len(total_result.scalars().all())
        
        # Get action breakdown
        action_query = select(AuditLog.action).where(AuditLog.timestamp >= start_date)
        action_result = await db.execute(action_query)
        actions = action_result.scalars().all()
        
        action_counts = {}
        for action in actions:
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # Get entity breakdown
        entity_query = select(AuditLog.entity).where(AuditLog.timestamp >= start_date)
        entity_result = await db.execute(entity_query)
        entities = entity_result.scalars().all()
        
        entity_counts = {}
        for entity in entities:
            entity_counts[entity] = entity_counts.get(entity, 0) + 1
        
        return {
            "period_days": days,
            "total_events": total_logs,
            "actions": action_counts,
            "entities": entity_counts,
            "start_date": start_date,
            "end_date": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to get audit stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit statistics"
        )
