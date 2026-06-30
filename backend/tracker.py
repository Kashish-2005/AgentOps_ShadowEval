"""
Module: tracker.py
Project: AgentOps-ShadowEval

This module provides telemetry and trajectory tracking for agent-tool interactions.
It includes logic for logging tool invocations, detecting infinite loops, 
and summarizing execution paths.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Literal, Callable, Awaitable
from contextlib import asynccontextmanager

from pydantic import BaseModel, Field


class ToolInvocationLog(BaseModel):
    """
    Schema for logging a single tool execution within a trajectory.
    """
    tool_name: str
    input_payload: dict[str, Any]
    execution_time_ms: float
    response_status: Literal["success", "error"]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InfiniteLoopError(Exception):
    """
    Exception raised when an agent exceeds the maximum allowed repetitive 
    calls to the same tool.
    """
    def __init__(self, tool_name: str, count: int) -> None:
        self.tool_name = tool_name
        self.count = count
        super().__init__(
            f"Infinite loop detected: Tool '{tool_name}' was called {count} times, "
            f"exceeding the safety threshold."
        )


class TrajectoryTracker:
    """
    Tracks the sequence of tool calls made by an agent and identifies 
    potential execution anomalies.
    """

    def __init__(self, loop_threshold: int = 4) -> None:
        """
        Initializes the tracker with a specific threshold for loop detection.

        Args:
            loop_threshold: Maximum number of times a single tool can be called.
        """
        self.loop_threshold = loop_threshold
        self.logs: list[ToolInvocationLog] = []
        self._call_counts: dict[str, int] = {}

    async def record(self, log: ToolInvocationLog) -> None:
        """
        Records a tool invocation and checks for infinite loop conditions.

        Args:
            log: The tool invocation record to store.

        Raises:
            InfiniteLoopError: If the tool call count exceeds the loop_threshold.
        """
        self.logs.append(log)
        
        # Update call frequency
        current_count = self._call_counts.get(log.tool_name, 0) + 1
        self._call_counts[log.tool_name] = current_count

        if current_count > self.loop_threshold:
            raise InfiniteLoopError(log.tool_name, current_count)

    def get_logs(self) -> list[ToolInvocationLog]:
        """Returns the full list of recorded tool invocations."""
        return self.logs

    def reset(self) -> None:
        """Clears all logs and call counts."""
        self.logs.clear()
        self._call_counts.clear()

    def summary(self) -> dict[str, Any]:
        """
        Provides a statistical summary of the tracked trajectory.

        Returns:
            A dictionary containing total calls, unique tools used, 
            loop detection status, and the last tool executed.
        """
        last_tool = self.logs[-1].tool_name if self.logs else None
        loop_detected = any(count > self.loop_threshold for count in self._call_counts.values())

        return {
            "total_calls": len(self.logs),
            "unique_tools": len(self._call_counts),
            "loop_detected": loop_detected,
            "last_tool": last_tool,
        }


@asynccontextmanager
async def tracked_tool_call(
    tracker: TrajectoryTracker, 
    tool_fn: Callable[[dict[str, Any]], Awaitable[Any]], 
    payload: dict[str, Any]
):
    """
    Async context manager that executes a tool, records its metadata to the 
    provided tracker, and yields the result.

    Args:
        tracker: The TrajectoryTracker instance to log the call.
        tool_fn: The asynchronous tool function to execute.
        payload: The input dictionary for the tool.

    Yields:
        ToolResult: The result object from the tool execution.
    """
    # Execute the tool
    result = await tool_fn(payload)

    # Prepare the log entry
    # Note: Assumes tool_fn returns a ToolResult-like object (per tools.py)
    log = ToolInvocationLog(
        tool_name=getattr(result, "tool_name", "unknown"),
        input_payload=payload,
        execution_time_ms=getattr(result, "execution_time_ms", 0.0),
        response_status=getattr(result, "status", "error"),
    )

    # Record to tracker (may raise InfiniteLoopError)
    await tracker.record(log)

    yield result