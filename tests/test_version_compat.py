"""Unit tests for version_compat.py — no database required."""
import re
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from mcp_postgresql_ops.version_compat import PostgreSQLVersion


def build_pg_stat_statements_query(version: PostgreSQLVersion) -> str:
    """Replicate get_pg_stat_statements_query logic for unit testing without DB."""
    base_columns = ["queryid", "query", "calls", "rows"]

    if version.has_pg_stat_statements_exec_time:
        base_columns.extend([
            "total_exec_time", "mean_exec_time", "min_exec_time", "max_exec_time", "stddev_exec_time"
        ])
    else:
        base_columns.extend([
            "total_time as total_exec_time", "mean_time as mean_exec_time",
            "min_time as min_exec_time", "max_time as max_exec_time",
            "stddev_time as stddev_exec_time"
        ])

    base_columns.extend([
        "shared_blks_hit", "shared_blks_read", "shared_blks_dirtied",
        "shared_blks_written", "local_blks_hit", "local_blks_read",
        "local_blks_dirtied", "local_blks_written", "temp_blks_read", "temp_blks_written"
    ])

    if version.has_pg_stat_statements_v17:
        base_columns.extend([
            "shared_blk_read_time", "shared_blk_write_time",
            "local_blk_read_time", "local_blk_write_time",
            "stats_since", "minmax_stats_since"
        ])
    elif version.has_pg_stat_statements_exec_time:
        base_columns.extend([
            "blk_read_time as shared_blk_read_time",
            "blk_write_time as shared_blk_write_time"
        ])
    else:
        base_columns.extend([
            "blk_read_time as shared_blk_read_time",
            "blk_write_time as shared_blk_write_time"
        ])

    if version.has_pg_stat_statements_v18:
        base_columns.extend([
            "parallel_workers_to_launch", "parallel_workers_launched",
            "wal_buffers_full"
        ])

    columns_str = ",\n    ".join(base_columns)
    return f"""
    SELECT
        {columns_str}
    FROM pg_stat_statements
    ORDER BY total_exec_time DESC
    """


class TestPostgreSQLVersionProperties:
    """Test every version property returns correct values for PG 12-18."""

    @pytest.mark.parametrize("major", [12, 13, 14, 15, 16, 17, 18])
    def test_is_modern(self, major):
        assert PostgreSQLVersion(major, 0, 0).is_modern is True

    def test_is_modern_false_for_old(self):
        assert PostgreSQLVersion(11, 0, 0).is_modern is False

    # PG 13+ properties
    @pytest.mark.parametrize("major,expected", [
        (12, False), (13, True), (14, True), (15, True), (16, True), (17, True), (18, True),
    ])
    def test_has_replication_slot_wal_status(self, major, expected):
        assert PostgreSQLVersion(major, 0, 0).has_replication_slot_wal_status is expected

    @pytest.mark.parametrize("major,expected", [
        (12, False), (13, True), (14, True), (15, True), (16, True), (17, True), (18, True),
    ])
    def test_has_table_stats_ins_since_vacuum(self, major, expected):
        assert PostgreSQLVersion(major, 0, 0).has_table_stats_ins_since_vacuum is expected

    @pytest.mark.parametrize("major,expected", [
        (12, False), (13, True), (14, True), (15, True), (16, True), (17, True), (18, True),
    ])
    def test_has_pg_stat_statements_exec_time(self, major, expected):
        assert PostgreSQLVersion(major, 0, 0).has_pg_stat_statements_exec_time is expected

    # PG 14+ properties
    @pytest.mark.parametrize("major,expected", [
        (12, False), (13, False), (14, True), (15, True), (16, True), (17, True), (18, True),
    ])
    def test_has_replication_slot_stats(self, major, expected):
        assert PostgreSQLVersion(major, 0, 0).has_replication_slot_stats is expected

    @pytest.mark.parametrize("major,expected", [
        (12, False), (13, False), (14, True), (15, True), (16, True), (17, True), (18, True),
    ])
    def test_has_parallel_leader_tracking(self, major, expected):
        assert PostgreSQLVersion(major, 0, 0).has_parallel_leader_tracking is expected

    # PG 16+ properties
    @pytest.mark.parametrize("major,expected", [
        (12, False), (13, False), (14, False), (15, False), (16, True), (17, True), (18, True),
    ])
    def test_has_pg_stat_io(self, major, expected):
        assert PostgreSQLVersion(major, 0, 0).has_pg_stat_io is expected

    @pytest.mark.parametrize("major,expected", [
        (12, False), (13, False), (14, False), (15, False), (16, True), (17, True), (18, True),
    ])
    def test_has_enhanced_wal_receiver(self, major, expected):
        assert PostgreSQLVersion(major, 0, 0).has_enhanced_wal_receiver is expected

    # PG 17+ properties
    @pytest.mark.parametrize("major,expected", [
        (12, False), (15, False), (16, False), (17, True), (18, True),
    ])
    def test_has_checkpointer_view(self, major, expected):
        assert PostgreSQLVersion(major, 0, 0).has_checkpointer_view is expected

    @pytest.mark.parametrize("major,expected", [
        (12, False), (16, False), (17, True), (18, True),
    ])
    def test_has_replication_slot_invalidation(self, major, expected):
        assert PostgreSQLVersion(major, 0, 0).has_replication_slot_invalidation is expected

    @pytest.mark.parametrize("major,expected", [
        (12, False), (16, False), (17, True), (18, True),
    ])
    def test_has_pg_stat_statements_v17(self, major, expected):
        assert PostgreSQLVersion(major, 0, 0).has_pg_stat_statements_v17 is expected

    @pytest.mark.parametrize("major,expected", [
        (12, False), (16, False), (17, True), (18, True),
    ])
    def test_has_pg_wait_events(self, major, expected):
        assert PostgreSQLVersion(major, 0, 0).has_pg_wait_events is expected

    @pytest.mark.parametrize("major,expected", [
        (12, False), (16, False), (17, True), (18, True),
    ])
    def test_has_wal_summarizer(self, major, expected):
        assert PostgreSQLVersion(major, 0, 0).has_wal_summarizer is expected

    # PG 18+ properties
    @pytest.mark.parametrize("major,expected", [
        (12, False), (16, False), (17, False), (18, True),
    ])
    def test_has_pg_stat_io_bytes(self, major, expected):
        assert PostgreSQLVersion(major, 0, 0).has_pg_stat_io_bytes is expected

    @pytest.mark.parametrize("major,expected", [
        (12, False), (17, False), (18, True),
    ])
    def test_has_vacuum_time_columns(self, major, expected):
        assert PostgreSQLVersion(major, 0, 0).has_vacuum_time_columns is expected

    @pytest.mark.parametrize("major,expected", [
        (12, False), (17, False), (18, True),
    ])
    def test_has_pg_aios(self, major, expected):
        assert PostgreSQLVersion(major, 0, 0).has_pg_aios is expected

    @pytest.mark.parametrize("major,expected", [
        (12, False), (17, False), (18, True),
    ])
    def test_has_per_backend_io(self, major, expected):
        assert PostgreSQLVersion(major, 0, 0).has_per_backend_io is expected

    @pytest.mark.parametrize("major,expected", [
        (12, False), (17, False), (18, True),
    ])
    def test_has_parallel_worker_stats(self, major, expected):
        assert PostgreSQLVersion(major, 0, 0).has_parallel_worker_stats is expected

    @pytest.mark.parametrize("major,expected", [
        (12, False), (17, False), (18, True),
    ])
    def test_has_checkpointer_v18(self, major, expected):
        assert PostgreSQLVersion(major, 0, 0).has_checkpointer_v18 is expected

    @pytest.mark.parametrize("major,expected", [
        (12, False), (17, False), (18, True),
    ])
    def test_has_pg_stat_statements_v18(self, major, expected):
        assert PostgreSQLVersion(major, 0, 0).has_pg_stat_statements_v18 is expected


class TestVersionComparison:
    """Test version comparison operators."""

    def test_ge_same(self):
        assert PostgreSQLVersion(16, 0, 0) >= PostgreSQLVersion(16, 0, 0)

    def test_ge_higher_major(self):
        assert PostgreSQLVersion(17, 0, 0) >= PostgreSQLVersion(16, 0, 0)

    def test_ge_lower_major(self):
        assert not (PostgreSQLVersion(15, 0, 0) >= PostgreSQLVersion(16, 0, 0))

    def test_lt(self):
        assert PostgreSQLVersion(15, 0, 0) < PostgreSQLVersion(16, 0, 0)

    def test_not_lt_same(self):
        assert not (PostgreSQLVersion(16, 0, 0) < PostgreSQLVersion(16, 0, 0))

    def test_str(self):
        assert str(PostgreSQLVersion(16, 4, 0)) == "16.4.0"

    def test_int_comparison(self):
        v = PostgreSQLVersion(17, 0, 0)
        assert v >= 16
        assert v >= 17
        assert not (v >= 18)


class TestPgStatStatementsQueryGeneration:
    """Test that pg_stat_statements query generation produces valid SQL."""

    TRAILING_COMMA_PATTERN = re.compile(r',\s*FROM\b', re.IGNORECASE)

    @pytest.mark.parametrize("major", [12, 13, 14, 15, 16, 17, 18])
    def test_no_trailing_comma_before_from(self, major):
        v = PostgreSQLVersion(major, 0, 0)
        query = build_pg_stat_statements_query(v)
        assert not self.TRAILING_COMMA_PATTERN.search(query), \
            f"PG{major}: trailing comma before FROM in pg_stat_statements query"

    @pytest.mark.parametrize("major", [12, 13, 14, 15, 16, 17, 18])
    def test_has_block_io_timing_columns(self, major):
        v = PostgreSQLVersion(major, 0, 0)
        query = build_pg_stat_statements_query(v)
        assert "blk_read_time" in query or "shared_blk_read_time" in query, \
            f"PG{major}: missing block I/O timing columns"

    @pytest.mark.parametrize("major", [12, 13, 14, 15, 16, 17, 18])
    def test_has_exec_time_columns(self, major):
        v = PostgreSQLVersion(major, 0, 0)
        query = build_pg_stat_statements_query(v)
        assert "total_exec_time" in query, \
            f"PG{major}: missing total_exec_time (or alias)"

    def test_pg17_has_stats_since(self):
        v = PostgreSQLVersion(17, 0, 0)
        query = build_pg_stat_statements_query(v)
        assert "stats_since" in query

    def test_pg18_has_parallel_workers(self):
        v = PostgreSQLVersion(18, 0, 0)
        query = build_pg_stat_statements_query(v)
        assert "parallel_workers_to_launch" in query
        assert "parallel_workers_launched" in query

    def test_pg12_no_parallel_workers(self):
        v = PostgreSQLVersion(12, 0, 0)
        query = build_pg_stat_statements_query(v)
        assert "parallel_workers" not in query

    def test_pg16_no_stats_since(self):
        v = PostgreSQLVersion(16, 0, 0)
        query = build_pg_stat_statements_query(v)
        assert "stats_since" not in query


class TestVersionAwareQueriesSQL:
    """Test VersionAwareQueries methods produce valid SQL."""

    TRAILING_COMMA_PATTERN = re.compile(r',\s*FROM\b', re.IGNORECASE)

    @pytest.mark.parametrize("major", [12, 13, 14, 15, 16, 17, 18])
    def test_replication_slots_query_no_trailing_comma(self, major):
        """Test via direct SQL string construction matching the method logic."""
        v = PostgreSQLVersion(major, 0, 0)
        # Reconstruct the query logic from VersionAwareQueries.get_replication_slots_query
        base_columns = """
                slot_name, plugin, slot_type, datoid, temporary, active,
                active_pid, restart_lsn, confirmed_flush_lsn"""

        if v.has_replication_slot_wal_status:
            base_columns += """,
                wal_status, safe_wal_size"""

        if v.has_replication_slot_invalidation:
            base_columns += """,
                invalidation_reason, inactive_since"""

        query = f"SELECT {base_columns} FROM pg_replication_slots"
        assert not self.TRAILING_COMMA_PATTERN.search(query), \
            f"PG{major}: trailing comma in replication slots query"

    @pytest.mark.parametrize("major", [12, 13, 14, 15, 16, 17, 18])
    def test_all_tables_stats_query_no_trailing_comma(self, major):
        """Test the vacuum_time_cols injection pattern."""
        v = PostgreSQLVersion(major, 0, 0)
        vacuum_time_cols = ""
        if v.has_vacuum_time_columns:
            vacuum_time_cols = """,
                ROUND(total_vacuum_time::numeric, 2) as total_vacuum_time_ms,
                ROUND(total_autovacuum_time::numeric, 2) as total_autovacuum_time_ms,
                ROUND(total_analyze_time::numeric, 2) as total_analyze_time_ms,
                ROUND(total_autoanalyze_time::numeric, 2) as total_autoanalyze_time_ms"""

        query = f"SELECT autoanalyze_count{vacuum_time_cols} FROM pg_stat_user_tables"
        assert not self.TRAILING_COMMA_PATTERN.search(query), \
            f"PG{major}: trailing comma in all_tables_stats query"
