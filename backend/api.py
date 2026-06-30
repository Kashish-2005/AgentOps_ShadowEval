"""
Module: api.py
Project: AgentOps-ShadowEval
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from prometheus_client import (
    Histogram, Counter, Gauge,
    generate_latest, CONTENT_TYPE_LATEST
)

from config import settings
from personas import PERSONAS, get_persona, list_personas
from traffic_engine import run_persona, run_all_personas, RunResult
from logging_config import setup_logging, get_logger, RequestIDMiddleware
from database import (
    init_db,
    insert_evaluation,
    get_all_evaluations,
    get_evaluations_by_persona,
    delete_evaluation,
    get_stats,
    EvaluationRecord,
)

# ── Prometheus Metrics ──────────────────────────────────────────────────────

agent_execution_latency = Histogram(
    "agent_execution_latency_seconds",
    "End-to-end latency per persona run",
    ["persona_name"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)
api_error_total = Counter(
    "api_error_total",
    "Total API errors",
    ["error_type", "endpoint"],
)
estimated_usd_cost_total = Gauge(
    "estimated_usd_cost_total",
    "Cumulative estimated USD cost (mocked)",
)
active_evaluations = Gauge(
    "active_evaluations",
    "Number of evaluations currently running",
)

logger = get_logger(__name__)


# ── Lifespan ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging(
        level=settings.LOG_LEVEL,
        json_format=settings.is_production,
    )
    try:
        await init_db()
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}")
        raise
    logger.info(f"AgentOps-ShadowEval started. Personas: {list(PERSONAS.keys())}")
    yield
    logger.info("Shutdown complete.")


# ── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AgentOps-ShadowEval API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request Models ───────────────────────────────────────────────────────────

class EvaluateRequest(BaseModel):
    persona_name: str
    concurrency_limit: int = Field(default=3, ge=1, le=10)


class BatchEvaluateRequest(BaseModel):
    persona_names: list[str] = Field(min_length=1, max_length=5)
    concurrency_limit: int = Field(default=3, ge=1, le=10)


# ── Helper ───────────────────────────────────────────────────────────────────

def _run_result_to_record(result: RunResult) -> EvaluationRecord:
    """Convert a RunResult into an EvaluationRecord for DB insertion."""
    return EvaluationRecord(
        persona=result.persona_name,
        persona_display_name=result.persona_display_name,
        latency_ms=result.latency_ms,
        tokens=result.simulated_token_count,
        efficiency_score=result.evaluation.efficiency_score,
        loop_detected=result.loop_detected,
        risk=result.evaluation.hallucination_risk.value
            if hasattr(result.evaluation.hallucination_risk, "value")
            else str(result.evaluation.hallucination_risk),
        task_completed=result.evaluation.task_completed,
        success_rate=result.evaluation.success_rate,
        tool_sequence=result.tool_sequence,
        notes=result.evaluation.notes,
        risk_factors=result.evaluation.risk_factors,
    )


def _update_metrics(result: RunResult) -> None:
    agent_execution_latency.labels(
        persona_name=result.persona_name
    ).observe(result.latency_ms / 1000.0)
    cost = result.simulated_token_count * settings.ESTIMATED_COST_PER_TOKEN_USD
    estimated_usd_cost_total.inc(cost)


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check — returns status and UTC timestamp."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }


@app.get("/api/v1/personas")
async def list_all_personas() -> list[dict]:
    """Return all registered personas for the frontend selector."""
    return list_personas()


@app.post("/api/v1/evaluate", response_model=RunResult)
async def evaluate_agent(request: EvaluateRequest) -> RunResult:
    """
    Run a single persona evaluation.
    Validates persona, runs simulation, saves to DB, updates Prometheus.
    """
    try:
        persona_profile = get_persona(request.persona_name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Persona '{request.persona_name}' not found. "
                   f"Available: {list(PERSONAS.keys())}",
        )

    active_evaluations.inc()
    try:
        semaphore = asyncio.Semaphore(request.concurrency_limit)
        result = await run_persona(persona_profile, semaphore)
        _update_metrics(result)

        # Save to DB
        try:
            record = _run_result_to_record(result)
            await insert_evaluation(record)
        except Exception as db_err:
            # Non-fatal — log but don't fail the response
            logger.error(f"Failed to persist evaluation: {db_err}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error during single evaluation")
        api_error_total.labels(
            error_type=type(e).__name__,
            endpoint="/api/v1/evaluate",
        ).inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during evaluation.",
        )
    finally:
        active_evaluations.dec()


@app.post("/api/v1/evaluate/batch")
async def evaluate_batch(request: BatchEvaluateRequest) -> list[RunResult]:
    """
    Run evaluations for multiple personas concurrently.
    """
    # Validate all persona names first
    invalid = [n for n in request.persona_names if n not in PERSONAS]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown personas: {invalid}. Available: {list(PERSONAS.keys())}",
        )

    personas_subset = {k: v for k, v in PERSONAS.items() if k in request.persona_names}

    active_evaluations.inc(len(request.persona_names))
    try:
        results = await run_all_personas(
            personas=personas_subset,
            concurrency_limit=request.concurrency_limit,
        )

        # Save all to DB — non-fatal if any fail
        for result in results:
            try:
                record = _run_result_to_record(result)
                await insert_evaluation(record)
                _update_metrics(result)
            except Exception as db_err:
                logger.error(f"Failed to persist batch result for {result.persona_name}: {db_err}")

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error during batch evaluation")
        api_error_total.labels(
            error_type=type(e).__name__,
            endpoint="/api/v1/evaluate/batch",
        ).inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during batch evaluation.",
        )
    finally:
        active_evaluations.dec(len(request.persona_names))


@app.get("/api/v1/history")
async def get_history(
    persona: str | None = None,
    limit: int = 50,
) -> list[EvaluationRecord]:
    """
    Fetch evaluation history from DB.
    Optional ?persona= filter. Optional ?limit= (max 200).
    """
    limit = min(limit, 200)
    try:
        if persona:
            return await get_evaluations_by_persona(persona, limit)
        return await get_all_evaluations(limit)
    except Exception as e:
        logger.error(f"Failed to fetch history: {e}")
        api_error_total.labels(
            error_type=type(e).__name__,
            endpoint="/api/v1/history",
        ).inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not retrieve history from database.",
        )


@app.get("/api/v1/stats")
async def get_dashboard_stats() -> dict:
    """
    Return aggregate stats for the dashboard stat cards.
    """
    try:
        return await get_stats()
    except Exception as e:
        logger.error(f"Failed to fetch stats: {e}")
        api_error_total.labels(
            error_type=type(e).__name__,
            endpoint="/api/v1/stats",
        ).inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not retrieve stats from database.",
        )


@app.delete("/api/v1/history/{record_id}")
async def delete_record(record_id: int) -> dict[str, bool]:
    """
    Delete a single evaluation record by ID.
    Returns {"deleted": true} if found and removed, {"deleted": false} if not found.
    """
    try:
        deleted = await delete_evaluation(record_id)
        return {"deleted": deleted}
    except Exception as e:
        logger.error(f"Failed to delete record {record_id}: {e}")
        api_error_total.labels(
            error_type=type(e).__name__,
            endpoint="/api/v1/history/{record_id}",
        ).inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not delete record.",
        )


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics scrape endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )

#TEMP
@app.post("/api/v1/debug/test-llm")
async def debug_test_llm(prompt: str = "Explain async Python in one sentence") -> dict:
    """TEMPORARY — direct test of query_llm_inference, bypassing persona simulation."""
    from tools import query_llm_inference
    result = await query_llm_inference({"prompt": prompt})
    return {
        "status": result.status,
        "output": result.output,
        "execution_time_ms": result.execution_time_ms,
    }