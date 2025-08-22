"""
PostgreSQL Version Compatibility Utilities

Provides version detection and compatibility handling for MCP PostgreSQL tools.
"""

import re
import logging
from typing import Tuple, Optional
from .functions import execute_single_query

logger = logging.getLogger(__name__)

class PostgreSQLVersion:
    """PostgreSQL version information and compatibility utilities."""
    
    def __init__(self, major: int, minor: int = 0, patch: int = 0):
        self.major = major
        self.minor = minor  
        self.patch = patch
        
    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"
        
    def __ge__(self, other):
        if isinstance(other, (int, float)):
            return self.major >= other
        if isinstance(other, PostgreSQLVersion):
            return (self.major, self.minor, self.patch) >= (other.major, other.minor, other.patch)
        return False
    
    def __lt__(self, other):
        if isinstance(other, (int, float)):
            return self.major < other
        if isinstance(other, PostgreSQLVersion):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
        return False
        
    @property
    def is_modern(self) -> bool:
        """Check if this is a modern PostgreSQL version (12+)."""
        return self.major >= 12
        
    @property
    def has_checkpointer_split(self) -> bool:
        """Check if checkpointer stats are in separate view (only PG15)."""
        return self.major == 15
        
    @property
    def has_pg_stat_io(self) -> bool:
        """Check if pg_stat_io view is available (16+)."""
        return self.major >= 16
        
    @property
    def has_enhanced_wal_receiver(self) -> bool:
        """Check if pg_stat_wal_receiver has written_lsn/flushed_lsn (16+)."""
        return self.major >= 16
        
    @property
    def has_replication_slot_stats(self) -> bool:
        """Check if pg_stat_replication_slots is available (14+)."""
        return self.major >= 14
        
    @property
    def has_parallel_leader_tracking(self) -> bool:
        """Check if pg_stat_activity has leader_pid column (14+)."""
        return self.major >= 14
        
    @property
    def has_replication_slot_wal_status(self) -> bool:
        """Check if pg_replication_slots has wal_status and safe_wal_size columns (13+)."""
        return self.major >= 13
        
    @property
    def has_table_stats_ins_since_vacuum(self) -> bool:
        """Check if pg_stat_*_tables has n_ins_since_vacuum column (13+)."""
        return self.major >= 13
        
    @property
    def has_pg_stat_statements_exec_time(self) -> bool:
        """Check if pg_stat_statements uses total_exec_time and mean_exec_time columns (13+)."""
        return self.major >= 13

# Global version cache
_cached_version: Optional[PostgreSQLVersion] = None

async def get_postgresql_version(database: str = None, force_refresh: bool = False) -> PostgreSQLVersion:
    """
    Get PostgreSQL server version with caching.
    
    Args:
        database: Database to connect to
        force_refresh: Force refresh cached version
        
    Returns:
        PostgreSQLVersion object
    """
    global _cached_version
    
    if _cached_version is not None and not force_refresh:
        return _cached_version
        
    try:
        result = await execute_single_query("SELECT version()", database=database)
        version_string = result.get('version', '')
        
        # Parse version string like "PostgreSQL 16.1 on x86_64-pc-linux-gnu..."
        version_match = re.search(r'PostgreSQL\s+(\d+)\.?(\d*)\.?(\d*)', version_string)
        
        if version_match:
            major = int(version_match.group(1))
            minor = int(version_match.group(2) or 0)
            patch = int(version_match.group(3) or 0)
            
            _cached_version = PostgreSQLVersion(major, minor, patch)
            logger.info(f"Detected PostgreSQL version: {_cached_version}")
            return _cached_version
        else:
            logger.warning(f"Could not parse version string: {version_string}")
            # Default to PostgreSQL 17 if parsing fails
            _cached_version = PostgreSQLVersion(17, 0, 0)
            return _cached_version
            
    except Exception as e:
        logger.error(f"Failed to get PostgreSQL version: {e}")
        # Default to PostgreSQL 17 if version detection fails
        _cached_version = PostgreSQLVersion(17, 0, 0)
        return _cached_version

async def check_feature_availability(feature: str, database: str = None) -> bool:
    """
    Check if a specific PostgreSQL feature is available.
    
    Args:
        feature: Feature name to check
        database: Database to connect to
        
    Returns:
        True if feature is available
    """
    version = await get_postgresql_version(database)
    
    feature_requirements = {
        'pg_stat_io': version.has_pg_stat_io,
        'checkpointer_split': version.has_checkpointer_split,
        'enhanced_wal_receiver': version.has_enhanced_wal_receiver,
        'replication_slot_stats': version.has_replication_slot_stats,
        'parallel_leader_tracking': version.has_parallel_leader_tracking,
    }
    
    return feature_requirements.get(feature, False)

async def get_compatible_column_list(table_name: str, 
                                   all_columns: list, 
                                   version_specific_columns: dict,
                                   database: str = None) -> str:
    """
    Generate version-compatible column list for SELECT queries.
    
    Args:
        table_name: PostgreSQL table/view name
        all_columns: List of all possible columns
        version_specific_columns: Dict mapping version requirements to columns
        database: Database to connect to
        
    Returns:
        Comma-separated column list for SQL SELECT
    """
    version = await get_postgresql_version(database)
    
    available_columns = []
    
    for col in all_columns:
        # Check if column has version requirements
        required_version = version_specific_columns.get(col)
        if required_version is None:
            # No version requirement - always available
            available_columns.append(col)
        elif version >= required_version:
            # Version requirement met
            available_columns.append(col)
        else:
            # Version requirement not met - provide NULL placeholder
            available_columns.append(f"NULL::text AS {col}")
            
    return ", ".join(available_columns)

def get_version_appropriate_query(base_query: str, 
                                version_variants: dict, 
                                version: PostgreSQLVersion) -> str:
    """
    Select version-appropriate query variant.
    
    Args:
        base_query: Default/fallback query
        version_variants: Dict mapping version requirements to query variants
        version: PostgreSQL version
        
    Returns:
        Most appropriate query for the version
    """
    # Sort version variants by version (highest first)
    sorted_variants = sorted(version_variants.items(), 
                           key=lambda x: (x[0].major, x[0].minor), 
                           reverse=True)
    
    for required_version, query in sorted_variants:
        if version >= required_version:
            return query
            
    return base_query

# Version-specific query builders
class VersionAwareQueries:
    """Collection of version-aware query builders."""
    
    @staticmethod
    async def get_bgwriter_checkpointer_stats(database: str = None) -> str:
        """Get background writer/checkpointer stats with version compatibility."""
        version = await get_postgresql_version(database)
        
        if version.has_checkpointer_split:
            # PostgreSQL 15+: Use separate checkpointer view
            return """
            SELECT 'checkpointer' as component,
                   num_timed, num_requested, restartpoints_timed, restartpoints_req, restartpoints_done,
                   write_time, sync_time, buffers_written, stats_reset
            FROM pg_stat_checkpointer
            UNION ALL
            SELECT 'bgwriter' as component,
                   NULL::bigint as num_timed, NULL::bigint as num_requested, 
                   NULL::bigint as restartpoints_timed, NULL::bigint as restartpoints_req, 
                   NULL::bigint as restartpoints_done, NULL::double precision as write_time,
                   NULL::double precision as sync_time,
                   buffers_clean as buffers_written, stats_reset
            FROM pg_stat_bgwriter
            """
        else:
            # PostgreSQL 10-14: All stats in bgwriter view
            return """
            SELECT 'bgwriter_legacy' as component,
                   buffers_clean, maxwritten_clean, buffers_alloc, stats_reset,
                   NULL::bigint as num_timed, NULL::bigint as num_requested
            FROM pg_stat_bgwriter
            """
    
    @staticmethod
    async def get_io_statistics(database: str = None) -> str:
        """Get I/O statistics with version compatibility."""
        version = await get_postgresql_version(database)
        
        if version.has_pg_stat_io:
            # PostgreSQL 16+: Use comprehensive pg_stat_io
            return """
            SELECT backend_type, object, context, 
                   reads, read_time, writes, write_time,
                   extends, extend_time, hits, evictions,
                   reuses, fsyncs, fsync_time
            FROM pg_stat_io
            WHERE reads > 0 OR writes > 0 OR hits > 0
            """
        else:
            # PostgreSQL 10-15: Fall back to pg_statio_* views
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
    
    @staticmethod 
    async def get_activity_with_leader_info(database: str = None) -> str:
        """Get activity info with parallel leader tracking if available."""
        version = await get_postgresql_version(database)
        
        base_columns = [
            "pid", "datname", "usename", "application_name", 
            "client_addr", "state", "query_start", "query"
        ]
        
        version_columns = {
            "leader_pid": PostgreSQLVersion(14),
            "query_id": PostgreSQLVersion(13)
        }
        
        columns = await get_compatible_column_list(
            "pg_stat_activity", 
            base_columns + list(version_columns.keys()),
            version_columns,
            database
        )
        
        return f"SELECT {columns} FROM pg_stat_activity WHERE state = 'active'"
    
    @staticmethod
    async def get_replication_slots_query(database: str = None) -> str:
        """Get replication slots info with version compatibility."""
        version = await get_postgresql_version(database)
        
        base_columns = [
            "slot_name", "plugin", "slot_type", "datoid", "temporary",
            "active", "active_pid", "restart_lsn", "confirmed_flush_lsn"
        ]
        
        # wal_status and safe_wal_size are available from PostgreSQL 13+
        if version.has_replication_slot_wal_status:
            return """
            SELECT 
                slot_name,
                plugin,
                slot_type,
                datoid,
                temporary,
                active,
                active_pid,
                restart_lsn,
                confirmed_flush_lsn,
                wal_status,
                safe_wal_size / 1024 / 1024 as safe_wal_size_mb
            FROM pg_replication_slots
            ORDER BY slot_name
            """
        else:
            # PostgreSQL 12 and older - without wal_status and safe_wal_size
            return """
            SELECT 
                slot_name,
                plugin,
                slot_type,
                datoid,
                temporary,
                active,
                active_pid,
                restart_lsn,
                confirmed_flush_lsn,
                NULL::text as wal_status,
                NULL::numeric as safe_wal_size_mb
            FROM pg_replication_slots
            ORDER BY slot_name
            """
    
    @staticmethod
    async def get_wal_receiver_query(database: str = None) -> str:
        """Get WAL receiver status with version compatibility."""
        version = await get_postgresql_version(database)
        
        if version.has_enhanced_wal_receiver:
            # PostgreSQL 16+: has written_lsn/flushed_lsn columns
            return """
            SELECT 
                pid,
                status,
                receive_start_lsn,
                receive_start_tli,
                written_lsn,
                flushed_lsn,
                received_tli,
                last_msg_send_time,
                last_msg_receipt_time,
                latest_end_lsn,
                latest_end_time,
                slot_name,
                sender_host,
                sender_port,
                conninfo
            FROM pg_stat_wal_receiver
            """
        else:
            # PostgreSQL 10-15: no written_lsn/flushed_lsn columns
            return """
            SELECT 
                pid,
                status,
                receive_start_lsn,
                receive_start_tli,
                NULL::text as written_lsn,
                NULL::text as flushed_lsn,
                received_tli,
                last_msg_send_time,
                last_msg_receipt_time,
                latest_end_lsn,
                latest_end_time,
                slot_name,
                sender_host,
                sender_port,
                conninfo
            FROM pg_stat_wal_receiver
            """
    
    @staticmethod
    async def get_all_tables_stats_query(include_system: bool = False, database: str = None) -> str:
        """Get all tables statistics query with version compatibility."""
        version = await get_postgresql_version(database)
        
        view_name = "pg_stat_all_tables" if include_system else "pg_stat_user_tables"
        
        # n_ins_since_vacuum is available from PostgreSQL 13+
        if version.has_table_stats_ins_since_vacuum:
            return f"""
            SELECT 
                schemaname as schema_name,
                relname as table_name,
                seq_scan as sequential_scans,
                seq_tup_read as seq_tuples_read,
                idx_scan as index_scans,
                idx_tup_fetch as idx_tuples_fetched,
                n_tup_ins as tuples_inserted,
                n_tup_upd as tuples_updated,
                n_tup_del as tuples_deleted,
                n_tup_hot_upd as hot_updates,
                n_live_tup as estimated_live_tuples,
                n_dead_tup as estimated_dead_tuples,
                CASE 
                    WHEN n_live_tup > 0 THEN
                        ROUND((n_dead_tup::numeric / n_live_tup) * 100, 2)
                    ELSE 0
                END as dead_tuple_ratio_percent,
                n_mod_since_analyze as modified_since_analyze,
                n_ins_since_vacuum as inserted_since_vacuum,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze,
                vacuum_count,
                autovacuum_count,
                analyze_count,
                autoanalyze_count
            FROM {view_name}
            ORDER BY seq_scan + COALESCE(idx_scan, 0) DESC, schemaname, relname
            """
        else:
            # PostgreSQL 12 - without n_ins_since_vacuum
            return f"""
            SELECT 
                schemaname as schema_name,
                relname as table_name,
                seq_scan as sequential_scans,
                seq_tup_read as seq_tuples_read,
                idx_scan as index_scans,
                idx_tup_fetch as idx_tuples_fetched,
                n_tup_ins as tuples_inserted,
                n_tup_upd as tuples_updated,
                n_tup_del as tuples_deleted,
                n_tup_hot_upd as hot_updates,
                n_live_tup as estimated_live_tuples,
                n_dead_tup as estimated_dead_tuples,
                CASE 
                    WHEN n_live_tup > 0 THEN
                        ROUND((n_dead_tup::numeric / n_live_tup) * 100, 2)
                    ELSE 0
                END as dead_tuple_ratio_percent,
                n_mod_since_analyze as modified_since_analyze,
                NULL::bigint as inserted_since_vacuum,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze,
                vacuum_count,
                autovacuum_count,
                analyze_count,
                autoanalyze_count
            FROM {view_name}
            ORDER BY seq_scan + COALESCE(idx_scan, 0) DESC, schemaname, relname
            """


# Utility functions for tool implementations
async def execute_version_aware_query(queries_by_version: dict, 
                                    fallback_query: str,
                                    database: str = None):
    """
    Execute the most appropriate query based on PostgreSQL version.
    
    Args:
        queries_by_version: Dict mapping PostgreSQLVersion to query strings
        fallback_query: Default query if no version matches
        database: Database to connect to
        
    Returns:
        Query results
    """
    from .functions import execute_query
    
    version = await get_postgresql_version(database)
    query = get_version_appropriate_query(fallback_query, queries_by_version, version)
    
    return await execute_query(query, database=database)


# Version-aware pg_stat_statements queries
async def get_pg_stat_statements_query(database: str = None) -> str:
    """
    Get version-compatible pg_stat_statements query.
    
    Args:
        database: Database to connect to for version detection
        
    Returns:
        SQL query string compatible with the database version
    """
    version = await get_postgresql_version(database)
    
    # Common base columns available in all versions
    base_columns = [
        "queryid", "query", "calls", "rows"
    ]
    
    # Add version-specific timing columns
    if version.has_pg_stat_statements_exec_time:
        # PostgreSQL 13+: uses total_exec_time, mean_exec_time
        base_columns.extend([
            "total_exec_time", "mean_exec_time", "min_exec_time", "max_exec_time", "stddev_exec_time"
        ])
    else:
        # PostgreSQL 12: uses total_time, mean_time
        base_columns.extend([
            "total_time as total_exec_time", "mean_time as mean_exec_time", 
            "min_time as min_exec_time", "max_time as max_exec_time", 
            "stddev_time as stddev_exec_time"
        ])
        
    # Add remaining common columns
    base_columns.extend([
        "shared_blks_hit", "shared_blks_read", "shared_blks_dirtied", 
        "shared_blks_written", "local_blks_hit", "local_blks_read", 
        "local_blks_dirtied", "local_blks_written", "temp_blks_read", "temp_blks_written"
    ])
    
    columns_str = ",\n    ".join(base_columns)
    
    return f"""
    SELECT 
        {columns_str}
    FROM pg_stat_statements 
    ORDER BY total_exec_time DESC 
    """


# Version-aware pg_stat_monitor queries
async def get_pg_stat_monitor_query(database: str = None) -> str:
    """
    Get version-compatible pg_stat_monitor query.
    
    Args:
        database: Database to connect to for version detection
        
    Returns:
        SQL query string compatible with the database version
    """
    version = await get_postgresql_version(database)
    
    # Common base columns available in all versions
    base_columns = [
        "query", "calls", "rows"
    ]
    
    # Add version-specific timing columns
    if version.has_pg_stat_statements_exec_time:
        # PostgreSQL 13+: uses total_exec_time, mean_exec_time
        base_columns.extend([
            "total_exec_time", "mean_exec_time"
        ])
    else:
        # PostgreSQL 12: uses total_time, mean_time
        base_columns.extend([
            "total_time as total_exec_time", "mean_time as mean_exec_time"
        ])
        
    # Add remaining common columns
    base_columns.extend([
        "shared_blks_hit", "shared_blks_read", "client_ip", "bucket_start_time"
    ])
    
    columns_str = ",\n    ".join(base_columns)
    
    return f"""
    SELECT 
        {columns_str}
    FROM pg_stat_monitor 
    ORDER BY total_exec_time DESC 
    """
