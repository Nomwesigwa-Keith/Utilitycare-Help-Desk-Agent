"""Tool implementations for the UtilityCare triage agent.

This module defines the two tools specified in the Tool Catalogue:
1. get_outage_status - Read-only retrieval of outage information
2. draft_ticket - Simulated side effect for ticket drafting
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal


@dataclass
class OutageStatusResult:
    """Result from get_outage_status tool."""
    outage_active: bool
    estimated_restoration: str | None
    affected_area_description: str


@dataclass
class TicketDraftResult:
    """Result from draft_ticket tool."""
    draft_id: str
    status: Literal["pending_approval"]
    draft_summary: str


# Mock outage database for simulation
MOCK_OUTAGE_DB = {
    ("NDA", "electricity"): {
        "outage_active": True,
        "estimated_restoration": "2026-09-18T18:00:00+03:00",
        "affected_area_description": "Ntinda and surrounding areas"
    },
    ("KLA", "water"): {
        "outage_active": True,
        "estimated_restoration": "2026-09-18T20:00:00+03:00",
        "affected_area_description": "Central Kampala business district"
    },
}


def get_outage_status(area_code: str, service_type: str) -> dict[str, object]:
    """
    Check whether a known service outage exists for the customer's area.
    
    This is a read-only lookup with no side effects. The agent may call this
    tool autonomously without human approval.
    
    Args:
        area_code: UtilityCare service area identifier (required)
        service_type: One of "electricity" or "water" (required)
    
    Returns:
        Dict with outage_active, estimated_restoration, affected_area_description
    
    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Validation
    if not area_code or not isinstance(area_code, str):
        raise ValueError("area_code is required and must be a string")
    if not service_type or not isinstance(service_type, str):
        raise ValueError("service_type is required and must be a string")
    if service_type not in ("electricity", "water"):
        raise ValueError(f"service_type must be 'electricity' or 'water', got '{service_type}'")
    
    # Simulate service lookup
    key = (area_code.upper(), service_type)
    outage_data = MOCK_OUTAGE_DB.get(key)
    
    if outage_data:
        result = OutageStatusResult(
            outage_active=outage_data["outage_active"],
            estimated_restoration=outage_data["estimated_restoration"],
            affected_area_description=outage_data["affected_area_description"]
        )
    else:
        # No outage found for this area/service
        result = OutageStatusResult(
            outage_active=False,
            estimated_restoration=None,
            affected_area_description=f"No outage reported for area {area_code}"
        )
    
    return {
        "outage_active": result.outage_active,
        "estimated_restoration": result.estimated_restoration,
        "affected_area_description": result.affected_area_description
    }


def draft_ticket(
    category: str,
    priority: str,
    summary: str,
    customer_area_code: str,
    recommended_action: str | None = None
) -> dict[str, object]:
    """
    Prepare a structured support ticket from a triaged issue.
    
    This creates a draft that remains in pending_approval state until
    explicit human action. The agent may draft autonomously but submission
    requires human approval.
    
    Args:
        category: One of power_outage, meter_fault, water_leak, billing_query, other
        priority: One of low, medium, high, urgent
        summary: Summary of the customer's issue
        customer_area_code: Links ticket to customer's service area
        recommended_action: Optional suggested next step for human agent
    
    Returns:
        Dict with draft_id, status (always "pending_approval"), draft_summary
    
    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Validation
    valid_categories = {"power_outage", "meter_fault", "water_leak", "billing_query", "other"}
    valid_priorities = {"low", "medium", "high", "urgent"}
    
    if not category or not isinstance(category, str):
        raise ValueError("category is required and must be a string")
    if category not in valid_categories:
        raise ValueError(f"category must be one of {valid_categories}, got '{category}'")
    
    if not priority or not isinstance(priority, str):
        raise ValueError("priority is required and must be a string")
    if priority not in valid_priorities:
        raise ValueError(f"priority must be one of {valid_priorities}, got '{priority}'")
    
    if not summary or not isinstance(summary, str):
        raise ValueError("summary is required and must be a non-empty string")
    
    if not customer_area_code or not isinstance(customer_area_code, str):
        raise ValueError("customer_area_code is required and must be a string")
    
    # Generate draft ID
    draft_id = f"DRAFT-{uuid.uuid4().hex[:8].upper()}"
    
    # Create draft summary
    draft_summary = (
        f"Category: {category}\n"
        f"Priority: {priority}\n"
        f"Summary: {summary}\n"
        f"Area: {customer_area_code}\n"
        f"Recommended Action: {recommended_action or 'None'}\n"
        f"Created: {datetime.now(timezone.utc).isoformat()}"
    )
    
    result = TicketDraftResult(
        draft_id=draft_id,
        status="pending_approval",
        draft_summary=draft_summary
    )
    
    return {
        "draft_id": result.draft_id,
        "status": result.status,
        "draft_summary": result.draft_summary
    }


# Tool registry for function calling
TOOL_REGISTRY = {
    "get_outage_status": {
        "function": get_outage_status,
        "description": "Check whether a known service outage exists for the customer's area",
        "parameters": {
            "type": "object",
            "properties": {
                "area_code": {
                    "type": "string",
                    "description": "UtilityCare service area identifier"
                },
                "service_type": {
                    "type": "string",
                    "enum": ["electricity", "water"],
                    "description": "Type of service to check"
                }
            },
            "required": ["area_code", "service_type"]
        }
    },
    "draft_ticket": {
        "function": draft_ticket,
        "description": "Prepare a structured support ticket from a triaged issue",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["power_outage", "meter_fault", "water_leak", "billing_query", "other"],
                    "description": "Issue category"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "description": "Ticket priority"
                },
                "summary": {
                    "type": "string",
                    "description": "Summary of the customer's issue"
                },
                "customer_area_code": {
                    "type": "string",
                    "description": "Customer's service area code"
                },
                "recommended_action": {
                    "type": "string",
                    "description": "Optional suggested next step for human agent"
                }
            },
            "required": ["category", "priority", "summary", "customer_area_code"]
        }
    }
}
