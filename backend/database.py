"""
Module: database.py
Project: AgentOps-ShadowEval

This module handles asynchronous persistence for evaluation results using SQLite.
It provides functions for database initialization, record insertion, and retrieval
with automatic serialization of complex types and strict Pydantic validation.
"""

import os
import json
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Any, Literal, AsyncGenerator
from contextlib import asynccontextmanager

import aiosqlite
from pydantic import BaseModel, Field, ConfigDict

# Environment configuration
DB_PATH = os.getenv("DB_PATH", "/data/shadoweval.db")

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Custom exception for database-related failures."""
    pass


class EvaluationRecord(BaseModel):
    """
    Pydantic model representing a persisted evaluation record.
    """
    id: int | None = None
    persona: str
    persona_display_name: str = ""
    latency_ms: float
    tokens: int
    efficiency_score: int
    success_rate: float = 0.0
    loop_detected: bool
    risk: str
    risk_factors: list[str] = []
    tool_sequence: list[str] = []
    task_completed: bool
    notes: list[str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


@asynccontextmanager
async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    Async context manager that provides a fresh database connection.
    Connections are closed automatically after use to prevent locking issues.
    """
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute("PRAGMA busy_timeout=5000")
    try:
        yield conn
    finally:
        await conn.close()


async def init_db() -> None:
    """
    Initializes the database schema if the table does not exist.
    
    Raises:
        DatabaseError: If the table creation fails.
    """
    query = """
    CREATE TABLE IF NOT EXISTS evaluations (
        id                   INTEGER PRIMARY KEY AUTOINCREMENT,
        persona              TEXT    NOT NULL,
        persona_display_name TEXT    NOT NULL DEFAULT '',
        latency_ms           REAL    NOT NULL,
        tokens               INTEGER NOT NULL,
        efficiency_score     INTEGER NOT NULL,
        success_rate         REAL    NOT NULL DEFAULT 0.0,
        loop_detected        INTEGER NOT NULL,
        risk                 TEXT    NOT NULL,
        risk_factors         TEXT    NOT NULL DEFAULT '[]',
        tool_sequence        TEXT    NOT NULL DEFAULT '[]',
        task_completed       INTEGER NOT NULL,
        notes                TEXT    NOT NULL,
        timestamp            TEXT    NOT NULL
    );
    """
    try:
        async with get_db() as db:
            await db.execute(query)
            await db.commit()
        logger.info(f"Database initialized successfully at: {DB_PATH}")
    except aiosqlite.Error as e:
        raise DatabaseError(f"Failed to initialize database: {e}")


async def insert_evaluation(record: EvaluationRecord) -> int:
    """
    Inserts a single evaluation record into the database.

    Args:
        record: The EvaluationRecord model to persist.

    Returns:
        int: The primary key ID of the newly inserted row.

    Raises:
        DatabaseError: If the insertion fails.
    """
    query = """
    INSERT INTO evaluations (
        persona, persona_display_name, latency_ms, tokens, efficiency_score, 
        success_rate, loop_detected, risk, risk_factors, tool_sequence,
        task_completed, notes, timestamp
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    try:
        async with get_db() as db:
            cursor = await db.execute(
                query,
                (
                    record.persona,
                    record.persona_display_name,
                    record.latency_ms,
                    record.tokens,
                    record.efficiency_score,
                    record.success_rate,
                    1 if record.loop_detected else 0,
                    record.risk,
                    json.dumps(record.risk_factors),
                    json.dumps(record.tool_sequence),
                    1 if record.task_completed else 0,
                    json.dumps(record.notes),
                    record.timestamp.isoformat(),
                ),
            )
            await db.commit()
            return cursor.lastrowid or 0
    except aiosqlite.Error as e:
        raise DatabaseError(f"Failed to insert record: {e}")


def _map_row_to_record(row: aiosqlite.Row) -> EvaluationRecord:
    """Helper to convert a sqlite3.Row into an EvaluationRecord."""
    return EvaluationRecord(
        id=row["id"],
        persona=row["persona"],
        persona_display_name=row["persona_display_name"],
        latency_ms=row["latency_ms"],
        tokens=row["tokens"],
        efficiency_score=row["efficiency_score"],
        success_rate=row["success_rate"],
        loop_detected=bool(row["loop_detected"]),
        risk=row["risk"],
        risk_factors=json.loads(row["risk_factors"]),
        tool_sequence=json.loads(row["tool_sequence"]),
        task_completed=bool(row["task_completed"]),
        notes=json.loads(row["notes"]),
        timestamp=datetime.fromisoformat(row["timestamp"]),
    )


async def get_all_evaluations(limit: int = 100) -> list[EvaluationRecord]:
    """
    Retrieves the most recent evaluation records.

    Args:
        limit: Maximum number of records to return.

    Returns:
        list[EvaluationRecord]: List of validated records.
    """
    query = "SELECT * FROM evaluations ORDER BY timestamp DESC LIMIT ?"
    try:
        async with get_db() as db:
            async with db.execute(query, (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [_map_row_to_record(row) for row in rows]
    except aiosqlite.Error as e:
        raise DatabaseError(f"Failed to fetch evaluations: {e}")


async def get_evaluations_by_persona(
    persona: str,
    limit: int = 50,
) -> list[EvaluationRecord]:
    """
    Filters evaluation records by persona name.

    Args:
        persona: The persona name to filter by.
        limit: Maximum number of records to return.

    Returns:
        list[EvaluationRecord]: List of matching records.
    """
    query = "SELECT * FROM evaluations WHERE persona = ? ORDER BY timestamp DESC LIMIT ?"
    try:
        async with get_db() as db:
            async with db.execute(query, (persona, limit)) as cursor:
                rows = await cursor.fetchall()
                return [_map_row_to_record(row) for row in rows]
    except aiosqlite.Error as e:
        raise DatabaseError(f"Failed to fetch evaluations for persona '{persona}': {e}")


async def delete_evaluation(record_id: int) -> bool:
    """
    Deletes an evaluation record by its unique ID.

    Args:
        record_id: The ID of the record to delete.

    Returns:
        bool: True if a row was deleted, False otherwise.
    """
    query = "DELETE FROM evaluations WHERE id = ?"
    try:
        async with get_db() as db:
            cursor = await db.execute(query, (record_id,))
            await db.commit()
            return cursor.rowcount > 0
    except aiosqlite.Error as e:
        raise DatabaseError(f"Failed to delete record {record_id}: {e}")


async def get_stats() -> dict[str, Any]:
    """
    Returns aggregate dashboard statistics.
    """
    try:
        async with get_db() as db:
            # Total runs
            async with db.execute("SELECT COUNT(*) as count FROM evaluations") as cur:
                row = await cur.fetchone()
                total = row["count"] if row else 0

            if total == 0:
                return {
                    "total_runs": 0,
                    "avg_efficiency": 0.0,
                    "avg_latency_ms": 0.0,
                    "loop_detection_rate": 0.0,
                    "risk_distribution": {"low": 0, "medium": 0, "high": 0},
                    "runs_by_persona": {},
                }

            # Averages
            async with db.execute(
                "SELECT AVG(efficiency_score) as avg_eff, AVG(latency_ms) as avg_lat FROM evaluations"
            ) as cur:
                row = await cur.fetchone()
                avg_eff = round(row["avg_eff"] or 0.0, 2)
                avg_lat = round(row["avg_lat"] or 0.0, 2)

            # Loop detection rate
            async with db.execute(
                "SELECT COUNT(*) as count FROM evaluations WHERE loop_detected = 1"
            ) as cur:
                row = await cur.fetchone()
                loop_count = row["count"] if row else 0

            # Risk distribution
            async with db.execute(
                "SELECT risk, COUNT(*) as count FROM evaluations GROUP BY risk"
            ) as cur:
                rows = await cur.fetchall()
                risk_dist: dict[str, int] = {"low": 0, "medium": 0, "high": 0}
                for r in rows:
                    risk_dist[r["risk"]] = r["count"]

            # Runs by persona
            async with db.execute(
                "SELECT persona, COUNT(*) as count FROM evaluations GROUP BY persona"
            ) as cur:
                rows = await cur.fetchall()
                runs_by_persona = {r["persona"]: r["count"] for r in rows}

            return {
                "total_runs": total,
                "avg_efficiency": avg_eff,
                "avg_latency_ms": avg_lat,
                "loop_detection_rate": round(loop_count / total, 3) if total > 0 else 0.0,
                "risk_distribution": risk_dist,
                "runs_by_persona": runs_by_persona,
            }
    except aiosqlite.Error as e:
        raise DatabaseError(f"Failed to fetch stats: {e}")