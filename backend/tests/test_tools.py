import pytest
from pydantic import ValidationError

from tools import ToolResult, financial_calculator, query_database


async def test_query_database_valid_payload_returns_success() -> None:
    result = await query_database({"table": "users"})
    assert result.status == "success"


async def test_query_database_missing_table_key_returns_error() -> None:
    result = await query_database({})
    assert result.status == "error"


async def test_query_database_unknown_table_name_returns_success_with_empty_rows() -> None:
    result = await query_database({"table": "nonexistent"})
    assert result.status == "success"
    assert result.output["count"] == 0


async def test_financial_calculator_sum_returns_six() -> None:
    result = await financial_calculator({"operation": "sum", "values": [1, 2, 3]})
    assert result.output["result"] == 6.0


async def test_financial_calculator_average_returns_six() -> None:
    result = await financial_calculator({"operation": "avg", "values": [4, 8]})
    assert result.output["result"] == 6.0


async def test_financial_calculator_missing_operation_returns_error() -> None:
    result = await financial_calculator({"values": [1, 2, 3]})
    assert result.status == "error"


async def test_financial_calculator_empty_values_list_returns_error() -> None:
    result = await financial_calculator(
        {"operation": "compound_interest", "values": []}
    )
    assert result.status == "error"


async def test_tool_result_execution_time_ms_is_non_negative() -> None:
    result = await query_database({"table": "users"})
    assert result.execution_time_ms >= 0


async def test_tool_result_rejects_invalid_status_value() -> None:
    result = await query_database({"table": "users"})
    with pytest.raises(ValidationError):
        ToolResult(
            tool_name=result.tool_name,
            output=result.output,
            status="invalid",  # type: ignore[arg-type]
            execution_time_ms=result.execution_time_ms,
        )
