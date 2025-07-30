"""
Pydantic schemas for request/response models
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any, Union
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, validator


# Enums
class UserRole(str, Enum):
    END_USER = "end_user"
    SALES = "sales"
    ADMIN = "admin"


class SubmissionStatus(str, Enum):
    NEW = "New"
    CONTACTED = "Contacted"
    IN_NEGOTIATION = "In Negotiation"
    CLOSED_WON = "Closed Won"
    CLOSED_LOST = "Closed Lost"


class CollaborationScope(str, Enum):
    INTERNAL_ONLY = "Internal only"
    EXTERNAL_VIA_SLACK_CONNECT = "External via Slack Connect"
    BOTH = "Both"


class O365License(str, Enum):
    E1 = "E1"
    E3 = "E3"
    E5 = "E5"
    F1 = "F1"
    F3 = "F3"
    BUSINESS_BASIC = "Business Basic"
    BUSINESS_STANDARD = "Business Standard"
    BUSINESS_PREMIUM = "Business Premium"
    NONE = "None"


# Base schemas
class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: Optional[str] = None


# Stakeholder contact schema
class StakeholderContact(BaseModel):
    """Stakeholder contact information"""
    email: EmailStr
    title: str
    phone: str


# Customer Information Schema (Step 1)
class CustomerInfoSchema(BaseModel):
    """Customer information form schema"""
    company_name: str = Field(..., min_length=1, max_length=255)
    contact_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: str = Field(..., min_length=1, max_length=50)
    project_lead: str = Field(..., min_length=1, max_length=255)
    it_contact: str = Field(..., min_length=1, max_length=255)
    rough_budget: float = Field(..., gt=0)
    ideal_timeline: date
    other_stakeholders: str = Field(..., regex="^(yes|no)$")
    stakeholder_contacts: Optional[List[StakeholderContact]] = None
    slack_renewal: str = Field(..., min_length=1)
    slack_cancellation: str = Field(..., min_length=1)
    total_licenses: int = Field(..., gt=0)
    collaboration_scope: CollaborationScope
    support_external_usecases: Optional[str] = Field(None, regex="^(Support in Teams|Continue Slack)$")
    other_collab_tools: List[str] = Field(..., min_items=1)
    
    @validator('stakeholder_contacts')
    def validate_stakeholder_contacts(cls, v, values):
        other_stakeholders = values.get('other_stakeholders')
        if other_stakeholders == 'yes' and (not v or len(v) == 0):
            raise ValueError('Stakeholder contacts required when other_stakeholders is yes')
        return v


# Technical Details Schema (Step 2)
class TechnicalDetailsSchema(BaseModel):
    """Technical details form schema"""
    ad_integration: str = Field(..., regex="^(yes|no)$")
    o365_user_assumption: Optional[str] = Field(None, regex="^(yes|no)$")
    analytics_report_filename: str = Field(..., min_length=1)  # File upload reference
    message_volume: int = Field(..., gt=0, description="Key field for cost calculations")
    migration_criteria: str = Field(..., min_length=1)
    installed_apps: str = Field(..., min_length=1)
    custom_apps: List[str] = Field(..., min_items=1)
    custom_app_details: Optional[str] = None
    third_party_apps: List[str] = Field(..., min_items=1)
    third_party_app_details: Optional[str] = None
    integrations: str = Field(..., min_length=1)
    governance_policy: str = Field(..., min_length=1)
    content_restrictions: str = Field(..., min_length=1)
    enterprise_search: str = Field(..., min_length=1)
    usage_pattern: str = Field(..., min_length=1)
    o365_current_usage: O365License
    slack_canvas_usage: Optional[str] = None
    slack_lists_usage: Optional[str] = None
    
    @validator('o365_user_assumption')
    def validate_o365_assumption(cls, v, values):
        ad_integration = values.get('ad_integration')
        if ad_integration == 'no' and v is None:
            raise ValueError('o365_user_assumption required when ad_integration is no')
        return v


# Complete submission schema
class SubmissionRequestSchema(BaseModel):
    """Complete submission request"""
    customer_info: CustomerInfoSchema
    technical_details: TechnicalDetailsSchema


# Estimate schemas
class EstimateBreakdown(BaseModel):
    """Cost breakdown details"""
    base_cost: Decimal
    additional_tiers: int
    addon_service_cost: Decimal
    data_prep_cost: Decimal
    total_cost: Decimal
    message_volume: int
    
    
class EstimateTimeline(BaseModel):
    """Timeline breakdown"""
    base_weeks: Decimal
    additional_weeks: Decimal
    total_weeks: Decimal


class EstimateResponse(BaseModel):
    """Estimate calculation response"""
    cost: Decimal
    effort_weeks: Decimal
    timeline_weeks: Decimal
    breakdown: EstimateBreakdown
    timeline: EstimateTimeline
    created_at: datetime
    
    class Config:
        from_attributes = True


# Submission schemas
class SubmissionResponse(BaseModel):
    """Submission response model"""
    id: int
    user_id: int
    status: SubmissionStatus
    sales_comments: Optional[str] = None
    cost: Optional[Decimal] = None
    effort_weeks: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SubmissionUpdateSchema(BaseModel):
    """Schema for updating submission by sales"""
    status: Optional[SubmissionStatus] = None
    sales_comments: Optional[str] = None


# User schemas
class UserResponse(BaseModel):
    """User response model"""
    id: int
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserCreateSchema(BaseModel):
    """Schema for creating new user"""
    email: EmailStr
    role: UserRole = UserRole.END_USER
    b2c_object_id: Optional[str] = None


class UserUpdateSchema(BaseModel):
    """Schema for updating user"""
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


# PDF Generation schema
class PDFResponse(BaseModel):
    """PDF generation response"""
    download_url: str
    expires_at: datetime
    file_size: Optional[int] = None


# Audit schemas
class AuditEventSchema(BaseModel):
    """Audit event creation schema"""
    entity: str
    action: str
    entity_id: int
    diff: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogResponse(BaseModel):
    """Audit log response"""
    id: int
    actor_id: int
    timestamp: datetime
    entity: str
    action: str
    entity_id: int
    diff: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    class Config:
        from_attributes = True


# Auth schemas
class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
