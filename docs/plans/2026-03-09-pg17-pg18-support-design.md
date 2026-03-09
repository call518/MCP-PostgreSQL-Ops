# PostgreSQL 17 & 18 Feature Support Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add comprehensive PostgreSQL 17 and 18 support to MCP-PostgreSQL-Ops, including new version properties, enhanced existing tools with new columns, new monitoring tools, and fixed version compatibility bugs.

**Architecture:** Extend `version_compat.py` with PG 17/18 version properties and query builders. Modify existing tools in `mcp_main.py` to use version-aware queries that expose new PG 17/18 columns. Add 4 new MCP tools for PG 17/18 specific views. Fix the `has_checkpointer_split` bug that currently only returns true for PG 15.

**Tech Stack:** Python 3.12, FastMCP, asyncpg, PostgreSQL 12-18

---

## Task 1: Fix `has_checkpointer_split` Bug and Add PG 17/18 Version Properties

**Files:**
- Modify: `src/mcp_postgresql_ops/version_compat.py`

**Context:** The `has_checkpointer_split` property currently returns `True` only for PG 15 (`self.major == 15`), but `pg_stat_checkpointer` exists in PG 15+ and `buffers_backend`/`buffers_backend_fsync` were removed from `pg_stat_bgwriter` in PG 17+. The bgwriter tool's else branch uses the PG 12-14 combined view for PG 16+ which is wrong — PG 16+ also has the split views.

**Step 1: Add new version properties to PostgreSQLVersion class**

Add after `has_pg_stat_statements_exec_time` (line 82):

```python
    @property
    def has_checkpointer_view(self) -> bool:
        """Check if pg_stat_checkpointer view exists (15+)."""
        return self.major >= 15

    @property
    def has_bgwriter_buffers_backend(self) -> bool:
        """Check if pg_stat_bgwriter has buffers_backend/buffers_backend_fsync (12-16, removed in 17)."""
        return self.major < 17

    @property
    def has_replication_slot_invalidation(self) -> bool:
        """Check if pg_replication_slots has invalidation_reason and inactive_since (17+)."""
        return self.major >= 17

    @property
    def has_pg_stat_statements_v17(self) -> bool:
        """Check if pg_stat_statements has stats_since, local_blk_read/write_time (17+)."""
        return self.major >= 17

    @property
    def has_vacuum_progress_indexes(self) -> bool:
        """Check if pg_stat_progress_vacuum has indexes_total/indexes_processed (17+)."""
        return self.major >= 17

    @property
    def has_pg_wait_events(self) -> bool:
        """Check if pg_wait_events view exists (17+)."""
        return self.major >= 17

    @property
    def has_wal_summarizer(self) -> bool:
        """Check if WAL summarizer functions exist for incremental backup (17+)."""
        return self.major >= 17

    @property
    def has_transaction_timeout(self) -> bool:
        """Check if transaction_timeout GUC exists (17+)."""
        return self.major >= 17

    @property
    def has_pg_stat_io_bytes(self) -> bool:
        """Check if pg_stat_io has read_bytes/write_bytes/extend_bytes columns (18+)."""
        return self.major >= 18

    @property
    def has_vacuum_time_columns(self) -> bool:
        """Check if pg_stat_*_tables has total_vacuum_time etc. (18+)."""
        return self.major >= 18

    @property
    def has_pg_aios(self) -> bool:
        """Check if pg_aios view exists for async I/O monitoring (18+)."""
        return self.major >= 18

    @property
    def has_per_backend_io(self) -> bool:
        """Check if pg_stat_get_backend_io() function exists (18+)."""
        return self.major >= 18

    @property
    def has_parallel_worker_stats(self) -> bool:
        """Check if pg_stat_database has parallel_workers_to_launch/launched (18+)."""
        return self.major >= 18

    @property
    def has_checkpointer_v18(self) -> bool:
        """Check if pg_stat_checkpointer has num_done and slru_written (18+)."""
        return self.major >= 18

    @property
    def has_pg_stat_statements_v18(self) -> bool:
        """Check if pg_stat_statements has parallel_workers_* and wal_buffers_full (18+)."""
        return self.major >= 18

    @property
    def has_idle_replication_slot_timeout(self) -> bool:
        """Check if idle_replication_slot_timeout GUC exists (18+)."""
        return self.major >= 18

    @property
    def has_pg_stat_wal_removed_columns(self) -> bool:
        """Check if pg_stat_wal had wal_write/wal_sync/wal_write_time/wal_sync_time removed (18+)."""
        return self.major >= 18
```

**Step 2: Fix `has_checkpointer_split` deprecation**

Keep the existing property but add a deprecation note in its docstring. It's used in `mcp_main.py` so we need to update callers too (Task 2).

```python
    @property
    def has_checkpointer_split(self) -> bool:
        """Check if checkpointer stats are in separate view (15+). Deprecated: use has_checkpointer_view."""
        return self.major >= 15
```

**Step 3: Update default version fallback from 17 to 18**

In `get_postgresql_version()`, change the fallback from `PostgreSQLVersion(17, 0, 0)` to `PostgreSQLVersion(18, 0, 0)` (lines 121 and 127).

**Step 4: Update `check_feature_availability()` dict**

Add new features to the dict at line 143:

```python
    feature_requirements = {
        'pg_stat_io': version.has_pg_stat_io,
        'checkpointer_split': version.has_checkpointer_view,
        'enhanced_wal_receiver': version.has_enhanced_wal_receiver,
        'replication_slot_stats': version.has_replication_slot_stats,
        'parallel_leader_tracking': version.has_parallel_leader_tracking,
        'pg_wait_events': version.has_pg_wait_events,
        'wal_summarizer': version.has_wal_summarizer,
        'pg_aios': version.has_pg_aios,
        'per_backend_io': version.has_per_backend_io,
        'vacuum_time_columns': version.has_vacuum_time_columns,
        'pg_stat_io_bytes': version.has_pg_stat_io_bytes,
    }
```

**Step 5: Commit**

```bash
git add src/mcp_postgresql_ops/version_compat.py
git commit -m "feat: add PG 17/18 version properties and fix checkpointer_split bug"
```

---

## Task 2: Fix bgwriter_stats Tool for PG 15-18 Compatibility

**Files:**
- Modify: `src/mcp_postgresql_ops/mcp_main.py` (the `get_bgwriter_stats` tool, around line 2854)

**Context:** The current code has 2 branches: PG 15 only (`has_checkpointer_split`) and "everything else" which uses `pg_stat_bgwriter` columns that don't exist in PG 16+. We need 3 branches:
- PG 12-14: Combined bgwriter view with all columns including `buffers_backend`, `checkpoint_*` columns
- PG 15-16: Split views (`pg_stat_checkpointer` + `pg_stat_bgwriter` with `buffers_backend`)
- PG 17-18: Split views but `buffers_backend`/`buffers_backend_fsync` removed from bgwriter

For PG 18, also include `num_done` and `slru_written` from `pg_stat_checkpointer`.

**Step 1: Rewrite the get_bgwriter_stats tool**

Replace the version branching logic (starting around line 2882) with:

```python
        pg_version = await get_postgresql_version()

        if pg_version.has_checkpointer_view:
            # PG 15+: Separate checkpointer view
            checkpointer_extra = ""
            if pg_version.has_checkpointer_v18:
                checkpointer_extra = """
                    num_done as completed_checkpoints,
                    slru_written as slru_buffers_written,"""

            query = f"""
            SELECT
                'Checkpointer (PG15+)' as component,
                num_timed as scheduled_checkpoints,
                num_requested as requested_checkpoints,
                num_timed + num_requested as total_checkpoints,
                CASE
                    WHEN (num_timed + num_requested) > 0 THEN
                        ROUND((num_timed::numeric / (num_timed + num_requested)) * 100, 2)
                    ELSE 0
                END as scheduled_checkpoint_ratio_percent,
                ROUND(write_time::numeric, 2) as checkpoint_write_time_ms,
                ROUND(sync_time::numeric, 2) as checkpoint_sync_time_ms,
                ROUND((write_time + sync_time)::numeric, 2) as total_checkpoint_time_ms,
                buffers_written as buffers_written_by_checkpoints,{checkpointer_extra}
                stats_reset as stats_reset_time
            FROM pg_stat_checkpointer
            UNION ALL
            SELECT
                'Background Writer (PG15+)' as component,
                0 as scheduled_checkpoints,
                0 as requested_checkpoints,
                0 as total_checkpoints,
                0 as scheduled_checkpoint_ratio_percent,
                0 as checkpoint_write_time_ms,
                0 as checkpoint_sync_time_ms,
                0 as total_checkpoint_time_ms,
                0 as buffers_written_by_checkpoints,{('0 as completed_checkpoints, 0 as slru_buffers_written,') if pg_version.has_checkpointer_v18 else ''}
                stats_reset as stats_reset_time
            FROM pg_stat_bgwriter
            """
            explanation = f"PostgreSQL {pg_version} detected - using separate checkpointer and bgwriter views"
        else:
            # PG 12-14: Combined bgwriter view
            query = """
            SELECT
                'Combined BGWriter (PG12-14)' as component,
                checkpoints_timed as scheduled_checkpoints,
                checkpoints_req as requested_checkpoints,
                checkpoints_timed + checkpoints_req as total_checkpoints,
                CASE
                    WHEN (checkpoints_timed + checkpoints_req) > 0 THEN
                        ROUND((checkpoints_timed::numeric / (checkpoints_timed + checkpoints_req)) * 100, 2)
                    ELSE 0
                END as scheduled_checkpoint_ratio_percent,
                ROUND(checkpoint_write_time::numeric, 2) as checkpoint_write_time_ms,
                ROUND(checkpoint_sync_time::numeric, 2) as checkpoint_sync_time_ms,
                ROUND((checkpoint_write_time + checkpoint_sync_time)::numeric, 2) as total_checkpoint_time_ms,
                buffers_checkpoint as buffers_written_by_checkpoints,
                buffers_clean as buffers_written_by_bgwriter,
                buffers_backend as buffers_written_by_backend,
                buffers_backend_fsync as backend_fsync_calls,
                buffers_alloc as buffers_allocated,
                maxwritten_clean as bgwriter_maxwritten_stops,
                stats_reset as stats_reset_time
            FROM pg_stat_bgwriter
            """
            explanation = f"PostgreSQL {pg_version} detected - using combined bgwriter view"
```

**Step 2: Update server_info tool feature list**

In `get_server_info` (around line 435), update the features dict to replace `'Checkpointer Split (15+)'` with `'Checkpointer View (15+)'` and add new PG 17/18 features:

```python
        features = {
            'Modern Version (12+)': pg_version.is_modern,
            'Checkpointer View (15+)': pg_version.has_checkpointer_view,
            'pg_stat_io View (16+)': pg_version.has_pg_stat_io,
            'Enhanced WAL Receiver (16+)': pg_version.has_enhanced_wal_receiver,
            'Replication Slot Stats (14+)': pg_version.has_replication_slot_stats,
            'Parallel Leader Tracking (14+)': pg_version.has_parallel_leader_tracking,
            'Wait Events View (17+)': pg_version.has_pg_wait_events,
            'WAL Summarizer (17+)': pg_version.has_wal_summarizer,
            'Replication Slot Invalidation (17+)': pg_version.has_replication_slot_invalidation,
            'VACUUM Time Columns (18+)': pg_version.has_vacuum_time_columns,
            'Async I/O View (18+)': pg_version.has_pg_aios,
            'Per-Backend I/O Stats (18+)': pg_version.has_per_backend_io,
            'Parallel Worker Stats (18+)': pg_version.has_parallel_worker_stats,
        }
```

Also update the compatibility summary to mention PG 17/18:

```python
        if pg_version.is_modern:
            if pg_version >= 18:
                result.append("All MCP tools fully supported with PG18 async I/O, VACUUM timing, and per-backend stats!")
            elif pg_version >= 17:
                result.append("All MCP tools fully supported with PG17 wait events, WAL summarizer, and enhanced stats!")
            elif pg_version >= 16:
                result.append("All MCP tools fully supported with latest features!")
            elif pg_version >= 14:
                result.append("Most advanced features available, consider upgrading to PG16+ for pg_stat_io")
            else:
                result.append("Core features supported, upgrade to PG14+ recommended for enhanced monitoring")
        else:
            result.append("Limited: PostgreSQL 12+ required for full MCP tool support")
```

**Step 3: Commit**

```bash
git add src/mcp_postgresql_ops/mcp_main.py
git commit -m "fix: correct bgwriter stats for PG 15-18 and update server info features"
```

---

## Task 3: Enhance Replication Slots Query with PG 17 Columns

**Files:**
- Modify: `src/mcp_postgresql_ops/version_compat.py` (the `get_replication_slots_query` method)

**Context:** PG 17 adds `invalidation_reason` and `inactive_since` to `pg_replication_slots`.

**Step 1: Update `get_replication_slots_query` in VersionAwareQueries**

Add a third branch for PG 17+ that includes the new columns:

```python
    @staticmethod
    async def get_replication_slots_query(database: str = None) -> str:
        version = await get_postgresql_version(database)

        base_columns = """
            slot_name,
            plugin,
            slot_type,
            datoid,
            temporary,
            active,
            active_pid,
            restart_lsn,
            confirmed_flush_lsn"""

        if version.has_replication_slot_invalidation:
            # PG 17+: includes invalidation_reason, inactive_since, wal_status, safe_wal_size
            return f"""
            SELECT
                {base_columns},
                wal_status,
                safe_wal_size / 1024 / 1024 as safe_wal_size_mb,
                invalidation_reason,
                inactive_since
            FROM pg_replication_slots
            ORDER BY slot_name
            """
        elif version.has_replication_slot_wal_status:
            # PG 13-16: wal_status and safe_wal_size
            return f"""
            SELECT
                {base_columns},
                wal_status,
                safe_wal_size / 1024 / 1024 as safe_wal_size_mb,
                NULL::text as invalidation_reason,
                NULL::timestamptz as inactive_since
            FROM pg_replication_slots
            ORDER BY slot_name
            """
        else:
            # PG 12
            return f"""
            SELECT
                {base_columns},
                NULL::text as wal_status,
                NULL::numeric as safe_wal_size_mb,
                NULL::text as invalidation_reason,
                NULL::timestamptz as inactive_since
            FROM pg_replication_slots
            ORDER BY slot_name
            """
```

**Step 2: Commit**

```bash
git add src/mcp_postgresql_ops/version_compat.py
git commit -m "feat: add PG 17 replication slot invalidation_reason and inactive_since"
```

---

## Task 4: Enhance pg_stat_statements Query with PG 17/18 Columns

**Files:**
- Modify: `src/mcp_postgresql_ops/version_compat.py` (the `get_pg_stat_statements_query` function)

**Context:** PG 17 adds `stats_since`, `minmax_stats_since`, `local_blk_read_time`, `local_blk_write_time`, and renames `blk_read_time`→`shared_blk_read_time`, `blk_write_time`→`shared_blk_write_time`. PG 18 adds `parallel_workers_to_launch`, `parallel_workers_launched`, `wal_buffers_full`.

**Step 1: Update `get_pg_stat_statements_query`**

After the block columns (line 538), add version-specific I/O timing and PG 18 columns:

```python
    # Add version-specific I/O timing columns
    if version.has_pg_stat_statements_v17:
        # PG 17+: renamed and new timing columns
        base_columns.extend([
            "shared_blk_read_time", "shared_blk_write_time",
            "local_blk_read_time", "local_blk_write_time",
            "stats_since", "minmax_stats_since"
        ])
    else:
        # PG 13-16: old names (blk_read_time/blk_write_time)
        base_columns.extend([
            "blk_read_time as shared_blk_read_time",
            "blk_write_time as shared_blk_write_time"
        ])

    if version.has_pg_stat_statements_v18:
        # PG 18+: parallel worker and WAL stats
        base_columns.extend([
            "parallel_workers_to_launch", "parallel_workers_launched",
            "wal_buffers_full"
        ])
```

Remove the old `blk_read_time`/`blk_write_time` references that may already exist if any.

**Step 2: Commit**

```bash
git add src/mcp_postgresql_ops/version_compat.py
git commit -m "feat: add PG 17/18 pg_stat_statements columns"
```

---

## Task 5: Enhance I/O Stats Tool with PG 18 Byte Columns

**Files:**
- Modify: `src/mcp_postgresql_ops/mcp_main.py` (the `get_io_stats` tool, around line 2986)

**Context:** PG 18 adds `read_bytes`, `write_bytes`, `extend_bytes` to `pg_stat_io` and removes `op_bytes`. Also adds WAL I/O activity rows.

**Step 1: Update the PG 16+ branch of get_io_stats**

Add conditional byte columns for PG 18:

```python
        if pg_version.has_pg_stat_io:
            byte_columns = ""
            if pg_version.has_pg_stat_io_bytes:
                byte_columns = """
                    pg_size_pretty(read_bytes) as read_bytes_pretty,
                    pg_size_pretty(write_bytes) as write_bytes_pretty,
                    pg_size_pretty(extend_bytes) as extend_bytes_pretty,"""

            query = f"""
            SELECT
                backend_type,
                object,
                context,
                reads,
                ROUND(read_time::numeric, 2) as read_time_ms,{byte_columns}
                writes,
                ROUND(write_time::numeric, 2) as write_time_ms,
                extends,
                ROUND(extend_time::numeric, 2) as extend_time_ms,
                hits,
                evictions,
                reuses,
                fsyncs,
                ROUND(fsync_time::numeric, 2) as fsync_time_ms,
                CASE
                    WHEN (reads + hits) > 0 THEN
                        ROUND((hits::numeric / (reads + hits)) * 100, 2)
                    ELSE 0
                END as hit_ratio_percent
            FROM pg_stat_io
            WHERE reads > 0 OR writes > 0 OR hits > 0 OR extends > 0 OR fsyncs > 0
            ORDER BY (reads + writes + extends) DESC
            LIMIT {limit}
            """
```

**Step 2: Commit**

```bash
git add src/mcp_postgresql_ops/mcp_main.py
git commit -m "feat: add PG 18 I/O byte columns to io_stats tool"
```

---

## Task 6: Enhance VACUUM/ANALYZE Stats with PG 18 Time Columns

**Files:**
- Modify: `src/mcp_postgresql_ops/version_compat.py` (the `get_all_tables_stats_query` method)
- Modify: `src/mcp_postgresql_ops/mcp_main.py` (the `get_vacuum_analyze_stats` tool)

**Context:** PG 18 adds `total_vacuum_time`, `total_autovacuum_time`, `total_analyze_time`, `total_autoanalyze_time` to `pg_stat_all_tables`.

**Step 1: Update `get_all_tables_stats_query` in version_compat.py**

Add PG 18 time columns after the `n_ins_since_vacuum` line in the PG 13+ branch:

```python
        # Add PG 18 VACUUM/ANALYZE time columns
        vacuum_time_cols = ""
        if version.has_vacuum_time_columns:
            vacuum_time_cols = """
                total_vacuum_time,
                total_autovacuum_time,
                total_analyze_time,
                total_autoanalyze_time,"""
```

Include this in the SELECT of both the PG 13+ and PG 12 branches (using NULLs for PG 12-17).

**Step 2: Update `get_vacuum_analyze_stats` in mcp_main.py**

Add version-aware columns to the vacuum stats query:

```python
        version = await get_postgresql_version(database_name)

        vacuum_time_cols = ""
        if version.has_vacuum_time_columns:
            vacuum_time_cols = """
            ROUND(total_vacuum_time::numeric, 2) as total_vacuum_time_ms,
            ROUND(total_autovacuum_time::numeric, 2) as total_autovacuum_time_ms,
            ROUND(total_analyze_time::numeric, 2) as total_analyze_time_ms,
            ROUND(total_autoanalyze_time::numeric, 2) as total_autoanalyze_time_ms,"""

        query = f"""
        SELECT
            schemaname as schema_name,
            relname as table_name,
            last_vacuum,
            last_autovacuum,
            last_analyze,
            last_autoanalyze,
            vacuum_count,
            autovacuum_count,
            analyze_count,
            autoanalyze_count,{vacuum_time_cols}
            n_tup_ins as inserts,
            n_tup_upd as updates,
            n_tup_del as deletes
        FROM pg_stat_user_tables
        ORDER BY schemaname, relname
        """
```

**Step 3: Commit**

```bash
git add src/mcp_postgresql_ops/version_compat.py src/mcp_postgresql_ops/mcp_main.py
git commit -m "feat: add PG 18 VACUUM/ANALYZE time columns"
```

---

## Task 7: Enhance Database Stats with PG 18 Parallel Worker Columns

**Files:**
- Modify: `src/mcp_postgresql_ops/mcp_main.py` (the `get_database_stats` tool, around line 2807)

**Context:** PG 18 adds `parallel_workers_to_launch` and `parallel_workers_launched` to `pg_stat_database`.

**Step 1: Add version-aware parallel worker columns**

```python
        version = await get_postgresql_version()

        parallel_cols = ""
        if version.has_parallel_worker_stats:
            parallel_cols = """
            parallel_workers_to_launch,
            parallel_workers_launched,"""

        query = f"""
        SELECT
            datname as database_name,
            numbackends as active_connections,
            xact_commit as transactions_committed,
            xact_rollback as transactions_rolled_back,
            ...existing columns...{parallel_cols}
            stats_reset
        FROM pg_stat_database
        WHERE datname IS NOT NULL
        ORDER BY datname
        """
```

**Step 2: Commit**

```bash
git add src/mcp_postgresql_ops/mcp_main.py
git commit -m "feat: add PG 18 parallel worker stats to database_stats"
```

---

## Task 8: New Tool — get_wait_events (PG 17+)

**Files:**
- Modify: `src/mcp_postgresql_ops/mcp_main.py` (add new tool)

**Context:** PG 17 introduced `pg_wait_events` view which provides descriptions for wait events. This is useful for understanding what sessions are waiting on.

**Step 1: Add the new tool**

Add after the `get_active_connections` tool:

```python
@mcp.tool()
async def get_wait_events(database_name: str = None, wait_event_type: str = None) -> str:
    """
    [Tool Purpose]: List available wait event types and their descriptions (PostgreSQL 17+)

    [Exact Functionality]:
    - Show all wait event types with human-readable descriptions
    - Correlate with current active sessions waiting on events
    - Filter by specific wait event type
    - Falls back to basic pg_stat_activity wait info on PG < 17

    [Required Use Cases]:
    - When user requests "wait events", "wait event descriptions", "what are sessions waiting on"
    - When diagnosing session waits and understanding wait event meanings
    - When analyzing wait patterns across the database

    [Strictly Prohibited Use Cases]:
    - Requests for session termination or wait resolution
    - Requests for configuration changes

    Args:
        database_name: Database name to analyze (uses default if omitted)
        wait_event_type: Filter by wait event type (e.g., "Lock", "IO", "LWLock")

    Returns:
        Wait event catalog with descriptions, or active session wait summary on older versions
    """
    try:
        version = await get_postgresql_version(database_name)

        if version.has_pg_wait_events:
            where_clause = ""
            params = []
            if wait_event_type:
                where_clause = "WHERE type ILIKE $1"
                params = [f"%{wait_event_type}%"]

            query = f"""
            SELECT
                type as wait_event_type,
                name as wait_event_name,
                description
            FROM pg_wait_events
            {where_clause}
            ORDER BY type, name
            """

            events = await execute_query(query, params, database=database_name)

            # Also get current wait event summary
            summary_query = """
            SELECT
                wait_event_type,
                wait_event,
                COUNT(*) as session_count
            FROM pg_stat_activity
            WHERE wait_event IS NOT NULL AND pid <> pg_backend_pid()
            GROUP BY wait_event_type, wait_event
            ORDER BY COUNT(*) DESC
            """
            summary = await execute_query(summary_query, database=database_name)

            result = []
            title = "Wait Event Catalog (pg_wait_events)"
            if wait_event_type:
                title += f" [Filter: {wait_event_type}]"
            result.append(format_table_data(events, title))

            if summary:
                result.append("\n" + format_table_data(summary, "Current Session Wait Summary"))
            else:
                result.append("\nNo sessions currently waiting on events")

            return "\n".join(result)
        else:
            # Fallback for PG < 17: just show current wait events from pg_stat_activity
            query = """
            SELECT
                wait_event_type,
                wait_event,
                COUNT(*) as session_count,
                string_agg(pid::text, ', ' ORDER BY pid) as pids
            FROM pg_stat_activity
            WHERE wait_event IS NOT NULL AND pid <> pg_backend_pid()
            GROUP BY wait_event_type, wait_event
            ORDER BY COUNT(*) DESC
            """
            events = await execute_query(query, database=database_name)

            result = format_table_data(events, f"Current Wait Events (PG {version} - no pg_wait_events catalog)")
            result += f"\n\nNote: Upgrade to PostgreSQL 17+ for detailed wait event descriptions"
            return result

    except Exception as e:
        logger.error(f"Failed to get wait events: {e}")
        return f"Error retrieving wait events: {str(e)}"
```

**Step 2: Commit**

```bash
git add src/mcp_postgresql_ops/mcp_main.py
git commit -m "feat: add get_wait_events tool for PG 17+ pg_wait_events view"
```

---

## Task 9: New Tool — get_wal_summarizer_status (PG 17+)

**Files:**
- Modify: `src/mcp_postgresql_ops/mcp_main.py` (add new tool)

**Context:** PG 17 added WAL summarization for incremental backups with new functions: `pg_get_wal_summarizer_state()`, `pg_available_wal_summaries()`.

**Step 1: Add the new tool**

Add after the `get_wal_status` tool:

```python
@mcp.tool()
async def get_wal_summarizer_status(database_name: str = None) -> str:
    """
    [Tool Purpose]: Monitor WAL summarizer status for incremental backup support (PostgreSQL 17+)

    [Exact Functionality]:
    - Show WAL summarizer process state and progress
    - Display available WAL summaries for incremental backups
    - Report summarize_wal configuration status
    - Falls back to configuration check on PG < 17

    [Required Use Cases]:
    - When user requests "WAL summarizer", "incremental backup status", "WAL summary"
    - When checking incremental backup readiness
    - When monitoring WAL summarization progress

    [Strictly Prohibited Use Cases]:
    - Requests for WAL summarizer configuration changes
    - Requests for backup execution

    Args:
        database_name: Database name (uses default if omitted)

    Returns:
        WAL summarizer state and available summaries, or version notice on older PG
    """
    try:
        version = await get_postgresql_version(database_name)

        if not version.has_wal_summarizer:
            return f"WAL summarizer is not available on PostgreSQL {version}. Upgrade to PostgreSQL 17+ for incremental backup support via WAL summarization."

        result = []

        # Check if summarize_wal is enabled
        config_query = """
        SELECT name, setting, short_desc
        FROM pg_settings
        WHERE name IN ('summarize_wal', 'wal_summary_keep_time')
        ORDER BY name
        """
        config = await execute_query(config_query, database=database_name)
        result.append(format_table_data(config, "WAL Summarizer Configuration"))

        # Get summarizer state
        try:
            state_query = "SELECT * FROM pg_get_wal_summarizer_state()"
            state = await execute_query(state_query, database=database_name)
            result.append("\n" + format_table_data(state, "WAL Summarizer State"))
        except Exception:
            result.append("\nWAL summarizer state unavailable (summarize_wal may be disabled)")

        # Get available summaries
        try:
            summaries_query = """
            SELECT *
            FROM pg_available_wal_summaries()
            ORDER BY start_lsn DESC
            LIMIT 20
            """
            summaries = await execute_query(summaries_query, database=database_name)
            if summaries:
                result.append("\n" + format_table_data(summaries, "Available WAL Summaries (Latest 20)"))
            else:
                result.append("\nNo WAL summaries available yet")
        except Exception:
            result.append("\nWAL summaries unavailable")

        return "\n".join(result)

    except Exception as e:
        logger.error(f"Failed to get WAL summarizer status: {e}")
        return f"Error retrieving WAL summarizer status: {str(e)}"
```

**Step 2: Commit**

```bash
git add src/mcp_postgresql_ops/mcp_main.py
git commit -m "feat: add get_wal_summarizer_status tool for PG 17+ incremental backups"
```

---

## Task 10: New Tool — get_async_io_status (PG 18+)

**Files:**
- Modify: `src/mcp_postgresql_ops/mcp_main.py` (add new tool)

**Context:** PG 18 introduces `pg_aios` view for monitoring the async I/O subsystem and `io_method` GUC parameter.

**Step 1: Add the new tool**

Add after the `get_io_stats` tool:

```python
@mcp.tool()
async def get_async_io_status(database_name: str = None) -> str:
    """
    [Tool Purpose]: Monitor asynchronous I/O subsystem status (PostgreSQL 18+)

    [Exact Functionality]:
    - Show active async I/O operations from pg_aios view
    - Display I/O method configuration and concurrency settings
    - Report async I/O file handle usage
    - Falls back to I/O configuration info on PG < 18

    [Required Use Cases]:
    - When user requests "async I/O status", "AIO monitoring", "I/O subsystem"
    - When investigating I/O performance and concurrency
    - When checking async I/O configuration

    [Strictly Prohibited Use Cases]:
    - Requests for I/O configuration changes
    - Requests for storage modifications

    Args:
        database_name: Database name (uses default if omitted)

    Returns:
        Async I/O subsystem status and configuration, or version notice on older PG
    """
    try:
        version = await get_postgresql_version(database_name)

        if not version.has_pg_aios:
            return f"Async I/O subsystem view (pg_aios) is not available on PostgreSQL {version}. Upgrade to PostgreSQL 18+ for async I/O monitoring."

        result = []

        # Get I/O configuration
        config_query = """
        SELECT name, setting, unit, short_desc
        FROM pg_settings
        WHERE name IN ('io_method', 'io_combine_limit', 'io_max_combine_limit',
                       'effective_io_concurrency', 'maintenance_io_concurrency')
        ORDER BY name
        """
        config = await execute_query(config_query, database=database_name)
        result.append(format_table_data(config, "Async I/O Configuration"))

        # Get active async I/O operations
        try:
            aios_query = "SELECT * FROM pg_aios LIMIT 100"
            aios = await execute_query(aios_query, database=database_name)
            if aios:
                result.append("\n" + format_table_data(aios, "Active Async I/O Operations (pg_aios)"))
            else:
                result.append("\nNo active async I/O operations at this moment")
        except Exception:
            result.append("\npg_aios view unavailable")

        return "\n".join(result)

    except Exception as e:
        logger.error(f"Failed to get async I/O status: {e}")
        return f"Error retrieving async I/O status: {str(e)}"
```

**Step 2: Commit**

```bash
git add src/mcp_postgresql_ops/mcp_main.py
git commit -m "feat: add get_async_io_status tool for PG 18+ async I/O monitoring"
```

---

## Task 11: New Tool — get_per_backend_io_stats (PG 18+)

**Files:**
- Modify: `src/mcp_postgresql_ops/mcp_main.py` (add new tool)

**Context:** PG 18 adds `pg_stat_get_backend_io()` for per-backend I/O statistics and `pg_stat_get_backend_wal()` for per-backend WAL stats.

**Step 1: Add the new tool**

```python
@mcp.tool()
async def get_per_backend_io_stats(database_name: str = None, limit: int = 20) -> str:
    """
    [Tool Purpose]: Analyze per-backend I/O and WAL statistics (PostgreSQL 18+)

    [Exact Functionality]:
    - Show I/O statistics broken down by individual backend process
    - Display per-backend WAL generation statistics
    - Identify backends with highest I/O activity
    - Falls back to aggregate stats on PG < 18

    [Required Use Cases]:
    - When user requests "per-backend I/O", "backend I/O stats", "which backend is doing most I/O"
    - When diagnosing I/O hotspots at the process level
    - When analyzing per-connection I/O patterns

    [Strictly Prohibited Use Cases]:
    - Requests for backend termination
    - Requests for I/O configuration changes

    Args:
        database_name: Database name (uses default if omitted)
        limit: Maximum results (1-100, default 20)

    Returns:
        Per-backend I/O and WAL statistics, or version notice on older PG
    """
    try:
        version = await get_postgresql_version(database_name)
        limit = max(1, min(limit, 100))

        if not version.has_per_backend_io:
            return f"Per-backend I/O statistics are not available on PostgreSQL {version}. Upgrade to PostgreSQL 18+ for pg_stat_get_backend_io()."

        result = []

        # Per-backend I/O stats joined with activity info
        query = f"""
        SELECT
            a.pid,
            a.usename as username,
            a.datname as database_name,
            a.application_name,
            a.state,
            bio.*
        FROM pg_stat_activity a
        CROSS JOIN LATERAL pg_stat_get_backend_io(a.pid) bio
        WHERE a.pid <> pg_backend_pid()
        ORDER BY bio.reads + bio.writes DESC
        LIMIT {limit}
        """

        try:
            stats = await execute_query(query, database=database_name)
            if stats:
                result.append(format_table_data(stats, f"Per-Backend I/O Statistics (Top {limit})"))
            else:
                result.append("No per-backend I/O statistics available")
        except Exception as e:
            result.append(f"Per-backend I/O query failed: {e}")

        # Per-backend WAL stats
        wal_query = f"""
        SELECT
            a.pid,
            a.usename as username,
            a.datname as database_name,
            bwal.*
        FROM pg_stat_activity a
        CROSS JOIN LATERAL pg_stat_get_backend_wal(a.pid) bwal
        WHERE a.pid <> pg_backend_pid()
        ORDER BY bwal.wal_bytes DESC NULLS LAST
        LIMIT {limit}
        """

        try:
            wal_stats = await execute_query(wal_query, database=database_name)
            if wal_stats:
                result.append("\n" + format_table_data(wal_stats, f"Per-Backend WAL Statistics (Top {limit})"))
        except Exception:
            pass

        return "\n".join(result) if result else "No per-backend statistics available"

    except Exception as e:
        logger.error(f"Failed to get per-backend I/O stats: {e}")
        return f"Error retrieving per-backend I/O statistics: {str(e)}"
```

**Step 2: Commit**

```bash
git add src/mcp_postgresql_ops/mcp_main.py
git commit -m "feat: add get_per_backend_io_stats tool for PG 18+ per-backend I/O"
```

---

## Task 12: Update VersionAwareQueries and Documentation

**Files:**
- Modify: `src/mcp_postgresql_ops/version_compat.py` (update VersionAwareQueries methods)
- Modify: `src/mcp_postgresql_ops/mcp_main.py` (update get_all_tables_stats tool)

**Step 1: Update `get_all_tables_stats_query` in version_compat.py for PG 18**

Add vacuum time columns to the PG 13+ branch:

```python
        vacuum_time_cols = ""
        vacuum_time_null_cols = ""
        if version.has_vacuum_time_columns:
            vacuum_time_cols = """
                ROUND(total_vacuum_time::numeric, 2) as total_vacuum_time_ms,
                ROUND(total_autovacuum_time::numeric, 2) as total_autovacuum_time_ms,
                ROUND(total_analyze_time::numeric, 2) as total_analyze_time_ms,
                ROUND(total_autoanalyze_time::numeric, 2) as total_autoanalyze_time_ms,"""
            vacuum_time_null_cols = vacuum_time_cols  # Same for PG 12 branch but with NULLs
```

**Step 2: Update `get_bgwriter_checkpointer_stats` in version_compat.py**

Fix this static method to handle PG 15+/17+/18+ properly (matching the fix from Task 2 but in the VersionAwareQueries class):

```python
    @staticmethod
    async def get_bgwriter_checkpointer_stats(database: str = None) -> str:
        version = await get_postgresql_version(database)

        if version.has_checkpointer_view:
            return """
            SELECT 'checkpointer' as component,
                   num_timed, num_requested, restartpoints_timed, restartpoints_req, restartpoints_done,
                   write_time, sync_time, buffers_written, stats_reset
            FROM pg_stat_checkpointer
            UNION ALL
            SELECT 'bgwriter' as component,
                   NULL::bigint, NULL::bigint, NULL::bigint, NULL::bigint, NULL::bigint,
                   NULL::double precision, NULL::double precision,
                   buffers_clean as buffers_written, stats_reset
            FROM pg_stat_bgwriter
            """
        else:
            return """
            SELECT 'bgwriter_legacy' as component,
                   buffers_clean, maxwritten_clean, buffers_alloc, stats_reset,
                   NULL::bigint as num_timed, NULL::bigint as num_requested
            FROM pg_stat_bgwriter
            """
```

**Step 3: Update the `get_io_statistics` method for PG 18**

```python
    @staticmethod
    async def get_io_statistics(database: str = None) -> str:
        version = await get_postgresql_version(database)

        if version.has_pg_stat_io:
            byte_cols = ""
            if version.has_pg_stat_io_bytes:
                byte_cols = "read_bytes, write_bytes, extend_bytes,"

            return f"""
            SELECT backend_type, object, context,
                   reads, read_time, writes, write_time,
                   extends, extend_time, hits, evictions,
                   reuses, fsyncs, fsync_time,
                   {byte_cols}
            FROM pg_stat_io
            WHERE reads > 0 OR writes > 0 OR hits > 0
            """
        else:
            return """
            SELECT 'client backend' as backend_type,
                   'relation' as object,
                   'normal' as context,
                   heap_blks_read as reads,
                   0::double precision as read_time,
                   0::bigint as writes,
                   0::double precision as write_time,
                   0::bigint as extends,
                   0::double precision as extend_time,
                   heap_blks_hit as hits,
                   0::bigint as evictions,
                   0::bigint as reuses,
                   0::bigint as fsyncs,
                   0::double precision as fsync_time
            FROM pg_statio_all_tables
            WHERE heap_blks_read > 0 OR heap_blks_hit > 0
            """
```

**Step 4: Commit**

```bash
git add src/mcp_postgresql_ops/version_compat.py src/mcp_postgresql_ops/mcp_main.py
git commit -m "feat: update VersionAwareQueries for PG 17/18 compatibility"
```

---

## Task 13: Update README and Supported Version Range

**Files:**
- Modify: `README.md` (update supported versions, tool list, feature matrix)

**Step 1: Update supported version references**

Change "PostgreSQL 12-17" references to "PostgreSQL 12-18" throughout the README.

**Step 2: Add new tools to the tool list**

Add entries for the 4 new tools:
- `get_wait_events` — PG 17+ wait event catalog with descriptions
- `get_wal_summarizer_status` — PG 17+ WAL summarizer for incremental backups
- `get_async_io_status` — PG 18+ async I/O subsystem monitoring
- `get_per_backend_io_stats` — PG 18+ per-backend I/O and WAL stats

**Step 3: Update version compatibility matrix**

Add new rows to the version feature matrix for PG 17 and PG 18 features.

**Step 4: Commit**

```bash
git add README.md
git commit -m "docs: update README for PG 17/18 support and new tools"
```

---

## Summary

| Task | Type | PG Version | Files Modified |
|------|------|-----------|----------------|
| 1 | C - Fix version compat | 17/18 | version_compat.py |
| 2 | C - Fix bgwriter tool | 15-18 | mcp_main.py |
| 3 | A - Enhance replication slots | 17 | version_compat.py |
| 4 | A - Enhance pg_stat_statements | 17/18 | version_compat.py |
| 5 | A - Enhance I/O stats | 18 | mcp_main.py |
| 6 | A - Enhance VACUUM stats | 18 | version_compat.py, mcp_main.py |
| 7 | A - Enhance database stats | 18 | mcp_main.py |
| 8 | B - New wait_events tool | 17 | mcp_main.py |
| 9 | B - New wal_summarizer tool | 17 | mcp_main.py |
| 10 | B - New async_io tool | 18 | mcp_main.py |
| 11 | B - New per_backend_io tool | 18 | mcp_main.py |
| 12 | A - Update VersionAwareQueries | 17/18 | version_compat.py, mcp_main.py |
| 13 | Docs | All | README.md |

**Total: 4 new tools, 6 enhanced existing tools, 2 bug fixes, 1 doc update**
