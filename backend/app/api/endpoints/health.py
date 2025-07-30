"""
Health check endpoints
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.database import get_db
from app.models.schemas import BaseResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=BaseResponse)
async def health_check():
    """Basic health check endpoint"""
    return BaseResponse(success=True, message="Service is healthy")


@router.get("/db", response_model=BaseResponse)
async def database_health_check(db: AsyncSession = Depends(get_db)):
    """Database connectivity health check"""
    try:
        # Simple query to test database connection
        await db.execute("SELECT 1")
        return BaseResponse(success=True, message="Database connection is healthy")
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return BaseResponse(success=False, message="Database connection failed")
