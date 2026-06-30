import pytest

from tracker import ToolInvocationLog, TrajectoryTracker


@pytest.fixture
def tracker() -> TrajectoryTracker:
    return TrajectoryTracker(loop_threshold=4)


@pytest.fixture
def success_log() -> ToolInvocationLog:
    return ToolInvocationLog(
        tool_name="query_database",
        input_payload={"table": "users"},
        execution_time_ms=12.0,
        response_status="success",
    )


@pytest.fixture
def error_log() -> ToolInvocationLog:
    return ToolInvocationLog(
        tool_name="financial_calculator",
        input_payload={"operation": "sum", "values": [1, 2, 3]},
        execution_time_ms=15.0,
        response_status="error",
    )


@pytest.fixture
def malformed_log() -> ToolInvocationLog:
    return ToolInvocationLog(
        tool_name="query_database",
        input_payload={},
        execution_time_ms=10.0,
        response_status="error",
    )
