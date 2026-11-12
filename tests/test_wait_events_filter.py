"""Unit tests for get_wait_events wait_event_type filtering — no database required."""
from unittest.mock import AsyncMock, patch

import pytest

from mcp_postgresql_ops import mcp_main
from mcp_postgresql_ops.version_compat import PostgreSQLVersion

get_wait_events = getattr(mcp_main.get_wait_events, "fn", mcp_main.get_wait_events)


async def _run(major, wait_event_type):
    mock_exec = AsyncMock(return_value=[])
    version = PostgreSQLVersion(major, 0, 0)
    with patch.object(mcp_main, "get_postgresql_version", new_callable=AsyncMock, return_value=version), \
         patch.object(mcp_main, "execute_query", mock_exec):
        await get_wait_events(wait_event_type=wait_event_type)
    return mock_exec.await_args_list


def _session_call(calls):
    """Return (query, params) of the call that reads pg_stat_activity."""
    for call in calls:
        query = call.args[0]
        if "pg_stat_activity" in query:
            params = call.args[1] if len(call.args) > 1 else call.kwargs.get("params")
            return query, params
    raise AssertionError("no pg_stat_activity query issued")


@pytest.mark.asyncio
@pytest.mark.parametrize("major", [16, 17, 18])
async def test_session_summary_applies_filter(major):
    query, params = _session_call(await _run(major, "Lock"))
    assert "wait_event_type ILIKE $1" in query
    assert params == ["%Lock%"]


@pytest.mark.asyncio
@pytest.mark.parametrize("major", [16, 17, 18])
async def test_session_summary_without_filter(major):
    query, params = _session_call(await _run(major, None))
    assert "ILIKE" not in query
    assert not params
