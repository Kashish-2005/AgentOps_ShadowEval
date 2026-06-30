import pytest

from tools import query_database
from tracker import InfiniteLoopError, ToolInvocationLog, TrajectoryTracker, tracked_tool_call


async def test_record_once_adds_one_log(tracker: TrajectoryTracker, success_log: ToolInvocationLog) -> None:
    await tracker.record(success_log)
    assert len(tracker.get_logs()) == 1


async def test_same_tool_four_times_does_not_raise(
    tracker: TrajectoryTracker, success_log: ToolInvocationLog
) -> None:
    for _ in range(4):
        await tracker.record(success_log)


async def test_same_tool_fifth_time_raises_infinite_loop_error(
    tracker: TrajectoryTracker, success_log: ToolInvocationLog
) -> None:
    for _ in range(4):
        await tracker.record(success_log)
    with pytest.raises(InfiniteLoopError):
        await tracker.record(success_log)


async def test_infinite_loop_error_has_tool_name_attribute(
    tracker: TrajectoryTracker, success_log: ToolInvocationLog
) -> None:
    for _ in range(4):
        await tracker.record(success_log)
    with pytest.raises(InfiniteLoopError) as exc_info:
        await tracker.record(success_log)
    assert exc_info.value.tool_name == success_log.tool_name


async def test_reset_clears_logs(tracker: TrajectoryTracker, success_log: ToolInvocationLog) -> None:
    await tracker.record(success_log)
    tracker.reset()
    assert len(tracker.get_logs()) == 0


async def test_reset_clears_loop_detected(
    tracker: TrajectoryTracker, success_log: ToolInvocationLog
) -> None:
    await tracker.record(success_log)
    tracker.reset()
    assert tracker.summary()["loop_detected"] is False


async def test_summary_contains_expected_keys(
    tracker: TrajectoryTracker, success_log: ToolInvocationLog
) -> None:
    await tracker.record(success_log)
    summary = tracker.summary()
    assert "total_calls" in summary
    assert "loop_detected" in summary
    assert "last_tool" in summary


async def test_success_rate_is_one_when_all_logs_success(
    tracker: TrajectoryTracker, success_log: ToolInvocationLog
) -> None:
    await tracker.record(success_log)
    logs = tracker.get_logs()
    success_count = sum(1 for log in logs if log.response_status == "success")
    success_rate = round(success_count / len(logs), 3)
    assert success_rate == 1.0


async def test_success_rate_is_zero_when_all_logs_error(
    tracker: TrajectoryTracker, error_log: ToolInvocationLog
) -> None:
    await tracker.record(error_log)
    logs = tracker.get_logs()
    success_count = sum(1 for log in logs if log.response_status == "success")
    success_rate = round(success_count / len(logs), 3)
    assert success_rate == 0.0


async def test_tracked_tool_call_records_one_log(tracker: TrajectoryTracker) -> None:
    async with tracked_tool_call(
        tracker, query_database, {"table": "users"}
    ) as result:
        assert result.status == "success"
    assert len(tracker.get_logs()) == 1
