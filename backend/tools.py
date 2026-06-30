"""
Module: tools.py
Project: AgentOps-ShadowEval

This module provides mock asynchronous tools used by agents during evaluation.
Each tool simulates real-world latency and provides deterministic outputs based
on the provided input payloads.
"""

import asyncio
import time
from typing import Any, Literal, Callable, Awaitable
from pydantic import BaseModel


class ToolResult(BaseModel):
    """
    Standardized schema for the result of a tool execution.

    Attributes:
        tool_name: The identifier of the tool that was executed.
        output: A dictionary containing the computed data or error details.
        status: Indicates whether the operation succeeded or encountered an error.
        execution_time_ms: The actual time taken to execute the tool in milliseconds.
    """

    tool_name: str
    output: dict[str, Any]
    status: Literal["success", "error"]
    execution_time_ms: float


async def query_database(payload: dict[str, Any]) -> ToolResult:
    """
    Simulates a database query against hardcoded tables.

    Args:
        payload: Dictionary containing 'table' (str) and 'filter' (Any).

    Returns:
        ToolResult: Contains mock rows if table exists, else an error.
    """
    start_time = time.perf_counter()
    tool_name = "query_database"

    # Simulate latency (deterministic 30ms within 10-50ms range)
    await asyncio.sleep(0.03)

    table = payload.get("table")
    if not table:
        execution_time = (time.perf_counter() - start_time) * 1000
        return ToolResult(
            tool_name=tool_name,
            output={"error": "Missing required key: 'table'"},
            status="error",
            execution_time_ms=execution_time,
        )

    # Mock data registry
    mock_db: dict[str, list[dict[str, Any]]] = {
        "users": [{"id": 1, "name": "Admin"}, {"id": 2, "name": "Guest"}],
        "orders": [{"id": 101, "amount": 250.0}, {"id": 102, "amount": 45.0}],
    }

    data = mock_db.get(table, [])
    execution_time = (time.perf_counter() - start_time) * 1000

    return ToolResult(
        tool_name=tool_name,
        output={"rows": data, "count": len(data)},
        status="success",
        execution_time_ms=execution_time,
    )


async def financial_calculator(payload: dict[str, Any]) -> ToolResult:
    """
    Performs basic financial computations.

    Args:
        payload: Dictionary containing:
            - 'operation': Literal["sum", "avg", "compound_interest"]
            - 'values': list[float]. 
              For 'compound_interest', expected order is [principal, rate, years].

    Returns:
        ToolResult: The calculation result or error details.
    """
    start_time = time.perf_counter()
    tool_name = "financial_calculator"

    # Simulate latency (deterministic 12ms within 5-20ms range)
    await asyncio.sleep(0.012)

    operation = payload.get("operation")
    values = payload.get("values", [])

    if not isinstance(values, list) or not all(isinstance(v, (int, float)) for v in values):
        execution_time = (time.perf_counter() - start_time) * 1000
        return ToolResult(
            tool_name=tool_name,
            output={"error": "Invalid or missing 'values' list"},
            status="error",
            execution_time_ms=execution_time,
        )

    result_value: float = 0.0
    status: Literal["success", "error"] = "success"
    output_payload: dict[str, Any] = {}

    try:
        match operation:
            case "sum":
                result_value = sum(values)
            case "avg":
                result_value = sum(values) / len(values) if values else 0.0
            case "compound_interest":
                # Formula: A = P(1 + r)^t
                if len(values) >= 3:
                    p, r, t = values[:3]
                    result_value = p * (1 + r) ** t
                else:
                    raise ValueError("Compound interest requires [principal, rate, years]")
            case _:
                status = "error"
                output_payload = {"error": f"Unsupported operation: {operation}"}

        if status == "success":
            output_payload = {"result": round(result_value, 4)}

    except Exception as e:
        status = "error"
        output_payload = {"error": str(e)}

    execution_time = (time.perf_counter() - start_time) * 1000
    return ToolResult(
        tool_name=tool_name,
        output=output_payload,
        status=status,
        execution_time_ms=execution_time,
    )


TOOL_REGISTRY: dict[str, Callable[[dict[str, Any]], Awaitable[ToolResult]]] = {
    "query_database": query_database,
    "financial_calculator": financial_calculator,
}