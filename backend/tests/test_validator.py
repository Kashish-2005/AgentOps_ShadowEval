from tracker import ToolInvocationLog, TrajectoryTracker
from validator import HallucinationRisk, evaluate


def test_last_log_success_means_task_completed(
    tracker: TrajectoryTracker, success_log: ToolInvocationLog
) -> None:
    tracker.logs.append(success_log)
    report = evaluate(tracker, "analyst", 50.0, loop_detected=False)
    assert report.task_completed is True


def test_last_log_error_means_task_not_completed(
    tracker: TrajectoryTracker, error_log: ToolInvocationLog
) -> None:
    tracker.logs.append(error_log)
    report = evaluate(tracker, "analyst", 50.0, loop_detected=False)
    assert report.task_completed is False


def test_no_logs_means_task_not_completed(tracker: TrajectoryTracker) -> None:
    report = evaluate(tracker, "analyst", 50.0, loop_detected=False)
    assert report.task_completed is False


def test_two_tool_calls_efficiency_score_is_eight(
    tracker: TrajectoryTracker, success_log: ToolInvocationLog
) -> None:
    tracker.logs.extend([success_log, success_log])
    report = evaluate(tracker, "analyst", 50.0, loop_detected=False)
    assert report.efficiency_score == 8


def test_nine_tool_calls_efficiency_score_is_one(
    tracker: TrajectoryTracker, success_log: ToolInvocationLog
) -> None:
    tracker.logs.extend([success_log] * 9)
    report = evaluate(tracker, "analyst", 50.0, loop_detected=False)
    assert report.efficiency_score == 1


def test_malformed_payload_missing_table_is_high_risk(
    tracker: TrajectoryTracker, malformed_log: ToolInvocationLog
) -> None:
    tracker.logs.append(malformed_log)
    report = evaluate(tracker, "analyst", 50.0, loop_detected=False)
    assert report.hallucination_risk == HallucinationRisk.HIGH


def test_all_valid_payloads_are_low_risk(
    tracker: TrajectoryTracker, success_log: ToolInvocationLog
) -> None:
    tracker.logs.append(success_log)
    report = evaluate(tracker, "analyst", 50.0, loop_detected=False)
    assert report.hallucination_risk == HallucinationRisk.LOW


def test_notes_list_is_never_empty(tracker: TrajectoryTracker) -> None:
    report = evaluate(tracker, "analyst", 50.0, loop_detected=False)
    assert len(report.notes) > 0


def test_all_success_logs_success_rate_is_one(
    tracker: TrajectoryTracker, success_log: ToolInvocationLog
) -> None:
    tracker.logs.extend([success_log, success_log])
    report = evaluate(tracker, "analyst", 50.0, loop_detected=False)
    assert report.success_rate == 1.0


def test_all_error_logs_success_rate_is_zero(
    tracker: TrajectoryTracker, error_log: ToolInvocationLog
) -> None:
    tracker.logs.extend([error_log, error_log])
    report = evaluate(tracker, "analyst", 50.0, loop_detected=False)
    assert report.success_rate == 0.0


def test_risk_factors_is_never_none(tracker: TrajectoryTracker) -> None:
    report = evaluate(tracker, "analyst", 50.0, loop_detected=False)
    assert report.risk_factors is not None


def test_loop_detected_true_in_report_when_passed_true(
    tracker: TrajectoryTracker,
) -> None:
    report = evaluate(tracker, "analyst", 50.0, loop_detected=True)
    assert report.loop_detected is True
