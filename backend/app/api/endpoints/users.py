"""
User management endpoints
"""
import logging
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.utils.database import get_db
from app.utils.security import verify_token, require_admin
from app.models import User
from app.models.schemas import (
    UserResponse,
    UserCreateSchema,
    UserUpdateSchema,
    BaseResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def get_users(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Get all users (admin only)"""
    try:
        query = select(User).order_by(User.created_at.desc())
        result = await db.execute(query)
        users = result.scalars().all()
        
        return [UserResponse.from_orm(user) for user in users]
        
    except Exception as e:
        logger.error(f"Failed to get users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Create new user (admin only)"""
    try:
        # Check if user already exists
        existing_query = select(User).where(User.email == user_data.email)
        existing_result = await db.execute(existing_query)
        existing_user = existing_result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create new user
        user = User(
            email=user_data.email,
            role=user_data.role,
            b2c_object_id=user_data.b2c_object_id
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"Created user {user.id} with email {user.email}")
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Get specific user details"""
    try:
        # Users can view their own profile, admins can view any profile
        current_user_id = current_user.get("user_id")
        current_user_role = current_user.get("role")
        
        if current_user_role != "admin" and current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    update_data: UserUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Update user details (admin only)"""
    try:
        # Get user
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        if update_dict:
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(**update_dict)
            )
            await db.commit()
            await db.refresh(user)
        
        logger.info(f"Updated user {user_id} by admin {current_user.get('user_id')}")
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete("/{user_id}", response_model=BaseResponse)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Deactivate user (admin only)"""
    try:
        # Don't actually delete, just deactivate
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=False)
        )
        await db.commit()
        
        logger.info(f"Deactivated user {user_id} by admin {current_user.get('user_id')}")
        
        return BaseResponse(success=True, message="User deactivated successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@router.get("/me/profile", response_model=UserResponse)
async def get_current_user_profile(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Get current user's profile"""
    try:
        user_id = current_user.get("user_id")
        
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )
