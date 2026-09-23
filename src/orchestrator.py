"""Tool calling orchestration layer for the UtilityCare triage agent.

This module manages the execution of tool calls initiated by the model,
including validation, execution, and result handling.
"""

from __future__ import annotations

import json
from typing import Any

from src.tools import TOOL_REGISTRY


class ToolExecutionError(Exception):
    """Raised when a tool execution fails."""
    pass


class ToolValidationError(Exception):
    """Raised when tool input validation fails."""
    pass


def execute_tool_call(tool_name: str, tool_args: dict[str, Any]) -> dict[str, Any]:
    """
    Execute a tool call with validation and error handling.
    
    Args:
        tool_name: Name of the tool to execute
        tool_args: Arguments to pass to the tool
    
    Returns:
        Tool execution result as a dictionary
    
    Raises:
        ToolValidationError: If tool name is invalid or input validation fails
        ToolExecutionError: If tool execution fails
    """
    # Check if tool exists
    if tool_name not in TOOL_REGISTRY:
        raise ToolValidationError(f"Unknown tool: {tool_name}")
    
    tool_info = TOOL_REGISTRY[tool_name]
    tool_function = tool_info["function"]
    
    # Validate required parameters
    required_params = tool_info["parameters"].get("required", [])
    for param in required_params:
        if param not in tool_args:
            raise ToolValidationError(f"Missing required parameter: {param}")
    
    # Execute tool with error handling
    try:
        result = tool_function(**tool_args)
        return result
    except ValueError as e:
        # Tool-level validation error
        raise ToolValidationError(f"Tool validation error: {e}")
    except Exception as e:
        # Unexpected tool execution error
        raise ToolExecutionError(f"Tool execution failed: {e}")


def get_tool_schema() -> dict[str, Any]:
    """
    Return the tool schema for function calling.
    
    This can be used to inform the model about available tools.
    """
    return {
        "tools": [
            {
                "name": name,
                "description": info["description"],
                "parameters": info["parameters"]
            }
            for name, info in TOOL_REGISTRY.items()
        ]
    }


def parse_tool_calls(model_response: str) -> list[dict[str, Any]]:
    """
    Parse tool calls from model response.
    
    Expected format: JSON array of tool calls with "name" and "arguments" fields.
    
    Args:
        model_response: Raw model response text
    
    Returns:
        List of parsed tool call dictionaries
    
    Raises:
        ValueError: If response cannot be parsed as valid tool calls
    """
    try:
        parsed = json.loads(model_response)
        
        # Handle both single object and array
        if isinstance(parsed, dict):
            if "tool_calls" in parsed:
                tool_calls = parsed["tool_calls"]
            else:
                # Single tool call
                tool_calls = [parsed]
        elif isinstance(parsed, list):
            tool_calls = parsed
        else:
            raise ValueError("Response must be a JSON object or array")
        
        # Validate tool call structure
        validated_calls = []
        for call in tool_calls:
            if not isinstance(call, dict):
                raise ValueError("Each tool call must be a JSON object")
            if "name" not in call:
                raise ValueError("Tool call missing 'name' field")
            if "arguments" not in call:
                raise ValueError("Tool call missing 'arguments' field")
            if not isinstance(call["arguments"], dict):
                raise ValueError("Tool call 'arguments' must be a JSON object")
            
            validated_calls.append({
                "name": call["name"],
                "arguments": call["arguments"]
            })
        
        return validated_calls
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in model response: {e}")


def execute_tool_calls(tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Execute multiple tool calls and return their results.
    
    Args:
        tool_calls: List of tool call dictionaries with "name" and "arguments"
    
    Returns:
        List of execution results, each containing:
        - tool_name: Name of the tool
        - success: Whether execution succeeded
        - result: Tool result if successful
        - error: Error message if failed
    """
    results = []
    
    for call in tool_calls:
        tool_name = call["name"]
        tool_args = call["arguments"]
        
        try:
            result = execute_tool_call(tool_name, tool_args)
            results.append({
                "tool_name": tool_name,
                "success": True,
                "result": result,
                "error": None
            })
        except ToolValidationError as e:
            results.append({
                "tool_name": tool_name,
                "success": False,
                "result": None,
                "error": str(e)
            })
        except ToolExecutionError as e:
            results.append({
                "tool_name": tool_name,
                "success": False,
                "result": None,
                "error": str(e)
            })
    
    return results
