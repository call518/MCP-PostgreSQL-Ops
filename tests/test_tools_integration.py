"""Integration tests: call every MCP tool against each PG version.

Requires Docker Compose test stack running (tests/docker/docker-compose.test.yml).
"""
import pytest

import mcp_postgresql_ops.mcp_main as _mcp_main


def _fn(name: str):
    """Extract the raw callable from a FunctionTool (fastmcp >= 2.14) or return as-is."""
    tool = getattr(_mcp_main, name)
    return getattr(tool, "fn", tool)


get_lock_monitoring = _fn("get_lock_monitoring")
get_wal_status = _fn("get_wal_status")
get_replication_status = _fn("get_replication_status")
get_server_info = _fn("get_server_info")
get_current_database_info = _fn("get_current_database_info")
get_database_list = _fn("get_database_list")
get_table_list = _fn("get_table_list")
get_user_list = _fn("get_user_list")
get_table_schema_info = _fn("get_table_schema_info")
get_database_schema_info = _fn("get_database_schema_info")
get_table_relationships = _fn("get_table_relationships")
get_active_connections = _fn("get_active_connections")
get_pg_stat_statements_top_queries = _fn("get_pg_stat_statements_top_queries")
get_pg_stat_monitor_recent_queries = _fn("get_pg_stat_monitor_recent_queries")
get_database_size_info = _fn("get_database_size_info")
get_table_size_info = _fn("get_table_size_info")
get_postgresql_config = _fn("get_postgresql_config")
get_index_usage_stats = _fn("get_index_usage_stats")
get_vacuum_analyze_stats = _fn("get_vacuum_analyze_stats")
get_table_bloat_analysis = _fn("get_table_bloat_analysis")
get_database_bloat_overview = _fn("get_database_bloat_overview")
get_autovacuum_status = _fn("get_autovacuum_status")
get_autovacuum_activity = _fn("get_autovacuum_activity")
get_running_vacuum_operations = _fn("get_running_vacuum_operations")
get_vacuum_effectiveness_analysis = _fn("get_vacuum_effectiveness_analysis")
get_database_stats = _fn("get_database_stats")
get_bgwriter_stats = _fn("get_bgwriter_stats")
get_io_stats = _fn("get_io_stats")
get_table_io_stats = _fn("get_table_io_stats")
get_index_io_stats = _fn("get_index_io_stats")
get_all_tables_stats = _fn("get_all_tables_stats")
get_user_functions_stats = _fn("get_user_functions_stats")
get_database_conflicts_stats = _fn("get_database_conflicts_stats")
get_wait_events = _fn("get_wait_events")
get_wal_summarizer_status = _fn("get_wal_summarizer_status")
get_async_io_status = _fn("get_async_io_status")
get_per_backend_io_stats = _fn("get_per_backend_io_stats")


pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("docker_compose_pg")]


def assert_tool_result(result, tool_name):
    """Common assertions for all tool results."""
    assert isinstance(result, str), f"{tool_name} did not return a string"
    assert len(result) > 0, f"{tool_name} returned empty string"
    # Should not contain Python tracebacks
    assert "Traceback" not in result, f"{tool_name} returned a traceback: {result[:500]}"


FK_SCOPE_DDL = """
DROP SCHEMA IF EXISTS fkscope_a CASCADE;
DROP SCHEMA IF EXISTS fkscope_b CASCADE;
CREATE SCHEMA fkscope_a;
CREATE SCHEMA fkscope_b;
CREATE TABLE fkscope_a.p (id int PRIMARY KEY);
CREATE TABLE fkscope_b.p (id int PRIMARY KEY);
-- same FK name on two tables of one schema and on a table in another schema
CREATE TABLE fkscope_a.t (id int PRIMARY KEY, pid int,
    CONSTRAINT fk_p FOREIGN KEY (pid) REFERENCES fkscope_a.p(id));
CREATE TABLE fkscope_a.u (id int PRIMARY KEY, pid int,
    CONSTRAINT fk_p FOREIGN KEY (pid) REFERENCES fkscope_a.p(id));
CREATE TABLE fkscope_b.t (id int PRIMARY KEY, pid int,
    CONSTRAINT fk_p FOREIGN KEY (pid) REFERENCES fkscope_b.p(id));
-- composite FK with reordered columns, and one column in two FKs (cross-schema)
CREATE TABLE fkscope_a.cp (x int, y int, PRIMARY KEY (x, y));
CREATE TABLE fkscope_a.c (id int PRIMARY KEY, cy int, cx int, pid int,
    CONSTRAINT fk_c FOREIGN KEY (cy, cx) REFERENCES fkscope_a.cp (y, x),
    CONSTRAINT fk_c_p FOREIGN KEY (pid) REFERENCES fkscope_a.p(id),
    CONSTRAINT fk_c_p2 FOREIGN KEY (pid) REFERENCES fkscope_b.p(id));
-- FK to a partitioned table: PostgreSQL adds per-partition clone constraints
CREATE TABLE fkscope_a.pp (id int PRIMARY KEY) PARTITION BY RANGE (id);
CREATE TABLE fkscope_a.pp1 PARTITION OF fkscope_a.pp FOR VALUES FROM (0) TO (100);
CREATE TABLE fkscope_a.pp2 PARTITION OF fkscope_a.pp FOR VALUES FROM (100) TO (200);
CREATE TABLE fkscope_a.r (id int PRIMARY KEY, ppid int,
    CONSTRAINT fk_r_pp FOREIGN KEY (ppid) REFERENCES fkscope_a.pp(id)
    ON DELETE CASCADE ON UPDATE SET NULL);
"""


def _rows(result, prefix):
    """Return output lines of one section, e.g. 'FK_OUTBOUND'."""
    return [line for line in result.splitlines() if line.startswith(prefix + " |")]


# ============================================================
# Core tools (PG 12+) — should work on all versions
# ============================================================

class TestCoreTools:
    """Tools that work on all supported PG versions (12+)."""

    async def test_get_lock_monitoring(self, setup_env):
        result = await get_lock_monitoring()
        assert_tool_result(result, "get_lock_monitoring")

    async def test_get_wal_status(self, setup_env):
        result = await get_wal_status()
        assert_tool_result(result, "get_wal_status")

    async def test_get_replication_status(self, setup_env):
        result = await get_replication_status()
        assert_tool_result(result, "get_replication_status")

    async def test_get_server_info(self, setup_env):
        major, _ = setup_env
        result = await get_server_info()
        assert_tool_result(result, "get_server_info")
        # Should mention the PG version
        assert str(major) in result, f"get_server_info should mention PG {major}"

    async def test_get_current_database_info(self, setup_env):
        result = await get_current_database_info()
        assert_tool_result(result, "get_current_database_info")
        assert "testdb" in result

    async def test_get_database_list(self, setup_env):
        result = await get_database_list()
        assert_tool_result(result, "get_database_list")
        assert "testdb" in result

    async def test_get_table_list(self, setup_env):
        result = await get_table_list()
        assert_tool_result(result, "get_table_list")

    async def test_get_user_list(self, setup_env):
        result = await get_user_list()
        assert_tool_result(result, "get_user_list")
        assert "postgres" in result

    async def test_get_table_schema_info(self, setup_env):
        result = await get_table_schema_info(database_name="testdb", table_name="customers", schema_name="sales")
        assert_tool_result(result, "get_table_schema_info")
        assert "customer" in result.lower()

    async def test_get_database_schema_info(self, setup_env):
        result = await get_database_schema_info(database_name="testdb")
        assert_tool_result(result, "get_database_schema_info")

    async def test_get_table_relationships(self, setup_env):
        result = await get_table_relationships(database_name="testdb", schema_name="sales")
        assert_tool_result(result, "get_table_relationships")

    async def test_get_active_connections(self, setup_env):
        result = await get_active_connections()
        assert_tool_result(result, "get_active_connections")

    async def test_get_pg_stat_statements(self, setup_env):
        result = await get_pg_stat_statements_top_queries(limit=5)
        assert_tool_result(result, "get_pg_stat_statements_top_queries")

    async def test_get_pg_stat_monitor(self, setup_env):
        # pg_stat_monitor extension may not be installed — that's OK
        result = await get_pg_stat_monitor_recent_queries(limit=5)
        assert_tool_result(result, "get_pg_stat_monitor_recent_queries")

    async def test_get_database_size_info(self, setup_env):
        result = await get_database_size_info()
        assert_tool_result(result, "get_database_size_info")
        assert "testdb" in result

    async def test_get_table_size_info(self, setup_env):
        result = await get_table_size_info(schema_name="sales")
        assert_tool_result(result, "get_table_size_info")

    async def test_get_postgresql_config(self, setup_env):
        result = await get_postgresql_config()
        assert_tool_result(result, "get_postgresql_config")

    async def test_get_postgresql_config_filtered(self, setup_env):
        result = await get_postgresql_config(filter_text="shared_preload")
        assert_tool_result(result, "get_postgresql_config(filtered)")
        assert "pg_stat_statements" in result

    async def test_get_index_usage_stats(self, setup_env):
        result = await get_index_usage_stats()
        assert_tool_result(result, "get_index_usage_stats")

    async def test_get_vacuum_analyze_stats(self, setup_env):
        result = await get_vacuum_analyze_stats()
        assert_tool_result(result, "get_vacuum_analyze_stats")

    async def test_get_table_bloat_analysis(self, setup_env):
        result = await get_table_bloat_analysis(min_dead_tuples=0)
        assert_tool_result(result, "get_table_bloat_analysis")

    async def test_get_database_bloat_overview(self, setup_env):
        result = await get_database_bloat_overview()
        assert_tool_result(result, "get_database_bloat_overview")

    async def test_get_autovacuum_status(self, setup_env):
        result = await get_autovacuum_status()
        assert_tool_result(result, "get_autovacuum_status")

    async def test_get_autovacuum_activity(self, setup_env):
        result = await get_autovacuum_activity()
        assert_tool_result(result, "get_autovacuum_activity")

    async def test_get_running_vacuum_operations(self, setup_env):
        result = await get_running_vacuum_operations()
        assert_tool_result(result, "get_running_vacuum_operations")

    async def test_get_vacuum_effectiveness_analysis(self, setup_env):
        result = await get_vacuum_effectiveness_analysis()
        assert_tool_result(result, "get_vacuum_effectiveness_analysis")

    async def test_get_database_stats(self, setup_env):
        result = await get_database_stats()
        assert_tool_result(result, "get_database_stats")

    async def test_get_bgwriter_stats(self, setup_env):
        result = await get_bgwriter_stats()
        assert_tool_result(result, "get_bgwriter_stats")

    async def test_get_io_stats(self, setup_env):
        result = await get_io_stats(limit=5)
        assert_tool_result(result, "get_io_stats")

    async def test_get_table_io_stats(self, setup_env):
        result = await get_table_io_stats(schema_name="sales")
        assert_tool_result(result, "get_table_io_stats")

    async def test_get_index_io_stats(self, setup_env):
        result = await get_index_io_stats(schema_name="sales")
        assert_tool_result(result, "get_index_io_stats")

    async def test_get_all_tables_stats(self, setup_env):
        result = await get_all_tables_stats()
        assert_tool_result(result, "get_all_tables_stats")

    async def test_get_user_functions_stats(self, setup_env):
        result = await get_user_functions_stats()
        assert_tool_result(result, "get_user_functions_stats")

    async def test_get_database_conflicts_stats(self, setup_env):
        result = await get_database_conflicts_stats()
        assert_tool_result(result, "get_database_conflicts_stats")


# ============================================================
# Foreign key lookups must not mix same-named constraints (#85)
# ============================================================

class TestForeignKeyScoping:

    @pytest.fixture
    async def fk_schema(self, setup_env):
        import asyncpg

        import mcp_postgresql_ops.functions as fn

        conn = await asyncpg.connect(**fn.POSTGRES_CONFIG)
        try:
            await conn.execute(FK_SCOPE_DDL)
            yield
        finally:
            await conn.execute("DROP SCHEMA IF EXISTS fkscope_a, fkscope_b CASCADE")
            await conn.close()

    async def test_relationships_outbound_is_scoped_to_table(self, fk_schema):
        result = await get_table_relationships(database_name="testdb", table_name="t", schema_name="fkscope_a")
        assert_tool_result(result, "get_table_relationships")
        rows = _rows(result, "FK_OUTBOUND")
        assert len(rows) == 1, result
        assert "pid → fkscope_a.p" in rows[0]

    async def test_relationships_inbound_lists_each_fk_once(self, fk_schema):
        result = await get_table_relationships(database_name="testdb", table_name="p", schema_name="fkscope_a")
        rows = _rows(result, "FK_INBOUND")
        sources = sorted(row.split(" | ")[3] for row in rows)
        assert sources == ["fkscope_a.c → pid", "fkscope_a.t → pid", "fkscope_a.u → pid"], result

    async def test_relationships_skip_partition_clones(self, fk_schema):
        result = await get_table_relationships(database_name="testdb", table_name="r", schema_name="fkscope_a")
        rows = _rows(result, "FK_OUTBOUND")
        assert len(rows) == 1, result
        assert "FK: fk_r_pp" in rows[0] and "ppid → fkscope_a.pp |" in rows[0]
        assert "Update: SET NULL, Delete: CASCADE" in rows[0]

    async def test_relationships_overview_pairs_are_correct(self, fk_schema):
        result = await get_table_relationships(database_name="testdb")
        rows = [r for r in _rows(result, "RELATIONSHIP") if "fkscope_" in r]
        pairs = sorted(row.split(" | ")[1] + " " + row.split(" | ")[2] for row in rows)
        assert pairs == [
            "fk_c fkscope_a.c → fkscope_a.cp",
            "fk_c fkscope_a.c → fkscope_a.cp",
            "fk_c_p fkscope_a.c → fkscope_a.p",
            "fk_c_p2 fkscope_a.c → fkscope_b.p",
            "fk_p fkscope_a.t → fkscope_a.p",
            "fk_p fkscope_a.u → fkscope_a.p",
            "fk_p fkscope_b.t → fkscope_b.p",
            "fk_r_pp fkscope_a.r → fkscope_a.pp",
        ], result

    async def test_schema_info_one_row_per_fk_column_with_schema(self, fk_schema):
        result = await get_table_schema_info(database_name="testdb", table_name="c", schema_name="fkscope_a")
        pid_rows = [r for r in _rows(result, "COLUMN") if r.startswith("COLUMN | pid |")]
        assert len(pid_rows) == 1, result
        assert "| fkscope_a.p, fkscope_b.p | id, id |" in pid_rows[0]
        assert "| fkscope_a.cp(y, x) |" in result

    async def test_schema_info_skips_partition_clones(self, fk_schema):
        result = await get_table_schema_info(database_name="testdb", table_name="r", schema_name="fkscope_a")
        fk_rows = [r for r in _rows(result, "CONSTRAINT") if "FOREIGN KEY" in r]
        assert len(fk_rows) == 1, result
        assert "| fkscope_a.pp(id) |" in fk_rows[0]


# ============================================================
# Version-gated tools — test behavior on all versions
# ============================================================

class TestVersionGatedTools:
    """Tools with version-specific behavior. Test they work or degrade gracefully."""

    async def test_get_wait_events(self, setup_env):
        """PG 17+ uses pg_wait_events catalog; PG 12-16 falls back to pg_stat_activity."""
        major, _ = setup_env
        result = await get_wait_events()
        assert_tool_result(result, "get_wait_events")
        if major >= 17:
            assert "wait_event" in result.lower() or "Wait Event" in result

    async def test_get_wait_events_filtered(self, setup_env):
        """Test with wait_event_type filter."""
        result = await get_wait_events(wait_event_type="Lock")
        assert_tool_result(result, "get_wait_events(filtered)")

    async def test_get_wal_summarizer_status(self, setup_env):
        """PG 17+ returns data; PG 12-16 returns version notice."""
        major, _ = setup_env
        result = await get_wal_summarizer_status()
        assert_tool_result(result, "get_wal_summarizer_status")
        if major < 17:
            assert "not available" in result.lower() or "17" in result

    async def test_get_async_io_status(self, setup_env):
        """PG 18+ returns data; PG 12-17 returns version notice."""
        major, _ = setup_env
        result = await get_async_io_status()
        assert_tool_result(result, "get_async_io_status")
        if major < 18:
            assert "not available" in result.lower() or "18" in result

    async def test_get_per_backend_io_stats(self, setup_env):
        """PG 18+ returns data; PG 12-17 returns version notice."""
        major, _ = setup_env
        result = await get_per_backend_io_stats(limit=5)
        assert_tool_result(result, "get_per_backend_io_stats")
        if major < 18:
            assert "not available" in result.lower() or "18" in result


# ============================================================
# Version-specific feature verification
# ============================================================

class TestVersionSpecificFeatures:
    """Verify version-specific columns/features appear in output."""

    async def test_bgwriter_checkpointer_split_pg17(self, setup_env):
        """PG 17+ should show separate Checkpointer component."""
        major, _ = setup_env
        result = await get_bgwriter_stats()
        assert_tool_result(result, "get_bgwriter_stats")
        if major >= 17:
            assert "Checkpointer" in result or "checkpointer" in result
        else:
            assert "Combined" in result or "combined" in result.lower() or "BGWriter" in result

    async def test_bgwriter_pg18_extra_cols(self, setup_env):
        """PG 18 should include completed_checkpoints and slru_buffers_written."""
        major, _ = setup_env
        if major < 18:
            pytest.skip("PG 18+ only")
        result = await get_bgwriter_stats()
        assert "completed_checkpoints" in result or "slru" in result.lower()

    async def test_io_stats_pg18_bytes(self, setup_env):
        """PG 18 should include byte columns in IO stats."""
        major, _ = setup_env
        if major < 18:
            pytest.skip("PG 18+ only")
        result = await get_io_stats(limit=5)
        assert "read_bytes" in result or "write_bytes" in result

    async def test_vacuum_stats_pg18_time_cols(self, setup_env):
        """PG 18 should include vacuum time columns."""
        major, _ = setup_env
        if major < 18:
            pytest.skip("PG 18+ only")
        result = await get_vacuum_analyze_stats()
        assert "vacuum_time" in result.lower() or "total_vacuum_time" in result

    async def test_all_tables_stats_pg18_vacuum_time(self, setup_env):
        """PG 18 should include vacuum time columns in all tables stats."""
        major, _ = setup_env
        if major < 18:
            pytest.skip("PG 18+ only")
        result = await get_all_tables_stats()
        assert "vacuum_time" in result.lower() or "total_vacuum_time" in result

    async def test_database_stats_pg18_parallel_workers(self, setup_env):
        """PG 18 should include parallel worker stats."""
        major, _ = setup_env
        if major < 18:
            pytest.skip("PG 18+ only")
        result = await get_database_stats()
        assert "parallel_workers" in result.lower() or "parallel" in result.lower()

    async def test_replication_status_pg17_invalidation(self, setup_env):
        """PG 17+ replication slots should include invalidation_reason column."""
        major, _ = setup_env
        if major < 17:
            pytest.skip("PG 17+ only")
        # This test just verifies the query doesn't error; actual slots may be empty
        result = await get_replication_status()
        assert_tool_result(result, "get_replication_status")

    async def test_server_info_features_dict(self, setup_env):
        """Verify get_server_info reports correct feature availability."""
        major, _ = setup_env
        result = await get_server_info()
        if major >= 17:
            assert "Checkpointer View" in result
        if major >= 16:
            assert "pg_stat_io" in result
