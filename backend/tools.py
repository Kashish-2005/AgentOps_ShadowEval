"""
Module: tools.py
Project: AgentOps-ShadowEval

This module provides mock asynchronous tools used by agents during evaluation.
Each tool simulates real-world latency and provides deterministic outputs based
on the provided input payloads.
"""

import asyncio
import logging
import time
from typing import Any, Literal, Callable, Awaitable
from pydantic import BaseModel
import os
import aiohttp

logger = logging.getLogger(__name__)


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


async def query_llm_inference(payload: dict[str, Any]) -> ToolResult:
    """
    Calls a real LLM via HuggingFace Inference API, or returns a
    deterministic mock response if USE_REAL_LLM is not enabled.

    Args:
        payload: Dictionary containing:
            - 'prompt': str (required)
            - 'max_length': int (optional, default 100)

    Returns:
        ToolResult: The model response or error details.
    """
    start_time = time.perf_counter()
    tool_name = "query_llm"

    prompt = payload.get("prompt")
    if not prompt:
        execution_time = (time.perf_counter() - start_time) * 1000
        return ToolResult(
            tool_name=tool_name,
            output={"error": "Missing required key: 'prompt'"},
            status="error",
            execution_time_ms=execution_time,
        )

    max_length = payload.get("max_length", 100)
    use_real_llm = os.getenv("USE_REAL_LLM", "False").lower() == "true"
    logger.info(f"query_llm_inference called — USE_REAL_LLM={use_real_llm}")

    # --- Mock mode ---
    if not use_real_llm:
        await asyncio.sleep(0.05)
        execution_time = (time.perf_counter() - start_time) * 1000
        return ToolResult(
            tool_name=tool_name,
            output={
                "response": f"[mock response] Analysis of: {prompt[:50]}...",
                "model": "mock-flan-t5",
                "mock": True,
            },
            status="success",
            execution_time_ms=execution_time,
        )

    # --- Real mode ---
    api_key = os.getenv("HUGGINGFACE_API_KEY", "")
    model = os.getenv("HUGGINGFACE_MODEL", "google/flan-t5-base")
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    logger.info(f"Calling HuggingFace model={model} api_key_present={bool(api_key)}")

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                url,
                headers=headers,
                json={"inputs": prompt, "parameters": {"max_length": max_length}},
            ) as resp:
                execution_time = (time.perf_counter() - start_time) * 1000

                if resp.status != 200:
                    error_body = await resp.text()
                    logger.warning(f"HuggingFace returned status {resp.status}: {error_body[:200]}")
                    return ToolResult(
                        tool_name=tool_name,
                        output={"error": f"HuggingFace API error {resp.status}: {error_body[:200]}"},
                        status="error",
                        execution_time_ms=execution_time,
                    )

                data = await resp.json()
                response_text = ""
                if isinstance(data, list) and len(data) > 0:
                    response_text = data[0].get("generated_text", str(data[0]))
                else:
                    response_text = str(data)

                logger.info(f"HuggingFace responded successfully, length={len(response_text)}")

                return ToolResult(
                    tool_name=tool_name,
                    output={
                        "response": response_text,
                        "model": model,
                        "mock": False,
                    },
                    status="success",
                    execution_time_ms=execution_time,
                )

    except asyncio.TimeoutError:
        execution_time = (time.perf_counter() - start_time) * 1000
        logger.warning("HuggingFace request timed out after 10 seconds")
        return ToolResult(
            tool_name=tool_name,
            output={"error": "LLM request timed out after 10 seconds"},
            status="error",
            execution_time_ms=execution_time,
        )
    except Exception as e:
        execution_time = (time.perf_counter() - start_time) * 1000
        logger.error(f"LLM request failed: {str(e)}")
        return ToolResult(
            tool_name=tool_name,
            output={"error": f"LLM request failed: {str(e)}"},
            status="error",
            execution_time_ms=execution_time,
        )


TOOL_REGISTRY: dict[str, Callable[[dict[str, Any]], Awaitable[ToolResult]]] = {
    "query_database": query_database,
    "financial_calculator": financial_calculator,
    "query_llm": query_llm_inference,
}