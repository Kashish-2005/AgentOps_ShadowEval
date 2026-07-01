"""
Module: traffic_engine.py
Project: AgentOps-ShadowEval

This module serves as the execution engine for the ShadowEval simulation. 
It orchestrates persona-based agent runs, manages concurrency via semaphores, 
simulates tool-use trajectories, and triggers the evaluation pipeline.
"""

import asyncio
import logging
import random
import time
from typing import Any

from pydantic import BaseModel

from personas import PersonaProfile
from tools import TOOL_REGISTRY
from tracker import TrajectoryTracker, tracked_tool_call, InfiniteLoopError
from validator import evaluate, EvaluationReport

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class RunResult(BaseModel):
    """
    The final output of a single persona simulation run.
    """
    persona_name: str
    persona_display_name: str = ""
    latency_ms: float
    simulated_token_count: int
    loop_detected: bool
    tool_sequence: list[str] = []
    evaluation: EvaluationReport


async def run_persona(
    persona: PersonaProfile,
    semaphore: asyncio.Semaphore,
    custom_prompt: str | None = None,
) -> RunResult:
    """
    Simulates a single agent interaction loop for a specific persona.

    This function simulates the agent's decision-making process, executes tools
    through a tracker, handles potential infinite loops, and produces an 
    evaluation report.

    Args:
        persona: The behavioral profile to simulate.
        semaphore: A concurrency primitive to limit simultaneous runs.
        custom_prompt: If provided, forces a real query_llm call using this
            exact prompt instead of random tool selection. Used when a real
            user submits their own text for evaluation.

    Returns:
        RunResult: The structured results of the simulation.
    """
    async with semaphore:
        logger.info(f"Starting run for persona: {persona['name']}")
        start_time = time.perf_counter()
        
        tracker = TrajectoryTracker(loop_threshold=4)
        loop_detected = False
        tool_sequence: list[str] = []
        
        try:
            if custom_prompt:
                # Real user prompt — single forced call to query_llm
                tool_name = "query_llm"
                tool_sequence.append(tool_name)
                tool_fn = TOOL_REGISTRY[tool_name]
                payload: dict[str, Any] = {"prompt": custom_prompt, "max_length": 150}
                await tracked_tool_call(tracker, tool_fn, payload)
            else:
                # Simulated persona behavior — existing random logic unchanged
                num_calls = max(2, min(5, persona["expected_tool_calls"]))

                for _ in range(num_calls):
                    tool_name = random.choice(list(TOOL_REGISTRY.keys()))
                    tool_sequence.append(tool_name)
                    tool_fn = TOOL_REGISTRY[tool_name]

                    is_malformed = (persona["name"] == "Adversarial Tester" and random.random() < 0.3)

                    payload = {}
                    if tool_name == "query_database":
                        if not is_malformed:
                            payload = {"table": random.choice(["users", "orders"]), "filter": "id > 0"}
                    elif tool_name == "financial_calculator":
                        if not is_malformed:
                            payload = {
                                "operation": random.choice(["sum", "avg"]),
                                "values": [random.uniform(10, 100) for _ in range(3)]
                            }
                    elif tool_name == "query_llm":
                        if not is_malformed:
                            payload = {"prompt": f"Analyze this scenario for {persona['name']}", "max_length": 100}

                    await tracked_tool_call(tracker, tool_fn, payload)

        except InfiniteLoopError as e:
            logger.warning(f"Loop detected for {persona['name']}: {e}")
            loop_detected = True
        except Exception as e:
            logger.error(f"Unexpected error during tool execution for {persona['name']}: {e}")

        end_time = time.perf_counter()
        total_latency_ms = (end_time - start_time) * 1000
        
        eval_report = evaluate(
            tracker=tracker,
            persona_name=persona["name"],
            latency_ms=total_latency_ms,
            loop_detected=loop_detected
        )
        
        token_base = 1000 if "verbose" in persona["query_style"] else 200
        simulated_tokens = token_base + random.randint(50, 500)

        logger.info(f"Completed run for persona: {persona['name']}")
        
        return RunResult(
            persona_name=persona["name"],
            persona_display_name=persona["name"],
            latency_ms=total_latency_ms,
            simulated_token_count=simulated_tokens,
            loop_detected=loop_detected,
            tool_sequence=tool_sequence,
            evaluation=eval_report
        )


async def run_all_personas(
    personas: dict[str, PersonaProfile],
    concurrency_limit: int = 3,
) -> list[RunResult]:
    """
    Orchestrates the parallel execution of multiple persona simulations.

    Args:
        personas: A dictionary of PersonaProfile objects.
        concurrency_limit: The maximum number of concurrent simulations.

    Returns:
        list[RunResult]: A list of results for all executed personas.
    """
    semaphore = asyncio.Semaphore(concurrency_limit)
    tasks = [
        run_persona(persona, semaphore) 
        for persona in personas.values()
    ]
    
    results = await asyncio.gather(*tasks)
    return list(results)