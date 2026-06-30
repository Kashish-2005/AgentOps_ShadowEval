"""
Module: validator.py
Project: AgentOps-ShadowEval

This module provides validation and evaluation logic for agent trajectories.
It assesses task completion, efficiency, hallucination risks, and structural 
integrity based on the logs collected by the TrajectoryTracker.
"""

from enum import Enum
from typing import TYPE_CHECKING, Literal
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from tracker import TrajectoryTracker


class HallucinationRisk(str, Enum):
    """Enumeration of potential hallucination risk levels."""
    LOW = "low"
    HIGH = "high"


class EvaluationReport(BaseModel):
    """
    Final evaluation report schema for a single agent trajectory.
    """
    task_completed: bool
    efficiency_score: int = Field(ge=1, le=10)
    loop_detected: bool
    hallucination_risk: HallucinationRisk
    total_tool_calls: int
    persona_name: str
    latency_ms: float
    notes: list[str]
    success_rate: float = 0.0
    risk_factors: list[str] = []


def evaluate(
    tracker: "TrajectoryTracker",
    persona_name: str,
    latency_ms: float,
    loop_detected: bool,
) -> EvaluationReport:
    """
    Evaluates an agent's trajectory and returns a structured report.
    """
    logs = tracker.get_logs()
    total_calls = len(logs)
    success_count = sum(1 for log in logs if log.response_status == "success")
    success_rate = round(success_count / total_calls, 3) if total_calls > 0 else 0.0
    
    notes: list[str] = []

    # 1. Determine Task Completion
    task_completed = False
    if logs:
        task_completed = logs[-1].response_status == "success"
        status_msg = "Task reached success state." if task_completed else "Task failed in terminal state."
    else:
        status_msg = "No tool calls were recorded."
    notes.append(f"Task Completion: {status_msg}")

    # 2. Efficiency Score
    efficiency_score = max(1, 10 - total_calls)
    notes.append(f"Efficiency: Score of {efficiency_score} based on {total_calls} tool calls.")

    # 3. Hallucination Risk Assessment
    risk = HallucinationRisk.LOW
    risk_factors: list[str] = []
    
    for log in logs:
        is_malformed = False
        if log.tool_name == "query_database":
            if "table" not in log.input_payload:
                is_malformed = True
        elif log.tool_name == "financial_calculator":
            if "operation" not in log.input_payload or "values" not in log.input_payload:
                is_malformed = True
        
        if is_malformed:
            risk = HallucinationRisk.HIGH
            risk_factors.append(f"Missing required keys in payload for tool '{log.tool_name}'")
            notes.append(f"Hallucination detected: Missing required keys in tool '{log.tool_name}'.")
            break
    
    if risk == HallucinationRisk.LOW:
        risk_factors.append("All tool payloads structurally valid")
        notes.append("Hallucination Risk: Low. All tool inputs were structurally sound.")

    if loop_detected:
        notes.append("System Warning: Infinite loop logic was triggered during execution.")

    return EvaluationReport(
        task_completed=task_completed,
        efficiency_score=efficiency_score,
        loop_detected=loop_detected,
        hallucination_risk=risk,
        total_tool_calls=total_calls,
        persona_name=persona_name,
        latency_ms=latency_ms,
        notes=notes,
        success_rate=success_rate,
        risk_factors=risk_factors,
    )