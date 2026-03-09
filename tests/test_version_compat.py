"""Unit tests for version_compat.py — no database required."""
import re
import sys
import os
from unittest.mock import AsyncMock, patch
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from mcp_postgresql_ops.version_compat import (
    PostgreSQLVersion,
    VersionAwareQueries,
    get_pg_stat_statements_query,
)


async def _mock_version_call(func, major, *args, **kwargs):
    """Call an async query builder with get_postgresql_version mocked to return the given major version."""
    version = PostgreSQLVersion(major, 0, 0)
    with patch("mcp_postgresql_ops.version_compat.get_postgresql_version", new_callable=AsyncMock, return_value=version):
        return await func(*args, **kwargs)


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

    def test_eq_same(self):
        assert PostgreSQLVersion(16, 0, 0) == PostgreSQLVersion(16, 0, 0)

    def test_eq_different(self):
        assert not (PostgreSQLVersion(16, 0, 0) == PostgreSQLVersion(17, 0, 0))

    def test_ne(self):
        assert PostgreSQLVersion(16, 0, 0) != PostgreSQLVersion(17, 0, 0)

    def test_le(self):
        assert PostgreSQLVersion(15, 0, 0) <= PostgreSQLVersion(16, 0, 0)
        assert PostgreSQLVersion(16, 0, 0) <= PostgreSQLVersion(16, 0, 0)
        assert not (PostgreSQLVersion(17, 0, 0) <= PostgreSQLVersion(16, 0, 0))

    def test_gt(self):
        assert PostgreSQLVersion(17, 0, 0) > PostgreSQLVersion(16, 0, 0)
        assert not (PostgreSQLVersion(16, 0, 0) > PostgreSQLVersion(16, 0, 0))

    def test_hash(self):
        a = PostgreSQLVersion(16, 0, 0)
        b = PostgreSQLVersion(16, 0, 0)
        assert hash(a) == hash(b)
        assert {a, b} == {a}

    def test_int_eq(self):
        assert PostgreSQLVersion(17, 0, 0) == 17
        assert not (PostgreSQLVersion(17, 0, 0) == 16)


class TestPgStatStatementsQueryGeneration:
    """Test that get_pg_stat_statements_query produces valid SQL for all versions."""

    TRAILING_COMMA_PATTERN = re.compile(r',\s*FROM\b', re.IGNORECASE)

    @pytest.mark.parametrize("major", [12, 13, 14, 15, 16, 17, 18])
    async def test_no_trailing_comma_before_from(self, major):
        query = await _mock_version_call(get_pg_stat_statements_query, major)
        assert not self.TRAILING_COMMA_PATTERN.search(query), \
            f"PG{major}: trailing comma before FROM in pg_stat_statements query"

    @pytest.mark.parametrize("major", [12, 13, 14, 15, 16, 17, 18])
    async def test_has_block_io_timing_columns(self, major):
        query = await _mock_version_call(get_pg_stat_statements_query, major)
        assert "blk_read_time" in query or "shared_blk_read_time" in query, \
            f"PG{major}: missing block I/O timing columns"

    @pytest.mark.parametrize("major", [12, 13, 14, 15, 16, 17, 18])
    async def test_has_exec_time_columns(self, major):
        query = await _mock_version_call(get_pg_stat_statements_query, major)
        assert "total_exec_time" in query, \
            f"PG{major}: missing total_exec_time (or alias)"

    async def test_pg17_has_stats_since(self):
        query = await _mock_version_call(get_pg_stat_statements_query, 17)
        assert "stats_since" in query

    async def test_pg18_has_parallel_workers(self):
        query = await _mock_version_call(get_pg_stat_statements_query, 18)
        assert "parallel_workers_to_launch" in query
        assert "parallel_workers_launched" in query

    async def test_pg12_no_parallel_workers(self):
        query = await _mock_version_call(get_pg_stat_statements_query, 12)
        assert "parallel_workers" not in query

    async def test_pg16_no_stats_since(self):
        query = await _mock_version_call(get_pg_stat_statements_query, 16)
        assert "stats_since" not in query


class TestVersionAwareQueriesSQL:
    """Test VersionAwareQueries methods produce valid SQL via mocked version detection."""

    TRAILING_COMMA_PATTERN = re.compile(r',\s*FROM\b', re.IGNORECASE)

    @pytest.mark.parametrize("major", [12, 13, 14, 15, 16, 17, 18])
    async def test_replication_slots_query_no_trailing_comma(self, major):
        query = await _mock_version_call(VersionAwareQueries.get_replication_slots_query, major)
        assert not self.TRAILING_COMMA_PATTERN.search(query), \
            f"PG{major}: trailing comma in replication slots query"

    @pytest.mark.parametrize("major", [12, 13, 14, 15, 16, 17, 18])
    async def test_replication_slots_query_has_base_columns(self, major):
        query = await _mock_version_call(VersionAwareQueries.get_replication_slots_query, major)
        assert "slot_name" in query
        assert "restart_lsn" in query

    async def test_replication_slots_pg17_has_invalidation(self):
        query = await _mock_version_call(VersionAwareQueries.get_replication_slots_query, 17)
        assert "invalidation_reason" in query
        assert "inactive_since" in query

    async def test_replication_slots_pg12_no_wal_status(self):
        query = await _mock_version_call(VersionAwareQueries.get_replication_slots_query, 12)
        assert "NULL::text as wal_status" in query

    @pytest.mark.parametrize("major", [12, 13, 14, 15, 16, 17, 18])
    async def test_all_tables_stats_query_no_trailing_comma(self, major):
        query = await _mock_version_call(VersionAwareQueries.get_all_tables_stats_query, major)
        assert not self.TRAILING_COMMA_PATTERN.search(query), \
            f"PG{major}: trailing comma in all_tables_stats query"

    async def test_all_tables_stats_pg18_has_vacuum_time(self):
        query = await _mock_version_call(VersionAwareQueries.get_all_tables_stats_query, 18)
        assert "total_vacuum_time" in query
        assert "total_autovacuum_time" in query

    async def test_all_tables_stats_pg16_no_vacuum_time(self):
        query = await _mock_version_call(VersionAwareQueries.get_all_tables_stats_query, 16)
        assert "total_vacuum_time" not in query

    async def test_all_tables_stats_pg13_has_ins_since_vacuum(self):
        query = await _mock_version_call(VersionAwareQueries.get_all_tables_stats_query, 13)
        assert "inserted_since_vacuum" in query

    async def test_all_tables_stats_pg12_uses_null_ins_since_vacuum(self):
        query = await _mock_version_call(VersionAwareQueries.get_all_tables_stats_query, 12)
        assert "NULL::bigint as inserted_since_vacuum" in query
        assert "n_ins_since_vacuum" not in query

    async def test_all_tables_stats_include_system(self):
        query = await _mock_version_call(
            VersionAwareQueries.get_all_tables_stats_query, 16, include_system=True
        )
        assert "pg_stat_all_tables" in query

    async def test_all_tables_stats_user_only(self):
        query = await _mock_version_call(
            VersionAwareQueries.get_all_tables_stats_query, 16, include_system=False
        )
        assert "pg_stat_user_tables" in query
