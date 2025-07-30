"""
Estimate calculation endpoints
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.utils.database import get_db
from app.utils.security import verify_token
from app.services.estimation import EstimationService
from app.models.schemas import (
    SubmissionRequestSchema,
    EstimateResponse,
    BaseResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/", response_model=EstimateResponse)
@limiter.limit("10/minute")
async def calculate_estimate(
    submission_data: SubmissionRequestSchema,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """
    Calculate cost and effort estimates based on submission data
    
    This endpoint uses the precise algorithms defined in the specification:
    - Baseline (first 3 million messages): $35,000, 8 weeks
    - Each additional 3 million messages: +$6,500, +1 week
    """
    try:
        logger.info(
            f"Calculating estimate for user {current_user.get('sub')} "
            f"with {submission_data.technical_details.message_volume:,} messages"
        )
        
        # Calculate estimate using the estimation service
        estimate_result = EstimationService.calculate_estimate(
            submission_data.technical_details
        )
        
        # Return the estimate response
        return EstimateResponse(**estimate_result)
        
    except ValueError as e:
        logger.warning(f"Invalid input for estimation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to calculate estimate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate estimate"
        )


@router.get("/addon-services", response_model=Dict[str, float])
async def get_addon_services():
    """Get available add-on services and their pricing per week"""
    try:
        services = EstimationService.get_addon_service_pricing()
        # Convert Decimal to float for JSON serialization
        return {name: float(price) for name, price in services.items()}
    except Exception as e:
        logger.error(f"Failed to get add-on services: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve add-on services"
        )


@router.post("/addon-cost")
async def calculate_addon_cost(
    service_name: str,
    weeks: int,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Calculate cost for a specific add-on service"""
    try:
        if weeks <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Weeks must be positive"
            )
        
        cost = EstimationService.calculate_addon_cost(service_name, weeks)
        
        return {
            "service_name": service_name,
            "weeks": weeks,
            "weekly_rate": float(EstimationService.get_addon_service_pricing()[service_name]),
            "total_cost": float(cost)
        }
        
    except ValueError as e:
        logger.warning(f"Invalid addon cost calculation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to calculate addon cost: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate addon cost"
        )
