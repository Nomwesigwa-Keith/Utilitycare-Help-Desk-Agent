"""Test script to demonstrate tool functionality.

This script tests both tools independently and through the agent.
"""

import json
from src.tools import get_outage_status, draft_ticket


def test_get_outage_status():
    """Test the get_outage_status tool."""
    print("=" * 60)
    print("Testing get_outage_status tool")
    print("=" * 60)
    
    # Test case 1: Known outage
    print("\nTest 1: Known outage in Ntinda (electricity)")
    result = get_outage_status(area_code="NDA", service_type="electricity")
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test case 2: No outage
    print("\nTest 2: No outage in unknown area")
    result = get_outage_status(area_code="XYZ", service_type="water")
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test case 3: Invalid service type (should raise error)
    print("\nTest 3: Invalid service type (should raise error)")
    try:
        result = get_outage_status(area_code="NDA", service_type="gas")
        print(f"ERROR: Should have raised ValueError, got: {result}")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
    
    # Test case 4: Missing area_code (should raise error)
    print("\nTest 4: Missing area_code (should raise error)")
    try:
        result = get_outage_status(area_code="", service_type="electricity")
        print(f"ERROR: Should have raised ValueError, got: {result}")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")


def test_draft_ticket():
    """Test the draft_ticket tool."""
    print("\n" + "=" * 60)
    print("Testing draft_ticket tool")
    print("=" * 60)
    
    # Test case 1: Valid ticket draft
    print("\nTest 1: Valid ticket draft")
    result = draft_ticket(
        category="power_outage",
        priority="high",
        summary="Power outage in Ntinda since morning",
        customer_area_code="NDA",
        recommended_action="Check outage status first"
    )
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test case 2: Ticket without recommended action
    print("\nTest 2: Ticket without recommended action")
    result = draft_ticket(
        category="billing_query",
        priority="medium",
        summary="Bill higher than usual",
        customer_area_code="KLA"
    )
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test case 3: Invalid category (should raise error)
    print("\nTest 3: Invalid category (should raise error)")
    try:
        result = draft_ticket(
            category="invalid_category",
            priority="medium",
            summary="Test",
            customer_area_code="NDA"
        )
        print(f"ERROR: Should have raised ValueError, got: {result}")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
    
    # Test case 4: Missing required field (should raise error)
    print("\nTest 4: Missing summary (should raise error)")
    try:
        result = draft_ticket(
            category="water_leak",
            priority="high",
            summary="",
            customer_area_code="NDA"
        )
        print(f"ERROR: Should have raised ValueError, got: {result}")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")


def test_tool_orchestration():
    """Test tool orchestration through the orchestrator."""
    print("\n" + "=" * 60)
    print("Testing tool orchestration")
    print("=" * 60)
    
    from src.orchestrator import execute_tool_calls, get_tool_schema
    
    # Show tool schema
    print("\nTool Schema:")
    schema = get_tool_schema()
    print(json.dumps(schema, indent=2))
    
    # Test executing multiple tool calls
    print("\nTest: Execute multiple tool calls")
    tool_calls = [
        {
            "name": "get_outage_status",
            "arguments": {"area_code": "NDA", "service_type": "electricity"}
        },
        {
            "name": "draft_ticket",
            "arguments": {
                "category": "power_outage",
                "priority": "high",
                "summary": "Power outage in Ntinda",
                "customer_area_code": "NDA"
            }
        }
    ]
    
    results = execute_tool_calls(tool_calls)
    print(f"\nResults: {json.dumps(results, indent=2)}")
    
    # Test invalid tool call
    print("\nTest: Invalid tool call (should fail)")
    invalid_calls = [
        {
            "name": "unknown_tool",
            "arguments": {}
        }
    ]
    results = execute_tool_calls(invalid_calls)
    print(f"Results: {json.dumps(results, indent=2)}")


if __name__ == "__main__":
    test_get_outage_status()
    test_draft_ticket()
    test_tool_orchestration()
    
    print("\n" + "=" * 60)
    print("All tool tests completed")
    print("=" * 60)
