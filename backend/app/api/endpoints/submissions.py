"""
Submission management endpoints
"""
import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.utils.database import get_db
from app.utils.security import verify_token, require_role
from app.models import User, Submission, Answer, Estimate
from app.models.schemas import (
    SubmissionRequestSchema,
    SubmissionResponse,
    SubmissionUpdateSchema,
    EstimateResponse,
    PDFResponse,
    BaseResponse
)
from app.services.estimation import EstimationService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=SubmissionResponse)
async def create_submission(
    submission_data: SubmissionRequestSchema,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Create a new submission with form data and calculate estimate"""
    try:
        user_id = current_user.get("user_id")
        
        # Create submission record
        submission = Submission(user_id=user_id)
        db.add(submission)
        await db.flush()  # Get submission ID
        
        # Store form answers
        customer_info = submission_data.customer_info.dict()
        technical_details = submission_data.technical_details.dict()
        
        # Store customer info answers
        for field_key, value in customer_info.items():
            answer = Answer(
                submission_id=submission.id,
                field_key=f"customer_info.{field_key}",
                value=value
            )
            db.add(answer)
        
        # Store technical details answers
        for field_key, value in technical_details.items():
            answer = Answer(
                submission_id=submission.id,
                field_key=f"technical_details.{field_key}",
                value=value
            )
            db.add(answer)
        
        # Calculate estimate
        estimate_result = EstimationService.calculate_estimate(
            submission_data.technical_details
        )
        
        # Store estimate
        estimate = Estimate(
            submission_id=submission.id,
            cost=estimate_result["cost"],
            effort_weeks=estimate_result["effort_weeks"],
            timeline_json=estimate_result["timeline"].dict(),
            breakdown_json=estimate_result["breakdown"].dict()
        )
        db.add(estimate)
        
        await db.commit()
        await db.refresh(submission)
        
        logger.info(f"Created submission {submission.id} for user {user_id}")
        
        return SubmissionResponse.from_orm(submission)
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create submission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create submission"
        )


@router.get("/", response_model=List[SubmissionResponse])
async def get_submissions(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_token),
    status_filter: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """Get submissions based on user role"""
    try:
        user_role = current_user.get("role")
        user_id = current_user.get("user_id")
        
        query = select(Submission).options(selectinload(Submission.estimate))
        
        # Filter based on user role
        if user_role == "end_user":
            # End users can only see their own submissions
            query = query.where(Submission.user_id == user_id)
        elif user_role == "sales":
            # Sales can see all submissions
            pass
        elif user_role == "admin":
            # Admins can see all submissions
            pass
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user role"
            )
        
        # Apply status filter if provided
        if status_filter:
            query = query.where(Submission.status == status_filter)
        
        # Apply limit and ordering
        query = query.order_by(Submission.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        submissions = result.scalars().all()
        
        return [SubmissionResponse.from_orm(sub) for sub in submissions]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get submissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve submissions"
        )


@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Get specific submission details"""
    try:
        query = select(Submission).options(
            selectinload(Submission.estimate),
            selectinload(Submission.answers)
        ).where(Submission.id == submission_id)
        
        result = await db.execute(query)
        submission = result.scalar_one_or_none()
        
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )
        
        # Check access permissions
        user_role = current_user.get("role")
        user_id = current_user.get("user_id")
        
        if user_role == "end_user" and submission.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return SubmissionResponse.from_orm(submission)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get submission {submission_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve submission"
        )


@router.put("/{submission_id}", response_model=SubmissionResponse)
async def update_submission(
    submission_id: int,
    update_data: SubmissionUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("sales"))
):
    """Update submission (sales and admin only)"""
    try:
        # Get submission
        query = select(Submission).where(Submission.id == submission_id)
        result = await db.execute(query)
        submission = result.scalar_one_or_none()
        
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        if update_dict:
            await db.execute(
                update(Submission)
                .where(Submission.id == submission_id)
                .values(**update_dict)
            )
            await db.commit()
            await db.refresh(submission)
        
        logger.info(f"Updated submission {submission_id} by user {current_user.get('user_id')}")
        
        return SubmissionResponse.from_orm(submission)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update submission {submission_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update submission"
        )


@router.get("/{submission_id}/estimate", response_model=EstimateResponse)
async def get_submission_estimate(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Get estimate for specific submission"""
    try:
        query = select(Estimate).where(Estimate.submission_id == submission_id)
        result = await db.execute(query)
        estimate = result.scalar_one_or_none()
        
        if not estimate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Estimate not found"
            )
        
        # Check access permissions (same as submission access)
        submission_query = select(Submission).where(Submission.id == submission_id)
        submission_result = await db.execute(submission_query)
        submission = submission_result.scalar_one_or_none()
        
        user_role = current_user.get("role")
        user_id = current_user.get("user_id")
        
        if user_role == "end_user" and submission.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return EstimateResponse.from_orm(estimate)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get estimate for submission {submission_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve estimate"
        )


@router.post("/{submission_id}/pdf", response_model=PDFResponse)
async def generate_pdf_report(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Generate PDF report for submission"""
    try:
        # Check if submission exists and user has access
        submission_query = select(Submission).options(
            selectinload(Submission.estimate),
            selectinload(Submission.answers)
        ).where(Submission.id == submission_id)
        
        result = await db.execute(submission_query)
        submission = result.scalar_one_or_none()
        
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )
        
        # Check access permissions
        user_role = current_user.get("role")
        user_id = current_user.get("user_id")
        
        if user_role == "end_user" and submission.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # TODO: Implement PDF generation service
        # For now, return a placeholder response
        from datetime import datetime, timedelta
        
        return PDFResponse(
            download_url=f"https://example.blob.core.windows.net/reports/submission_{submission_id}.pdf",
            expires_at=datetime.utcnow() + timedelta(hours=24),
            file_size=1024000
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate PDF for submission {submission_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PDF report"
        )
