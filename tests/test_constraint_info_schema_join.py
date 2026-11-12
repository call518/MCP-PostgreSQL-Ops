"""Unit tests for the constraint queries in get_table_schema_info — no database required."""
import re
from unittest.mock import AsyncMock, patch

import pytest

from mcp_postgresql_ops import mcp_main


async def _captured_sql():
    mock = AsyncMock(return_value=[])
    with patch.object(mcp_main, "execute_query", mock):
        tool = getattr(mcp_main.get_table_schema_info, "fn", mcp_main.get_table_schema_info)
        await tool("postgres", "t", "a")
    return mock.call_args.args[0]


def _eq(sql, left, right):
    """Count `left = right` conditions in either order."""
    pat = rf"(?:{left}\s*=\s*{right}|{right}\s*=\s*{left})"
    return len(re.findall(pat, sql))


def _section(sql, start, end):
    i = sql.index(start)
    return sql[i:sql.index(end, i)]


@pytest.mark.asyncio
async def test_constraint_info_is_scoped_to_the_table():
    sql = _section(await _captured_sql(), "constraint_info AS (", "index_info AS (")
    # key_column_usage must be matched on constraint_schema,
    # and key_column_usage also on table_name, not on constraint_name alone.
    assert _eq(sql, r"kcu\.constraint_schema", r"tc\.constraint_schema") == 1
    assert _eq(sql, r"kcu\.table_name", r"tc\.table_name") == 1
    assert "constraint_column_usage" not in sql  # cannot tell which table owns the constraint


@pytest.mark.asyncio
@pytest.mark.parametrize("start,end", [("column_info AS (", "constraint_info AS (")])
async def test_column_key_lookups_are_scoped(start, end):
    sql = _section(await _captured_sql(), start, end)
    assert _eq(sql, r"kcu\.constraint_schema", r"tc\.constraint_schema") == 1
    assert _eq(sql, r"kcu\.table_name", r"tc\.table_name") == 1
    assert "constraint_column_usage" not in sql  # cannot tell which table owns the constraint
    assert "pg_constraint" in sql
