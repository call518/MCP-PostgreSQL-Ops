"""
MCP PostgreSQL Operations Server

A professional MCP server for PostgreSQL database server operations, monitoring, and management.

Key Features:
1. Query performance monitoring via pg_stat_statements and pg_stat_monitor
2. Database, table, and user listing
3. PostgreSQL configuration and status information
4. Connection information and active session monitoring
5. Index usage statistics and performance metrics
"""

import argparse
import logging
import os
import sys
from typing import Any, Optional
from fastmcp import FastMCP
from .functions import (
    execute_query,
    execute_single_query,
    format_table_data,
    format_bytes,
    format_duration,
    get_server_version,
    check_extension_exists,
    get_pg_stat_statements_data,
    get_pg_stat_monitor_data,
    sanitize_connection_info,
    read_prompt_template,
    parse_prompt_sections,
    POSTGRES_CONFIG
)

# =============================================================================
# Logging configuration
# =============================================================================
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# =============================================================================
# Server initialization
# =============================================================================
mcp = FastMCP("mcp-postgresql-ops")

# Prompt template path
PROMPT_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "prompt_template.md")

# =============================================================================
# MCP Tools (PostgreSQL Operations Tools)

@mcp.tool()
async def get_lock_monitoring(
    database_name: str = None,
    granted: str = None, 
    state: str = None,
    mode: str = None,
    locktype: str = None,
    username: str = None
) -> str:
    """
    [Tool Purpose]: Monitor current locks and potential deadlocks in PostgreSQL
    
    [Exact Functionality]:
    - List all current locks held and waited for by sessions
    - Show blocked and blocking sessions, lock types, and wait status
    - Help diagnose lock contention and deadlock risk
    - Filter results by granted status, state, mode, lock type, or username
    
    [Required Use Cases]:
    - When user requests "lock monitoring", "deadlock check", "blocked sessions", etc.
    - When diagnosing performance issues due to locking
    - When checking for blocked or waiting queries
    - When filtering specific types of locks or users
    
    [Strictly Prohibited Use Cases]:
    - Requests for killing sessions or force-unlocking
    - Requests for lock configuration changes
    - Requests for historical lock data (only current state is shown)
    
    Args:
        database_name: Database name to analyze (uses default database if omitted)
        granted: Filter by granted status ("true" or "false")
        state: Filter by session state ("active", "idle", "idle in transaction", etc.)
        mode: Filter by lock mode ("AccessShareLock", "ExclusiveLock", etc.)
        locktype: Filter by lock type ("relation", "transactionid", "virtualxid", etc.)
        username: Filter by specific username
    
    Returns:
        Table-format information showing PID, user, database, lock type, relation, mode, granted, waiting, and blocked-by info
    """
    try:
        # Build WHERE conditions based on filters
        where_conditions = []
        params = []
        param_count = 0
        
        if granted is not None:
            param_count += 1
            where_conditions.append(f"l.granted = ${param_count}")
            params.append(granted.lower() == "true")
            
        if state:
            param_count += 1
            where_conditions.append(f"a.state ILIKE ${param_count}")
            params.append(f"%{state}%")
            
        if mode:
            param_count += 1
            where_conditions.append(f"l.mode ILIKE ${param_count}")
            params.append(f"%{mode}%")
            
        if locktype:
            param_count += 1
            where_conditions.append(f"l.locktype ILIKE ${param_count}")
            params.append(f"%{locktype}%")
            
        if username:
            param_count += 1
            where_conditions.append(f"a.usename ILIKE ${param_count}")
            params.append(f"%{username}%")
        
        # Build WHERE clause
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f'''
        SELECT
            a.pid,
            a.usename AS username,
            a.datname AS database,
            l.locktype,
            l.mode,
            l.granted,
            l.relation::regclass AS relation,
            a.state,
            a.query_start,
            LEFT(a.query, 80) AS query,
            l.virtualtransaction,
            l.virtualxid,
            l.transactionid,
            l.fastpath,
            a.wait_event_type,
            a.wait_event,
            bl.pid AS blocked_by
        FROM pg_locks l
        JOIN pg_stat_activity a ON l.pid = a.pid
        LEFT JOIN pg_locks bl_l
            ON l.locktype = bl_l.locktype
            AND l.database IS NOT DISTINCT FROM bl_l.database
            AND l.relation IS NOT DISTINCT FROM bl_l.relation
            AND l.page IS NOT DISTINCT FROM bl_l.page
            AND l.tuple IS NOT DISTINCT FROM bl_l.tuple
            AND l.transactionid IS NOT DISTINCT FROM bl_l.transactionid
            AND l.pid <> bl_l.pid
            AND NOT l.granted AND bl_l.granted
        LEFT JOIN pg_stat_activity bl ON bl_l.pid = bl.pid
        {where_clause}
        ORDER BY a.datname, a.pid, l.locktype, l.mode
        '''
        
        locks = await execute_query(query, params, database=database_name)
        
        # Build title with filter information
        title = "Current Locks and Blocked Sessions"
        if database_name:
            title += f" (Database: {database_name})"
            
        filters = []
        if granted is not None:
            filters.append(f"granted={granted}")
        if state:
            filters.append(f"state='{state}'")
        if mode:
            filters.append(f"mode='{mode}'")
        if locktype:
            filters.append(f"locktype='{locktype}'")
        if username:
            filters.append(f"username='{username}'")
            
        if filters:
            title += f" [Filters: {', '.join(filters)}]"
            
        return format_table_data(locks, title)
    except Exception as e:
        logger.error(f"Failed to get lock monitoring info: {e}")
        return f"Error retrieving lock monitoring information: {str(e)}"


@mcp.tool()
async def get_wal_status() -> str:
    """
    [Tool Purpose]: Monitor WAL (Write Ahead Log) status and statistics
    
    [Exact Functionality]:
    - Show current WAL location and LSN information
    - Display WAL file generation rate and size statistics
    - Monitor WAL archiving status and lag
    - Provide WAL-related configuration and activity metrics
    
    [Required Use Cases]:
    - When user requests "WAL status", "WAL monitoring", "log shipping status", etc.
    - When diagnosing replication lag or WAL archiving issues
    - When monitoring database write activity and WAL generation
    
    [Strictly Prohibited Use Cases]:
    - Requests for WAL configuration changes
    - Requests for manual WAL switching or archiving
    - Requests for WAL file manipulation or cleanup
    
    Returns:
        WAL status information including current LSN, WAL files, archiving status, and statistics
    """
    try:
        # Get WAL status and statistics
        wal_query = """
        SELECT 
            pg_current_wal_lsn() as current_wal_lsn,
            pg_wal_lsn_diff(pg_current_wal_lsn(), '0/0') / 1024 / 1024 as wal_mb_generated,
            CASE WHEN pg_is_in_recovery() THEN 'Recovery (Standby)' ELSE 'Primary' END as server_role,
            pg_is_in_recovery() as in_recovery
        """
        
        wal_info = await execute_query(wal_query)
        
        # Get WAL archiving statistics (if available)
        archiver_query = """
        SELECT 
            archived_count,
            last_archived_wal,
            last_archived_time,
            failed_count,
            last_failed_wal,
            last_failed_time,
            stats_reset
        FROM pg_stat_archiver
        """
        
        archiver_stats = await execute_query(archiver_query)
        
        # Get WAL settings
        config_query = """
        SELECT name, setting, unit
        FROM pg_settings 
        WHERE name IN (
            'wal_level', 'archive_mode', 'archive_command',
            'max_wal_size', 'min_wal_size', 'checkpoint_segments',
            'checkpoint_completion_target', 'wal_buffers'
        )
        ORDER BY name
        """
        
        wal_config = await execute_query(config_query)
        
        result = []
        result.append("=== WAL Status Information ===\n")
        result.append(format_table_data(wal_info, "Current WAL Status"))
        result.append("\n" + format_table_data(archiver_stats, "WAL Archiver Statistics"))
        result.append("\n" + format_table_data(wal_config, "WAL Configuration Settings"))
        
        return "\n".join(result)
        
    except Exception as e:
        logger.error(f"Failed to get WAL status: {e}")
        return f"Error retrieving WAL status information: {str(e)}"


@mcp.tool()
async def get_replication_status() -> str:
    """
    [Tool Purpose]: Monitor PostgreSQL replication status and statistics
    
    [Exact Functionality]:
    - Show current replication connections and their status
    - Display replication lag information for standbys
    - Monitor WAL sender and receiver processes
    - Provide replication slot information and statistics
    
    [Required Use Cases]:
    - When user requests "replication status", "standby lag", "replication monitoring", etc.
    - When diagnosing replication issues or performance problems
    - When checking replication slot usage and lag
    
    [Strictly Prohibited Use Cases]:
    - Requests for replication configuration changes
    - Requests for replication slot creation or deletion
    - Requests for failover or switchover operations
    
    Returns:
        Replication status including connections, lag information, slots, and statistics
    """
    try:
        # Get replication connections (from primary)
        repl_query = """
        SELECT 
            client_addr,
            client_hostname,
            client_port,
            usename,
            application_name,
            state,
            sent_lsn,
            write_lsn,
            flush_lsn,
            replay_lsn,
            write_lag,
            flush_lag,
            replay_lag,
            sync_priority,
            sync_state,
            backend_start
        FROM pg_stat_replication
        ORDER BY client_addr
        """
        
        repl_connections = await execute_query(repl_query)
        
        # Get replication slots
        slots_query = """
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
        
        repl_slots = await execute_query(slots_query)
        
        # Get WAL receiver status (from standby)
        # PostgreSQL 16+ uses written_lsn/flushed_lsn, older versions use received_lsn
        receiver_query = """
        SELECT 
            pid,
            status,
            receive_start_lsn,
            receive_start_tli,
            CASE 
                WHEN EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name = 'pg_stat_wal_receiver' 
                           AND column_name = 'written_lsn')
                THEN written_lsn::text
                ELSE NULL::text
            END AS written_lsn,
            CASE 
                WHEN EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name = 'pg_stat_wal_receiver' 
                           AND column_name = 'flushed_lsn')
                THEN flushed_lsn::text
                ELSE NULL::text
            END AS flushed_lsn,
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
        
        wal_receiver = await execute_query(receiver_query)
        
        result = []
        result.append("=== Replication Status Information ===\n")
        
        if repl_connections:
            result.append(format_table_data(repl_connections, "Replication Connections (Primary Side)"))
        else:
            result.append("No active replication connections found (this may be a standby server)\n")
        
        if repl_slots:
            result.append("\n" + format_table_data(repl_slots, "Replication Slots"))
        else:
            result.append("\nNo replication slots found")
        
        if wal_receiver:
            result.append("\n" + format_table_data(wal_receiver, "WAL Receiver Status (Standby Side)"))
        else:
            result.append("\nNo WAL receiver process found (this may be a primary server)")
        
        return "\n".join(result)
        
    except Exception as e:
        logger.error(f"Failed to get replication status: {e}")
        return f"Error retrieving replication status information: {str(e)}"
# =============================================================================

@mcp.tool()
async def get_server_info() -> str:
    """
    [Tool Purpose]: Check basic information and connection status of PostgreSQL server
    
    [Exact Functionality]:
    - Retrieve PostgreSQL server version information
    - Display connection settings (with password masking)
    - Verify server accessibility
    - Check installation status of extensions (pg_stat_statements, pg_stat_monitor)
    
    [Required Use Cases]:
    - When user requests "server info", "PostgreSQL status", "connection check", etc.
    - When basic database server information is needed
    - When preliminary check is needed before using monitoring tools
    
    [Strictly Prohibited Use Cases]:
    - Requests for specific data or table information
    - Requests for performance statistics or monitoring data
    - Requests for configuration changes or administrative tasks
    
    Returns:
        Comprehensive information including server version, connection info, and extension status
    """
    try:
        # Retrieve server version
        version = await get_server_version()
        
        # Connection information (with password masking)
        conn_info = sanitize_connection_info()
        
        # Check extension status
        pg_stat_statements_exists = await check_extension_exists("pg_stat_statements")
        pg_stat_monitor_exists = await check_extension_exists("pg_stat_monitor")
        
        result = []
        result.append("=== PostgreSQL Server Information ===\n")
        result.append(f"Version: {version}")
        result.append(f"Host: {conn_info['host']}")
        result.append(f"Port: {conn_info['port']}")
        result.append(f"Database: {conn_info['database']}")
        result.append(f"User: {conn_info['user']}")
        result.append("")
        result.append("=== Extension Status ===")
        result.append(f"pg_stat_statements: {'✓ Installed' if pg_stat_statements_exists else '✗ Not installed'}")
        result.append(f"pg_stat_monitor: {'✓ Installed' if pg_stat_monitor_exists else '✗ Not installed'}")
        
        return "\n".join(result)
        
    except Exception as e:
        logger.error(f"Failed to get server info: {e}")
        return f"Error retrieving server information: {str(e)}"


@mcp.tool()
async def get_database_list() -> str:
    """
    [Tool Purpose]: Retrieve list of all databases and their basic information on PostgreSQL server
    
    [Exact Functionality]:
    - Retrieve list of all databases on the server
    - Display owner, encoding, and size information for each database
    - Include database connection limit information
    
    [Required Use Cases]:
    - When user requests "database list", "DB list", "database info", etc.
    - When need to check what databases exist on the server
    - When database size or owner information is needed
    
    [Strictly Prohibited Use Cases]:
    - Requests for tables or schemas inside specific databases
    - Requests for database creation or deletion
    - Requests related to user permissions or security
    
    Returns:
        Table-format information including database name, owner, encoding, size, and connection limit
    """
    try:
        query = """
        SELECT 
            d.datname as database_name,
            u.usename as owner,
            d.encoding,
            pg_encoding_to_char(d.encoding) as encoding_name,
            CASE WHEN d.datconnlimit = -1 THEN 'unlimited' 
                 ELSE d.datconnlimit::text END as connection_limit,
            pg_size_pretty(pg_database_size(d.datname)) as size
        FROM pg_database d
        JOIN pg_user u ON d.datdba = u.usesysid
        ORDER BY d.datname
        """
        
        databases = await execute_query(query)
        return format_table_data(databases, "Database List")
        
    except Exception as e:
        logger.error(f"Failed to get database list: {e}")
        return f"Error retrieving database list: {str(e)}"


@mcp.tool()
async def get_table_list(database_name: str = None) -> str:
    """
    [Tool Purpose]: Retrieve list of all tables and their information from specified database (or current DB)
    
    [Exact Functionality]:
    - Retrieve list of all tables in specified database
    - Display schema, owner, and size information for each table
    - Distinguish table types (regular tables, views, etc.)
    
    [Required Use Cases]:
    - When user requests "table list", "table listing", "schema info", etc.
    - When need to understand structure of specific database
    - When table size or owner information is needed
    
    [Strictly Prohibited Use Cases]:
    - Requests for data inside tables
    - Requests for table structure changes or creation/deletion
    - Requests for detailed column information of specific tables
    
    Args:
        database_name: Database name to query (uses currently connected database if omitted)
    
    Returns:
        Table-format information including table name, schema, owner, type, and size
    """
    try:
        query = """
        SELECT 
            schemaname as schema_name,
            tablename as table_name,
            tableowner as owner,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
        FROM pg_tables 
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
        ORDER BY schemaname, tablename
        """
        
        # Execute query on specified database or default
        tables = await execute_query(query, database=database_name)
        title = f"Table List"
        if database_name:
            title += f" (Database: {database_name})"
            
        return format_table_data(tables, title)
        
    except Exception as e:
        logger.error(f"Failed to get table list: {e}")
        return f"Error retrieving table list: {str(e)}"


@mcp.tool()
async def get_user_list() -> str:
    """
    [Tool Purpose]: Retrieve list of all user accounts and permission information on PostgreSQL server
    
    [Exact Functionality]:
    - Retrieve list of all database user accounts
    - Display permission information for each user (superuser, database creation rights, etc.)
    - Include account creation date and expiration date information
    
    [Required Use Cases]:
    - When user requests "user list", "account info", "permission check", etc.
    - When user permission management or security inspection is needed
    - When account status overview is needed
    
    [Strictly Prohibited Use Cases]:
    - Requests for user password information
    - Requests for user creation, deletion, or permission changes
    - Requests for specific user sessions or activity history
    
    Returns:
        Table-format information including username, superuser status, permissions, and account status
    """
    try:
        # PostgreSQL 버전 호환성을 위해 pg_roles 사용
        query = """
        SELECT 
            rolname as username,
            oid as user_id,
            CASE WHEN rolsuper THEN 'Yes' ELSE 'No' END as is_superuser,
            CASE WHEN rolcreatedb THEN 'Yes' ELSE 'No' END as can_create_db,
            CASE WHEN rolcreaterole THEN 'Yes' ELSE 'No' END as can_create_role,
            CASE WHEN rolcanlogin THEN 'Yes' ELSE 'No' END as can_login,
            CASE WHEN rolreplication THEN 'Yes' ELSE 'No' END as replication,
            rolconnlimit as connection_limit,
            rolvaliduntil as valid_until
        FROM pg_roles
        WHERE rolcanlogin = true  -- 로그인 가능한 사용자만
        ORDER BY rolname
        """
        
        users = await execute_query(query)
        return format_table_data(users, "Database Users")
        
    except Exception as e:
        logger.error(f"Failed to get user list: {e}")
        return f"Error retrieving user list: {str(e)}"


@mcp.tool()
async def get_active_connections() -> str:
    """
    [Tool Purpose]: Retrieve all active connections and session information on current PostgreSQL server
    
    [Exact Functionality]:
    - Retrieve list of all currently active connected sessions
    - Display user, database, and client address for each connection
    - Include session status and currently executing query information
    
    [Required Use Cases]:
    - When user requests "active connections", "current sessions", "connection status", etc.
    - When server load or performance problem diagnosis is needed
    - When checking connection status of specific users or applications
    
    [Strictly Prohibited Use Cases]:
    - Requests for forceful connection termination or session management
    - Requests for detailed query history of specific sessions
    - Requests for connection security or authentication-related changes
    
    Returns:
        Information including PID, username, database name, client address, status, and current query
    """
    try:
        query = """
        SELECT 
            pid,
            usename as username,
            datname as database_name,
            client_addr,
            client_port,
            state,
            query_start,
            LEFT(query, 100) as current_query
        FROM pg_stat_activity 
        WHERE pid <> pg_backend_pid()
        ORDER BY query_start DESC
        """
        
        connections = await execute_query(query)
        return format_table_data(connections, "Active Connections")
        
    except Exception as e:
        logger.error(f"Failed to get active connections: {e}")
        return f"Error retrieving active connections: {str(e)}"


@mcp.tool()
async def get_pg_stat_statements_top_queries(limit: int = 20, database_name: str = None) -> str:
    """
    [Tool Purpose]: Analyze top queries that consumed the most time using pg_stat_statements extension
    
    [Exact Functionality]:
    - Retrieve top query list based on total execution time
    - Display call count, average execution time, and cache hit rate for each query
    - Support identification of queries requiring performance optimization
    
    [Required Use Cases]:
    - When user requests "slow queries", "performance analysis", "top queries", etc.
    - When database performance optimization is needed
    - When query performance monitoring or tuning is required
    
    [Strictly Prohibited Use Cases]:
    - When pg_stat_statements extension is not installed
    - Requests for query execution or data modification
    - Requests for statistics data reset or configuration changes
    
    Args:
        limit: Number of top queries to retrieve (default: 20, max: 100)
        database_name: Database name to analyze (uses default database if omitted)
    
    Returns:
        Performance statistics including query text, call count, total execution time, average execution time, and cache hit rate
    """
    try:
        # Check extension exists
        if not await check_extension_exists("pg_stat_statements"):
            return "Error: pg_stat_statements extension is not installed or enabled"
        
        # Limit range constraint
        limit = max(1, min(limit, 100))
        
        data = await get_pg_stat_statements_data(limit, database=database_name)
        
        title = f"Top {limit} Queries by Total Execution Time (pg_stat_statements)"
        if database_name:
            title += f" (Database: {database_name})"
            
        return format_table_data(data, title)
        
    except Exception as e:
        logger.error(f"Failed to get pg_stat_statements data: {e}")
        return f"Error retrieving pg_stat_statements data: {str(e)}"


@mcp.tool()
async def get_pg_stat_monitor_recent_queries(limit: int = 20, database_name: str = None) -> str:
    """
    [Tool Purpose]: Analyze recently executed queries and detailed monitoring information using pg_stat_monitor extension
    
    [Exact Functionality]:
    - Retrieve detailed performance information of recently executed queries
    - Display client IP and time bucket information by execution period
    - Provide more detailed monitoring data than pg_stat_statements
    
    [Required Use Cases]:
    - When user requests "recent queries", "detailed monitoring", "pg_stat_monitor", etc.
    - When real-time query performance monitoring is needed
    - When client-specific or time-based query analysis is required
    
    [Strictly Prohibited Use Cases]:
    - When pg_stat_monitor extension is not installed
    - Requests for query execution or data modification
    - Requests for monitoring configuration changes or data reset
    
    Args:
        limit: Number of recent queries to retrieve (default: 20, max: 100)
        database_name: Database name to analyze (uses default database if omitted)
    
    Returns:
        Detailed monitoring information including query text, execution statistics, client info, and bucket time
    """
    try:
        # Check extension exists
        if not await check_extension_exists("pg_stat_monitor"):
            return "Error: pg_stat_monitor extension is not installed or enabled"
        
        # Limit range constraint
        limit = max(1, min(limit, 100))
        
        data = await get_pg_stat_monitor_data(limit, database=database_name)
        
        title = f"Recent {limit} Queries (pg_stat_monitor)"
        if database_name:
            title += f" (Database: {database_name})"
            
        return format_table_data(data, title)
        
    except Exception as e:
        logger.error(f"Failed to get pg_stat_monitor data: {e}")
        return f"Error retrieving pg_stat_monitor data: {str(e)}"


@mcp.tool()
async def get_database_size_info() -> str:
    """
    [Tool Purpose]: Analyze size information and storage usage status of all databases in PostgreSQL server
    
    [Exact Functionality]:
    - Retrieve disk usage for each database
    - Analyze overall server storage usage status
    - Provide database list sorted by size
    
    [Required Use Cases]:
    - When user requests "database size", "disk usage", "storage space", etc.
    - When capacity management or cleanup is needed
    - When resource usage status by database needs to be identified
    
    [Strictly Prohibited Use Cases]:
    - Requests for data deletion or cleanup operations
    - Requests for storage configuration changes
    - Requests related to backup or restore
    
    Returns:
        Table-format information with database names and size information sorted by size
    """
    try:
        query = """
        SELECT 
            datname as database_name,
            pg_size_pretty(pg_database_size(datname)) as size,
            pg_database_size(datname) as size_bytes
        FROM pg_database 
        WHERE datistemplate = false
        ORDER BY pg_database_size(datname) DESC
        """
        
        sizes = await execute_query(query)
        
        # Calculate total size
        total_size = sum(row['size_bytes'] for row in sizes)
        
        result = []
        result.append(f"Total size of all databases: {format_bytes(total_size)}\n")
        
        # Remove size_bytes column (not for display)
        for row in sizes:
            del row['size_bytes']
            
        result.append(format_table_data(sizes, "Database Sizes"))
        
        return "\n".join(result)
        
    except Exception as e:
        logger.error(f"Failed to get database size info: {e}")
        return f"Error retrieving database size information: {str(e)}"


@mcp.tool()
async def get_table_size_info(schema_name: str = "public", database_name: str = None) -> str:
    """
    [Tool Purpose]: Analyze size information and index usage of all tables in specified schema
    
    [Exact Functionality]:
    - Retrieve size information of all tables within schema
    - Analyze index size and total size per table
    - Provide table list sorted by size
    
    [Required Use Cases]:
    - When user requests "table size", "schema capacity", "index usage", etc.
    - When storage analysis of specific schema is needed
    - When resource usage status per table needs to be identified
    
    [Strictly Prohibited Use Cases]:
    - Requests for table data deletion or cleanup operations
    - Requests for index creation or deletion
    - Requests for table structure changes
    
    Args:
        schema_name: Schema name to analyze (default: "public")
        database_name: Database name to analyze (uses default database if omitted)
    
    Returns:
        Information sorted by size including table name, table size, index size, and total size
    """
    try:
        query = """
        SELECT 
            schemaname as schema_name,
            tablename as table_name,
            pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
            pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) as index_size,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
            pg_total_relation_size(schemaname||'.'||tablename) as total_size_bytes
        FROM pg_tables 
        WHERE schemaname = $1
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """
        
        tables = await execute_query(query, [schema_name], database=database_name)
        
        if not tables:
            db_info = f" in database '{database_name}'" if database_name else ""
            return f"No tables found in schema '{schema_name}'{db_info}"
        
        # Calculate total size
        total_size = sum(row['total_size_bytes'] for row in tables)
        
        result = []
        db_info = f" in database '{database_name}'" if database_name else ""
        result.append(f"Total size of tables in schema '{schema_name}'{db_info}: {format_bytes(total_size)}\n")
        
        # Remove total_size_bytes column
        for row in tables:
            del row['total_size_bytes']
            
        title = f"Table Sizes in Schema '{schema_name}'"
        if database_name:
            title += f" (Database: {database_name})"
        result.append(format_table_data(tables, title))
        
        return "\n".join(result)
        
    except Exception as e:
        logger.error(f"Failed to get table size info: {e}")
        return f"Error retrieving table size information: {str(e)}"


@mcp.tool()
async def get_postgresql_config(config_name: str = None, filter_text: str = None) -> str:
    """
    [Tool Purpose]: Retrieve and analyze PostgreSQL server configuration parameter values
    
    [Exact Functionality]:
    - Retrieve all PostgreSQL configuration parameters (when config_name is not specified)
    - Retrieve current value and description of specific configuration parameter
    - Filter configurations by text pattern (when filter_text is specified)
    - Display whether configuration can be changed and if restart is required
    
    [Required Use Cases]:
    - When user requests "PostgreSQL config", "config", "parameters", etc.
    - When checking specific configuration values is needed
    - When searching for configurations containing specific text
    - When configuration status identification is needed for performance tuning
    
    [Strictly Prohibited Use Cases]:
    - Requests for configuration value changes or modifications
    - Requests for PostgreSQL restart or reload
    - Requests for system-level configuration changes
    
    Args:
        config_name: Specific configuration parameter name to retrieve (shows all configs if omitted)
        filter_text: Text to filter configuration names or descriptions (optional)
    
    Returns:
        Configuration information including parameter name, current value, unit, description, and changeability
    """
    try:
        if config_name:
            # Retrieve specific configuration
            query = """
            SELECT 
                name,
                setting,
                unit,
                category,
                short_desc,
                context,
                vartype,
                source,
                min_val,
                max_val,
                boot_val,
                reset_val
            FROM pg_settings 
            WHERE name = $1
            """
            config = await execute_query(query, [config_name])
            
            if not config:
                return f"Configuration parameter '{config_name}' not found"
                
            return format_table_data(config, f"Configuration: {config_name}")
        
        elif filter_text:
            # Filter configurations by text pattern
            query = """
            SELECT 
                name,
                setting,
                unit,
                category,
                short_desc,
                context,
                source
            FROM pg_settings 
            WHERE name ILIKE $1 OR short_desc ILIKE $1
            ORDER BY category, name
            """
            filter_pattern = f"%{filter_text}%"
            configs = await execute_query(query, [filter_pattern])
            
            if not configs:
                return f"No configuration parameters found matching '{filter_text}'"
            
            return format_table_data(configs, f"PostgreSQL Configurations containing '{filter_text}' ({len(configs)} found)")
        
        else:
            # Retrieve all configurations
            query = """
            SELECT 
                name,
                setting,
                unit,
                category,
                short_desc,
                context,
                source
            FROM pg_settings 
            ORDER BY category, name
            """
            configs = await execute_query(query)
            return format_table_data(configs, "All PostgreSQL Configuration Parameters")
            
    except Exception as e:
        logger.error(f"Failed to get PostgreSQL config: {e}")
        return f"Error retrieving PostgreSQL configuration: {str(e)}"


@mcp.tool()
async def get_index_usage_stats(database_name: str = None) -> str:
    """
    [Tool Purpose]: Analyze usage rate and performance statistics of all indexes in database
    
    [Exact Functionality]:
    - Analyze usage frequency and efficiency of all indexes
    - Identify unused indexes
    - Provide scan count and tuple return statistics per index
    
    [Required Use Cases]:
    - When user requests "index usage rate", "index performance", "unnecessary indexes", etc.
    - When database performance optimization is needed
    - When index cleanup or reorganization is required
    
    [Strictly Prohibited Use Cases]:
    - Requests for index creation or deletion
    - Requests for index reorganization or REINDEX execution
    - Requests for statistics reset
    
    Args:
        database_name: Database name to analyze (uses default database if omitted)
    
    Returns:
        Index usage statistics including schema, table, index name, scans, and tuples read
    """
    try:
        query = """
        SELECT 
            schemaname as schema_name,
            relname as table_name,
            indexrelname as index_name,
            idx_scan as scans,
            idx_tup_read as tuples_read,
            idx_tup_fetch as tuples_fetched,
            CASE 
                WHEN idx_scan = 0 THEN 'Never used'
                WHEN idx_scan < 100 THEN 'Low usage'
                WHEN idx_scan < 1000 THEN 'Medium usage'
                ELSE 'High usage'
            END as usage_level
        FROM pg_stat_user_indexes
        ORDER BY idx_scan DESC, schemaname, relname, indexrelname
        """
        
        indexes = await execute_query(query, database=database_name)
        
        title = "Index Usage Statistics"
        if database_name:
            title += f" (Database: {database_name})"
            
        return format_table_data(indexes, title)
        
    except Exception as e:
        logger.error(f"Failed to get index usage stats: {e}")
        return f"Error retrieving index usage statistics: {str(e)}"


@mcp.tool()
async def get_vacuum_analyze_stats(database_name: str = None) -> str:
    """
    [Tool Purpose]: Analyze VACUUM and ANALYZE execution history and statistics per table
    
    [Exact Functionality]:
    - Retrieve last VACUUM/ANALYZE execution time for each table
    - Provide Auto VACUUM/ANALYZE execution count statistics
    - Analyze table activity with tuple insert/update/delete statistics
    
    [Required Use Cases]:
    - When user requests "VACUUM status", "ANALYZE history", "table statistics", etc.
    - When database maintenance status overview is needed
    - When performance issues or statistics update status verification is required
    
    [Strictly Prohibited Use Cases]:
    - Requests for VACUUM or ANALYZE execution
    - Requests for Auto VACUUM configuration changes
    - Requests for forced statistics update
    
    Args:
        database_name: Database name to analyze (uses default database if omitted)
    
    Returns:
        Schema name, table name, last VACUUM time, last ANALYZE time, and execution count statistics
    """
    try:
        query = """
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
            autoanalyze_count,
            n_tup_ins as inserts,
            n_tup_upd as updates,
            n_tup_del as deletes
        FROM pg_stat_user_tables
        ORDER BY schemaname, relname
        """
        
        stats = await execute_query(query, database=database_name)
        
        title = "VACUUM/ANALYZE Statistics"
        if database_name:
            title += f" (Database: {database_name})"
            
        return format_table_data(stats, title)
        
    except Exception as e:
        logger.error(f"Failed to get vacuum/analyze stats: {e}")
        return f"Error retrieving VACUUM/ANALYZE statistics: {str(e)}"


@mcp.tool()
async def get_database_stats() -> str:
    """
    [Tool Purpose]: Get comprehensive database-wide statistics and performance metrics
    
    [Exact Functionality]:
    - Show database-wide transaction statistics (commits, rollbacks)
    - Display block I/O statistics (disk reads vs buffer hits)
    - Provide tuple operation statistics (returned, fetched, inserted, updated, deleted)
    - Show temporary file usage and deadlock counts
    - Include checksum failure information and I/O timing data
    
    [Required Use Cases]:
    - When user requests "database statistics", "database performance", "transaction stats", etc.
    - When analyzing overall database performance and activity
    - When investigating I/O performance or buffer cache efficiency
    - When checking for deadlocks or temporary file usage
    
    [Strictly Prohibited Use Cases]:
    - Requests for statistics reset or modification
    - Requests for database configuration changes
    - Requests for performance tuning actions
    
    Returns:
        Comprehensive database statistics including transactions, I/O, tuples, and performance metrics
    """
    try:
        query = """
        SELECT 
            datname as database_name,
            numbackends as active_connections,
            xact_commit as transactions_committed,
            xact_rollback as transactions_rolled_back,
            ROUND((xact_commit::numeric / NULLIF(xact_commit + xact_rollback, 0)) * 100, 2) as commit_ratio_percent,
            blks_read as disk_blocks_read,
            blks_hit as buffer_blocks_hit,
            CASE 
                WHEN blks_read + blks_hit > 0 THEN 
                    ROUND((blks_hit::numeric / (blks_read + blks_hit)) * 100, 2)
                ELSE 0
            END as buffer_hit_ratio_percent,
            tup_returned as tuples_returned,
            tup_fetched as tuples_fetched,
            tup_inserted as tuples_inserted,
            tup_updated as tuples_updated,
            tup_deleted as tuples_deleted,
            conflicts as query_conflicts,
            temp_files as temporary_files_created,
            pg_size_pretty(temp_bytes) as temp_files_size,
            deadlocks as deadlock_count,
            COALESCE(checksum_failures, 0) as checksum_failures,
            CASE 
                WHEN checksum_last_failure IS NOT NULL THEN
                    checksum_last_failure::text
                ELSE 'None'
            END as last_checksum_failure,
            COALESCE(ROUND(blk_read_time::numeric, 2), 0) as disk_read_time_ms,
            COALESCE(ROUND(blk_write_time::numeric, 2), 0) as disk_write_time_ms,
            stats_reset
        FROM pg_stat_database 
        WHERE datname IS NOT NULL
        ORDER BY datname
        """
        
        stats = await execute_query(query)
        return format_table_data(stats, "Database Statistics")
        
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return f"Error retrieving database statistics: {str(e)}"


@mcp.tool()
async def get_bgwriter_stats() -> str:
    """
    [Tool Purpose]: Analyze background writer and checkpoint performance statistics
    
    [Exact Functionality]:
    - Show checkpoint execution statistics (timed vs requested)
    - Display checkpoint timing information (write and sync times)
    - Provide buffer writing statistics by different processes
    - Analyze background writer performance and efficiency
    
    [Required Use Cases]:
    - When user requests "checkpoint stats", "bgwriter performance", "buffer stats", etc.
    - When analyzing I/O performance and checkpoint impact
    - When investigating background writer efficiency
    - When troubleshooting checkpoint-related performance issues
    
    [Strictly Prohibited Use Cases]:
    - Requests for checkpoint execution or configuration changes
    - Requests for background writer parameter modifications
    - Requests for statistics reset
    
    Returns:
        Background writer and checkpoint performance statistics
    """
    try:
        query = """
        SELECT 
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
            CASE 
                WHEN buffers_clean > 0 AND maxwritten_clean > 0 THEN
                    ROUND((maxwritten_clean::numeric / buffers_clean) * 100, 2)
                ELSE 0
            END as bgwriter_stop_ratio_percent,
            stats_reset as stats_reset_time
        FROM pg_stat_bgwriter
        """
        
        stats = await execute_query(query)
        return format_table_data(stats, "Background Writer Statistics")
        
    except Exception as e:
        logger.error(f"Failed to get bgwriter stats: {e}")
        return f"Error retrieving background writer statistics: {str(e)}"


@mcp.tool()
async def get_table_io_stats(database_name: str = None, schema_name: str = "public") -> str:
    """
    [Tool Purpose]: Analyze I/O performance statistics for tables (disk reads vs buffer cache hits)
    
    [Exact Functionality]:
    - Show heap, index, and TOAST table I/O statistics
    - Calculate buffer hit ratios for performance analysis
    - Identify tables with poor buffer cache performance
    - Provide detailed I/O breakdown by table component
    
    [Required Use Cases]:
    - When user requests "table I/O stats", "buffer performance", "disk vs cache", etc.
    - When analyzing table-level I/O performance
    - When identifying tables causing excessive disk I/O
    - When optimizing buffer cache efficiency
    
    [Strictly Prohibited Use Cases]:
    - Requests for I/O optimization actions
    - Requests for buffer cache configuration changes
    - Requests for statistics reset
    
    Args:
        database_name: Database name to analyze (uses default database if omitted)
        schema_name: Schema name to filter (default: public)
    
    Returns:
        Table I/O statistics including heap, index, and TOAST performance metrics
    """
    try:
        where_clause = "WHERE schemaname = $1" if schema_name else ""
        params = [schema_name] if schema_name else None
        
        query = f"""
        SELECT 
            schemaname as schema_name,
            relname as table_name,
            heap_blks_read as heap_disk_reads,
            heap_blks_hit as heap_buffer_hits,
            CASE 
                WHEN heap_blks_read + heap_blks_hit > 0 THEN
                    ROUND((heap_blks_hit::numeric / (heap_blks_read + heap_blks_hit)) * 100, 2)
                ELSE 0
            END as heap_hit_ratio_percent,
            idx_blks_read as index_disk_reads,
            idx_blks_hit as index_buffer_hits,
            CASE 
                WHEN idx_blks_read + idx_blks_hit > 0 THEN
                    ROUND((idx_blks_hit::numeric / (idx_blks_read + idx_blks_hit)) * 100, 2)
                ELSE 0
            END as index_hit_ratio_percent,
            COALESCE(toast_blks_read, 0) as toast_disk_reads,
            COALESCE(toast_blks_hit, 0) as toast_buffer_hits,
            CASE 
                WHEN COALESCE(toast_blks_read, 0) + COALESCE(toast_blks_hit, 0) > 0 THEN
                    ROUND((COALESCE(toast_blks_hit, 0)::numeric / 
                           (COALESCE(toast_blks_read, 0) + COALESCE(toast_blks_hit, 0))) * 100, 2)
                ELSE 0
            END as toast_hit_ratio_percent,
            COALESCE(tidx_blks_read, 0) as toast_idx_disk_reads,
            COALESCE(tidx_blks_hit, 0) as toast_idx_buffer_hits,
            heap_blks_read + idx_blks_read + COALESCE(toast_blks_read, 0) + COALESCE(tidx_blks_read, 0) as total_disk_reads
        FROM pg_statio_user_tables
        {where_clause}
        ORDER BY total_disk_reads DESC, schemaname, relname
        """
        
        stats = await execute_query(query, params, database=database_name)
        
        title = "Table I/O Statistics"
        if database_name:
            title += f" (Database: {database_name}"
            if schema_name:
                title += f", Schema: {schema_name}"
            title += ")"
        elif schema_name:
            title += f" (Schema: {schema_name})"
            
        return format_table_data(stats, title)
        
    except Exception as e:
        logger.error(f"Failed to get table I/O stats: {e}")
        return f"Error retrieving table I/O statistics: {str(e)}"


@mcp.tool()
async def get_index_io_stats(database_name: str = None, schema_name: str = "public") -> str:
    """
    [Tool Purpose]: Analyze I/O performance statistics for indexes (disk reads vs buffer cache hits)
    
    [Exact Functionality]:
    - Show index-level I/O statistics and buffer hit ratios
    - Identify indexes with poor buffer cache performance
    - Provide detailed I/O performance metrics per index
    - Help optimize index and buffer cache usage
    
    [Required Use Cases]:
    - When user requests "index I/O stats", "index buffer performance", etc.
    - When analyzing index-level I/O performance
    - When identifying indexes causing excessive disk I/O
    - When optimizing index buffer cache efficiency
    
    [Strictly Prohibited Use Cases]:
    - Requests for index optimization actions
    - Requests for buffer cache configuration changes
    - Requests for statistics reset
    
    Args:
        database_name: Database name to analyze (uses default database if omitted)
        schema_name: Schema name to filter (default: public)
    
    Returns:
        Index I/O statistics including buffer hit ratios and performance metrics
    """
    try:
        where_clause = "WHERE schemaname = $1" if schema_name else ""
        params = [schema_name] if schema_name else None
        
        query = f"""
        SELECT 
            schemaname as schema_name,
            relname as table_name,
            indexrelname as index_name,
            idx_blks_read as disk_reads,
            idx_blks_hit as buffer_hits,
            idx_blks_read + idx_blks_hit as total_block_accesses,
            CASE 
                WHEN idx_blks_read + idx_blks_hit > 0 THEN
                    ROUND((idx_blks_hit::numeric / (idx_blks_read + idx_blks_hit)) * 100, 2)
                ELSE 0
            END as buffer_hit_ratio_percent,
            CASE 
                WHEN idx_blks_read + idx_blks_hit = 0 THEN 'No I/O activity'
                WHEN idx_blks_read > idx_blks_hit THEN 'Disk-heavy'
                WHEN idx_blks_hit > idx_blks_read * 10 THEN 'Cache-friendly'
                ELSE 'Mixed I/O'
            END as io_pattern
        FROM pg_statio_user_indexes
        {where_clause}
        ORDER BY idx_blks_read DESC, schemaname, relname, indexrelname
        """
        
        stats = await execute_query(query, params, database=database_name)
        
        title = "Index I/O Statistics"
        if database_name:
            title += f" (Database: {database_name}"
            if schema_name:
                title += f", Schema: {schema_name}"
            title += ")"
        elif schema_name:
            title += f" (Schema: {schema_name})"
            
        return format_table_data(stats, title)
        
    except Exception as e:
        logger.error(f"Failed to get index I/O stats: {e}")
        return f"Error retrieving index I/O statistics: {str(e)}"


@mcp.tool()
async def get_all_tables_stats(database_name: str = None, include_system: bool = False) -> str:
    """
    [Tool Purpose]: Get comprehensive statistics for all tables (including system tables if requested)
    
    [Exact Functionality]:
    - Show detailed access statistics for all tables in database
    - Include sequential scans, index scans, and tuple operations
    - Provide live/dead tuple estimates and maintenance history
    - Option to include system catalog tables
    
    [Required Use Cases]:
    - When user requests "all tables stats", "complete table statistics", etc.
    - When analyzing overall table usage patterns
    - When investigating table maintenance needs across the database
    - When getting comprehensive database activity overview
    
    [Strictly Prohibited Use Cases]:
    - Requests for table maintenance operations (VACUUM, ANALYZE)
    - Requests for statistics reset or modification
    - Requests for table optimization actions
    
    Args:
        database_name: Database name to analyze (uses default database if omitted)
        include_system: Include system tables in results (default: False)
    
    Returns:
        Comprehensive table statistics including access patterns and maintenance history
    """
    try:
        view_name = "pg_stat_all_tables" if include_system else "pg_stat_user_tables"
        
        query = f"""
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
        
        stats = await execute_query(query, database=database_name)
        
        title = "All Tables Statistics"
        if include_system:
            title = "All Tables Statistics (Including System)"
        if database_name:
            title += f" (Database: {database_name})"
            
        return format_table_data(stats, title)
        
    except Exception as e:
        logger.error(f"Failed to get all tables stats: {e}")
        return f"Error retrieving all tables statistics: {str(e)}"


@mcp.tool()
async def get_user_functions_stats(database_name: str = None) -> str:
    """
    [Tool Purpose]: Analyze performance statistics for user-defined functions
    
    [Exact Functionality]:
    - Show execution count and timing statistics for user functions
    - Calculate average execution time per function call
    - Identify performance bottlenecks in user-defined functions
    - Provide total and self execution time breakdown
    
    [Required Use Cases]:
    - When user requests "function stats", "function performance", etc.
    - When analyzing user-defined function performance
    - When identifying slow or frequently called functions
    - When optimizing application function usage
    
    [Strictly Prohibited Use Cases]:
    - Requests for function modification or optimization
    - Requests for statistics reset
    - Requests for function execution or testing
    
    Args:
        database_name: Database name to analyze (uses default database if omitted)
    
    Returns:
        User-defined function performance statistics including call counts and timing
    """
    try:
        query = """
        SELECT 
            schemaname as schema_name,
            funcname as function_name,
            calls as total_calls,
            ROUND(total_time::numeric, 2) as total_time_ms,
            ROUND(self_time::numeric, 2) as self_time_ms,
            CASE 
                WHEN calls > 0 THEN
                    ROUND((total_time::numeric / calls), 4)
                ELSE 0
            END as avg_total_time_per_call_ms,
            CASE 
                WHEN calls > 0 THEN
                    ROUND((self_time::numeric / calls), 4)
                ELSE 0
            END as avg_self_time_per_call_ms,
            CASE 
                WHEN total_time > 0 THEN
                    ROUND((self_time::numeric / total_time::numeric) * 100, 2)
                ELSE 0
            END as self_time_ratio_percent,
            CASE 
                WHEN calls = 0 THEN 'Never called'
                WHEN calls < 10 THEN 'Low usage'
                WHEN calls < 100 THEN 'Medium usage'
                ELSE 'High usage'
            END as usage_level
        FROM pg_stat_user_functions
        ORDER BY total_time DESC, calls DESC, schemaname, funcname
        """
        
        stats = await execute_query(query, database=database_name)
        
        title = "User Functions Statistics"
        if database_name:
            title += f" (Database: {database_name})"
            
        return format_table_data(stats, title)
        
    except Exception as e:
        logger.error(f"Failed to get user functions stats: {e}")
        return f"Error retrieving user functions statistics: {str(e)}"


@mcp.tool()
async def get_database_conflicts_stats(database_name: str = None) -> str:
    """
    [Tool Purpose]: Analyze query conflicts in standby/replica database environments
    
    [Exact Functionality]:
    - Show conflict statistics for standby servers (only relevant on replicas)
    - Display conflicts by type (tablespace, lock, snapshot, bufferpin, deadlock)
    - Help diagnose replication-related performance issues
    - Provide conflict resolution statistics
    
    [Required Use Cases]:
    - When user requests "replication conflicts", "standby conflicts", etc.
    - When analyzing replica server performance issues
    - When troubleshooting replication lag or conflicts
    - When monitoring standby server health
    
    [Strictly Prohibited Use Cases]:
    - Requests for conflict resolution actions
    - Requests for replication configuration changes
    - Requests for statistics reset
    
    Args:
        database_name: Database name to analyze (uses default database if omitted)
    
    Returns:
        Database conflict statistics (meaningful only on standby servers)
    """
    try:
        query = """
        SELECT 
            datname as database_name,
            confl_tablespace as tablespace_conflicts,
            confl_lock as lock_timeout_conflicts,
            confl_snapshot as snapshot_conflicts,
            confl_bufferpin as buffer_pin_conflicts,
            confl_deadlock as deadlock_conflicts,
            confl_tablespace + confl_lock + confl_snapshot + 
            confl_bufferpin + confl_deadlock as total_conflicts,
            CASE 
                WHEN confl_tablespace + confl_lock + confl_snapshot + 
                     confl_bufferpin + confl_deadlock = 0 THEN 'No conflicts'
                WHEN confl_tablespace + confl_lock + confl_snapshot + 
                     confl_bufferpin + confl_deadlock < 10 THEN 'Low conflict rate'
                WHEN confl_tablespace + confl_lock + confl_snapshot + 
                     confl_bufferpin + confl_deadlock < 100 THEN 'Medium conflict rate'
                ELSE 'High conflict rate'
            END as conflict_level
        FROM pg_stat_database_conflicts
        WHERE datname IS NOT NULL
        ORDER BY total_conflicts DESC, datname
        """
        
        stats = await execute_query(query, database=database_name)
        
        if not stats:
            return "Database Conflicts Statistics\n\nNote: This server appears to be a primary server. Conflict statistics are only available on standby/replica servers."
        
        title = "Database Conflicts Statistics (Standby Server)"
        if database_name:
            title += f" (Database: {database_name})"
            
        return format_table_data(stats, title)
        
    except Exception as e:
        logger.error(f"Failed to get database conflicts stats: {e}")
        return f"Error retrieving database conflicts statistics: {str(e)}"


# =============================================================================
# Prompt Template Tools
# =============================================================================

@mcp.tool()
async def get_prompt_template(section: Optional[str] = None, mode: Optional[str] = None) -> str:
    """
    Returns the MCP prompt template (full, headings, or specific section).
    Args:
        section: Section number or keyword (optional)
        mode: 'full', 'headings', or None (optional)
    """
    template = read_prompt_template(PROMPT_TEMPLATE_PATH)
    
    if mode == "headings":
        headings, _ = parse_prompt_sections(template)
        lines = ["Section Headings:"]
        for title in headings:
            lines.append(title)
        return "\n".join(lines)
    
    if section:
        headings, sections = parse_prompt_sections(template)
        # Try by number
        try:
            idx = int(section) - 1
            # Skip the first section (title section) and adjust index
            if 0 <= idx < len(headings):
                return sections[idx + 1]  # +1 to skip the title section
        except Exception:
            pass
        # Try by keyword
        section_lower = section.strip().lower()
        for i, heading in enumerate(headings):
            if section_lower in heading.lower():
                return sections[i + 1]  # +1 to skip the title section
        return f"Section '{section}' not found."
    
    return template


# =============================================================================
# MCP Prompts (for prompts/list exposure)
# =============================================================================

@mcp.prompt("prompt_template_full")
def prompt_template_full_prompt() -> str:
    """Return the full canonical prompt template."""
    return read_prompt_template(PROMPT_TEMPLATE_PATH)

@mcp.prompt("prompt_template_headings")
def prompt_template_headings_prompt() -> str:
    """Return compact list of section headings."""
    template = read_prompt_template(PROMPT_TEMPLATE_PATH)
    headings, _ = parse_prompt_sections(template)
    lines = ["Section Headings:"]
    for idx, title in enumerate(headings, 1):
        lines.append(f"{idx}. {title}")
    return "\n".join(lines)

@mcp.prompt("prompt_template_section")
def prompt_template_section_prompt(section: Optional[str] = None) -> str:
    """Return a specific prompt template section by number or keyword."""
    if not section:
        template = read_prompt_template(PROMPT_TEMPLATE_PATH)
        headings, _ = parse_prompt_sections(template)
        lines = ["[HELP] Missing 'section' argument."]
        lines.append("Specify a section number or keyword.")
        lines.append("Examples: 1 | overview | tool map | usage")
        lines.append("")
        lines.append("Available sections:")
        for idx, title in enumerate(headings, 1):
            lines.append(f"{idx}. {title}")
        return "\n".join(lines)
    
    template = read_prompt_template(PROMPT_TEMPLATE_PATH)
    headings, sections = parse_prompt_sections(template)
    
    # Try by number
    try:
        idx = int(section) - 1
        if 0 <= idx < len(headings):
            return sections[idx + 1]  # +1 to skip the title section
    except Exception:
        pass
    
    # Try by keyword
    section_lower = section.strip().lower()
    for i, heading in enumerate(headings):
        if section_lower in heading.lower():
            return sections[i + 1]  # +1 to skip the title section
    
    return f"Section '{section}' not found."


# =============================================================================
# Server execution
# =============================================================================

def validate_config(transport_type: str, host: str, port: int) -> None:
    """Validate server configuration"""
    if transport_type not in ["stdio", "streamable-http"]:
        raise ValueError(f"Invalid transport type: {transport_type}")
    
    if transport_type == "streamable-http":
        # Host validation
        if not host:
            raise ValueError("Host is required for streamable-http transport")
        
        # Port validation
        if not (1 <= port <= 65535):
            raise ValueError(f"Port must be between 1 and 65535, got: {port}")
        
        logger.info(f"Configuration validated for streamable-http: {host}:{port}")
    else:
        logger.info("Configuration validated for stdio transport")


def main(argv: Optional[list] = None) -> None:
    """Main execution function"""
    parser = argparse.ArgumentParser(
        prog="mcp-postgresql-ops", 
        description="MCP PostgreSQL Operations Server"
    )
    parser.add_argument(
        "--log-level",
        dest="log_level",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Overrides env var if provided.",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    parser.add_argument(
        "--type",
        dest="transport_type",
        help="Transport type. Default: stdio",
        choices=["stdio", "streamable-http"],
        default="stdio"
    )
    parser.add_argument(
        "--host",
        dest="host",
        help="Host address for streamable-http transport. Default: 127.0.0.1",
        default=None
    )
    parser.add_argument(
        "--port",
        dest="port",
        type=int,
        help="Port number for streamable-http transport. Default: 8080",
        default=None
    )
    
    try:
        args = parser.parse_args(argv)
        
        # Determine log level: CLI arg > environment variable > default
        log_level = args.log_level or os.getenv("MCP_LOG_LEVEL", "INFO")
        
        # Set logging level
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {log_level}')
        
        logger.setLevel(numeric_level)
        logging.getLogger().setLevel(numeric_level)
        
        # Reduce noise from external libraries at DEBUG level
        logging.getLogger("aiohttp.client").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        
        if args.log_level:
            logger.info("Log level set via CLI to %s", args.log_level)
        elif os.getenv("MCP_LOG_LEVEL"):
            logger.info("Log level set via environment variable to %s", log_level)
        else:
            logger.info("Using default log level: %s", log_level)

        # Priority: CLI arguments > environment variables > defaults
        transport_type = args.transport_type or os.getenv("FASTMCP_TYPE", "stdio")
        host = args.host or os.getenv("FASTMCP_HOST", "127.0.0.1") 
        port = args.port or int(os.getenv("FASTMCP_PORT", "8080"))
        
        # Debug logging for environment variables
        logger.debug(f"Environment variables - POSTGRES_HOST: {os.getenv('POSTGRES_HOST')}, POSTGRES_PORT: {os.getenv('POSTGRES_PORT')}")
        logger.debug(f"POSTGRES_CONFIG values: {POSTGRES_CONFIG}")
        
        # PostgreSQL connection information logging
        logger.info(f"PostgreSQL connection: {POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}")
        
        # Configuration validation
        validate_config(transport_type, host, port)
        
        # Execute based on transport mode
        if transport_type == "streamable-http":
            logger.info(f"Starting MCP PostgreSQL server with streamable-http transport on {host}:{port}")
            # os.environ["HOST"] = host
            # os.environ["PORT"] = str(port)
            # mcp.run(transport="streamable-http")
            mcp.run(transport="streamable-http", host=host, port=port)
        else:
            logger.info("Starting MCP PostgreSQL server with stdio transport")
            # mcp.run()
            mcp.run(transport='stdio')
            
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    """Entrypoint for MCP PostgreSQL Operations server.

    Supports optional CLI arguments while remaining backward-compatible 
    with stdio launcher expectations.
    """
    main()