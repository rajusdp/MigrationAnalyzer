"""
API routes configuration
"""
from fastapi import APIRouter

from app.api.endpoints import estimate, submissions, users, audit, health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(estimate.router, prefix="/estimate", tags=["estimates"])
api_router.include_router(submissions.router, prefix="/submissions", tags=["submissions"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
