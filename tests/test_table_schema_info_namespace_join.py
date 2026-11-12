"""Unit tests for get_table_schema_info SQL — no database required."""
import re
from unittest.mock import AsyncMock, patch

import pytest

from mcp_postgresql_ops import mcp_main


async def _captured_query():
    mock = AsyncMock(return_value=[])
    with patch.object(mcp_main, "execute_query", mock):
        fn = getattr(mcp_main.get_table_schema_info, "fn", mcp_main.get_table_schema_info)
        await fn(database_name="postgres", table_name="t", schema_name="a")
    return mock.call_args.args[0]


def _norm(sql):
    return re.sub(r"\s+", " ", sql)


@pytest.mark.asyncio
async def test_table_info_pg_class_join_is_namespace_scoped():
    sql = _norm(await _captured_query())
    assert "pg_class c ON c.relname = t.table_name AND c.relnamespace = n.oid" in sql
    # pg_namespace must be joined before pg_class so n.oid is available
    assert sql.index("JOIN pg_namespace n ON n.nspname = t.table_schema") < sql.index(
        "pg_class c ON c.relname = t.table_name"
    )


@pytest.mark.asyncio
async def test_index_info_pg_class_join_is_namespace_scoped():
    sql = _norm(await _captured_query())
    assert "JOIN pg_namespace n ON n.nspname = i.schemaname" in sql
    assert "pg_class c ON c.relname = i.indexname AND c.relnamespace = n.oid" in sql
