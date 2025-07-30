"""
Cost and effort estimation service
Implements the precise algorithms from the specification
"""
import math
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any
from datetime import datetime

from app.models.schemas import TechnicalDetailsSchema, EstimateBreakdown, EstimateTimeline

logger = logging.getLogger(__name__)

# Base pricing constants
BASE_COST = Decimal('35000.00')
BASE_WEEKS = Decimal('8.0')
TIER_SIZE = 3_000_000  # 3 million messages per tier

# Add-on service pricing (per week)
ADDON_SERVICES = {
    "hypercare_support": Decimal('4000.00'),
    "adoption_change_management": Decimal('2000.00'),
    "application_integration_dev": Decimal('4000.00')
}


class EstimationService:
    """Service for calculating migration costs and effort estimates"""
    
    @staticmethod
    def calculate_total_cost(message_volume: int) -> Dict[str, Any]:
        """
        Calculate total migration cost based on message volume tiers
        
        Baseline (first 3 million messages): $35,000
        Each additional 3 million-message tier:
        - Data preparation: $500
        - Migration execution: $6,000
        
        Args:
            message_volume: Total number of messages to migrate
            
        Returns:
            Dict with cost breakdown details
        """
        logger.info(f"Calculating cost for {message_volume:,} messages")
        
        if message_volume <= 0:
            raise ValueError("Message volume must be positive")
        
        base_cost = BASE_COST
        
        if message_volume <= TIER_SIZE:
            # Within base tier
            return {
                "base_cost": base_cost,
                "additional_tiers": 0,
                "addon_service_cost": Decimal('0.00'),
                "data_prep_cost": Decimal('0.00'),
                "total_cost": base_cost,
                "message_volume": message_volume
            }
        
        # Calculate additional tiers beyond first 3M
        excess = message_volume - TIER_SIZE
        additional_tiers = math.ceil(excess / TIER_SIZE)
        
        # Cost per additional tier
        addon_service_cost = Decimal('6000.00') * additional_tiers  # Migration execution
        data_prep_cost = Decimal('500.00') * additional_tiers       # Data preparation
        
        total_cost = base_cost + addon_service_cost + data_prep_cost
        
        logger.info(
            f"Cost calculation: Base=${base_cost}, "
            f"Additional tiers={additional_tiers}, "
            f"Addon=${addon_service_cost}, "
            f"Data prep=${data_prep_cost}, "
            f"Total=${total_cost}"
        )
        
        return {
            "base_cost": base_cost,
            "additional_tiers": additional_tiers,
            "addon_service_cost": addon_service_cost,
            "data_prep_cost": data_prep_cost,
            "total_cost": total_cost,
            "message_volume": message_volume
        }
    
    @staticmethod
    def calculate_effort_weeks(message_volume: int) -> Dict[str, Any]:
        """
        Calculate effort in weeks based on message volume
        
        Baseline (first 3 million messages): 8 weeks
        Each additional 3 million messages: +1 week
        
        Args:
            message_volume: Total number of messages to migrate
            
        Returns:
            Dict with timeline breakdown details
        """
        logger.info(f"Calculating effort for {message_volume:,} messages")
        
        if message_volume <= 0:
            raise ValueError("Message volume must be positive")
        
        base_weeks = BASE_WEEKS
        
        if message_volume <= TIER_SIZE:
            # Within base tier
            return {
                "base_weeks": base_weeks,
                "additional_weeks": Decimal('0.0'),
                "total_weeks": base_weeks
            }
        
        # Calculate additional weeks for excess messages
        excess = message_volume - TIER_SIZE
        additional_tiers = math.ceil(excess / TIER_SIZE)
        additional_weeks = Decimal(str(additional_tiers))
        
        total_weeks = base_weeks + additional_weeks
        
        logger.info(
            f"Effort calculation: Base={base_weeks} weeks, "
            f"Additional={additional_weeks} weeks, "
            f"Total={total_weeks} weeks"
        )
        
        return {
            "base_weeks": base_weeks,
            "additional_weeks": additional_weeks,
            "total_weeks": total_weeks
        }
    
    @classmethod
    def calculate_estimate(cls, technical_details: TechnicalDetailsSchema) -> Dict[str, Any]:
        """
        Calculate complete estimate for a submission
        
        Args:
            technical_details: Technical details from form submission
            
        Returns:
            Complete estimate with cost and timeline breakdowns
        """
        message_volume = technical_details.message_volume
        
        try:
            # Calculate cost breakdown
            cost_breakdown = cls.calculate_total_cost(message_volume)
            
            # Calculate effort timeline
            timeline_breakdown = cls.calculate_effort_weeks(message_volume)
            
            # Create response objects
            breakdown = EstimateBreakdown(
                base_cost=cost_breakdown["base_cost"],
                additional_tiers=cost_breakdown["additional_tiers"],
                addon_service_cost=cost_breakdown["addon_service_cost"],
                data_prep_cost=cost_breakdown["data_prep_cost"],
                total_cost=cost_breakdown["total_cost"],
                message_volume=cost_breakdown["message_volume"]
            )
            
            timeline = EstimateTimeline(
                base_weeks=timeline_breakdown["base_weeks"],
                additional_weeks=timeline_breakdown["additional_weeks"],
                total_weeks=timeline_breakdown["total_weeks"]
            )
            
            result = {
                "cost": cost_breakdown["total_cost"],
                "effort_weeks": timeline_breakdown["total_weeks"],
                "timeline_weeks": timeline_breakdown["total_weeks"],
                "breakdown": breakdown,
                "timeline": timeline,
                "created_at": datetime.utcnow()
            }
            
            logger.info(
                f"Estimate completed: {message_volume:,} messages -> "
                f"${result['cost']} over {result['effort_weeks']} weeks"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate estimate: {str(e)}")
            raise
    
    @staticmethod
    def get_addon_service_pricing() -> Dict[str, Decimal]:
        """Get add-on service pricing per week"""
        return ADDON_SERVICES.copy()
    
    @staticmethod
    def calculate_addon_cost(service_name: str, weeks: int) -> Decimal:
        """
        Calculate cost for optional add-on service
        
        Args:
            service_name: Name of the add-on service
            weeks: Number of weeks the service is needed
            
        Returns:
            Total cost for the add-on service
        """
        if service_name not in ADDON_SERVICES:
            raise ValueError(f"Unknown add-on service: {service_name}")
        
        if weeks <= 0:
            raise ValueError("Weeks must be positive")
        
        weekly_rate = ADDON_SERVICES[service_name]
        total_cost = weekly_rate * weeks
        
        logger.info(f"Add-on {service_name}: {weeks} weeks @ ${weekly_rate}/week = ${total_cost}")
        
        return total_cost
