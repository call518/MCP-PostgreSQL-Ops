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
    get_current_database_name,
    POSTGRES_CONFIG
)
from .version_compat import (
    get_postgresql_version,
    check_feature_availability,
    VersionAwareQueries
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
        
        # Get replication slots with version compatibility
        slots_query = await VersionAwareQueries.get_replication_slots_query()
        repl_slots = await execute_query(slots_query)
        
        # Get WAL receiver status with version compatibility
        receiver_query = await VersionAwareQueries.get_wal_receiver_query()
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
        pg_version = await get_postgresql_version()
        
        # Connection information (with password masking)
        conn_info = sanitize_connection_info()
        
        # Check extension status
        pg_stat_statements_exists = await check_extension_exists("pg_stat_statements")
        pg_stat_monitor_exists = await check_extension_exists("pg_stat_monitor")
        
        # Version compatibility features
        features = {
            'Modern Version (12+)': pg_version.is_modern,
            'Checkpointer Split (15+)': pg_version.has_checkpointer_split,
            'pg_stat_io View (16+)': pg_version.has_pg_stat_io,
            'Enhanced WAL Receiver (16+)': pg_version.has_enhanced_wal_receiver,
            'Replication Slot Stats (14+)': pg_version.has_replication_slot_stats,
            'Parallel Leader Tracking (14+)': pg_version.has_parallel_leader_tracking,
        }
        
        result = []
        result.append("=== PostgreSQL Server Information ===\n")
        result.append(f"Version: {version}")
        result.append(f"Parsed Version: PostgreSQL {pg_version}")
        result.append(f"Host: {conn_info['host']}")
        result.append(f"Port: {conn_info['port']}")
        result.append(f"Database: {conn_info['database']}")
        result.append(f"User: {conn_info['user']}")
        result.append("")
        
        result.append("=== Extension Status ===")
        result.append(f"pg_stat_statements: {'✓ Installed' if pg_stat_statements_exists else '✗ Not installed'}")
        result.append(f"pg_stat_monitor: {'✓ Installed' if pg_stat_monitor_exists else '✗ Not installed'}")
        result.append("")
        
        result.append("=== Version Compatibility Features ===")
        for feature, available in features.items():
            status = "✓ Available" if available else "✗ Not Available"
            result.append(f"{feature}: {status}")
        result.append("")
        
        # Add compatibility summary
        if pg_version.is_modern:
            if pg_version >= 16:
                result.append("🚀 Excellent: All MCP tools fully supported with latest features!")
            elif pg_version >= 14:
                result.append("✅ Great: Most advanced features available, consider upgrading to PG16+ for pg_stat_io")
            else:
                result.append("✅ Good: Core features supported, upgrade to PG14+ recommended for enhanced monitoring")
        else:
            result.append("⚠️  Limited: PostgreSQL 12+ required for full MCP tool support")
            
        return "\n".join(result)
        
    except Exception as e:
        logger.error(f"Failed to get server info: {e}")
        return f"Error retrieving server information: {str(e)}"


@mcp.tool()
async def get_current_database_info(database_name: str = None) -> str:
    """
    [Tool Purpose]: Get information about the current database connection
    
    [Exact Functionality]:
    - Show the name of the currently connected database
    - Display database-specific information like encoding, locale, and size
    - Provide connection context for clarity in multi-database environments
    
    [Required Use Cases]:
    - When user asks "what database am I connected to?", "current database", etc.
    - When clarifying database context for analysis operations
    - When troubleshooting connection issues or confirming target database
    
    [Strictly Prohibited Use Cases]:
    - Requests for database structure changes or creation/deletion
    - Requests for user authentication or permission changes
    - Requests for configuration modifications
    
    Args:
        database_name: Target database to get info for (uses default connection if omitted)
    
    Returns:
        Current database name and related information for connection clarity
    """
    try:
        # Get current database name
        current_db = await get_current_database_name(database_name)
        
        # Get detailed database information
        query = """
        SELECT 
            datname as database_name,
            pg_encoding_to_char(encoding) as encoding,
            datcollate as collate,
            datctype as ctype,
            pg_size_pretty(pg_database_size(datname)) as database_size,
            pg_database_size(datname) as size_bytes,
            datconnlimit as connection_limit,
            CASE 
                WHEN datconnlimit = -1 THEN 'Unlimited'
                ELSE datconnlimit::text
            END as connection_limit_display
        FROM pg_database 
        WHERE datname = $1
        """
        
        db_info = await execute_query(query, [current_db], database=database_name)
        
        if not db_info:
            return f"Database information not found for: {current_db}"
        
        info = db_info[0]
        
        result = []
        result.append("=== Current Database Information ===\n")
        result.append(f"Connected Database: {info['database_name']}")
        result.append(f"Database Size: {info['database_size']}")
        result.append(f"Character Encoding: {info['encoding']}")
        result.append(f"LC_COLLATE: {info['collate']}")
        result.append(f"LC_CTYPE: {info['ctype']}")
        result.append(f"Connection Limit: {info['connection_limit_display']}")
        result.append("")
        
        # Add context note
        result.append("💡 This is the database used for analysis operations when no specific database is specified.")
        
        return "\n".join(result)
        
    except Exception as e:
        logger.error(f"Failed to get current database info: {e}")
        return f"Error retrieving current database information: {str(e)}"


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
async def get_table_schema_info(database_name: str, table_name: str = None, schema_name: str = "public") -> str:
    """
    [Tool Purpose]: Retrieve detailed schema information for specific table or all tables in a database
    
    [Exact Functionality]:
    - Retrieve detailed column information including data types, constraints, defaults
    - Display primary keys, foreign keys, indexes, and other table constraints
    - Show table-level metadata such as size, row count estimates
    
    [Required Use Cases]:
    - When user requests "table schema", "column info", "table structure", etc.
    - When detailed table design information is needed for development
    - When analyzing database structure and relationships
    
    [Strictly Prohibited Use Cases]:
    - Requests for actual data inside tables
    - Requests for table structure changes or DDL operations
    - Requests for performance statistics (use other tools for that)
    
    Args:
        database_name: Database name to query (REQUIRED - specify which database to analyze)
        table_name: Specific table name to analyze (if None, shows all tables)
        schema_name: Schema name to search in (default: "public")
    
    Returns:
        Detailed table schema information including columns, constraints, and metadata
    """
    try:
        if table_name:
            # Specific table schema information
            query = """
            WITH table_info AS (
                SELECT 
                    t.table_schema,
                    t.table_name,
                    t.table_type,
                    pg_size_pretty(pg_total_relation_size(quote_ident(t.table_schema)||'.'||quote_ident(t.table_name))) as table_size,
                    pg_stat_get_tuples_inserted(c.oid) + pg_stat_get_tuples_updated(c.oid) + pg_stat_get_tuples_deleted(c.oid) as total_writes,
                    pg_stat_get_live_tuples(c.oid) as estimated_rows
                FROM information_schema.tables t
                LEFT JOIN pg_class c ON c.relname = t.table_name
                LEFT JOIN pg_namespace n ON n.nspname = t.table_schema AND n.oid = c.relnamespace
                WHERE t.table_name = $1 AND t.table_schema = $2
            ),
            column_info AS (
                SELECT 
                    c.column_name,
                    c.ordinal_position,
                    c.data_type,
                    c.character_maximum_length,
                    c.numeric_precision,
                    c.numeric_scale,
                    c.is_nullable,
                    c.column_default,
                    CASE 
                        WHEN pk.column_name IS NOT NULL THEN 'PRIMARY KEY'
                        WHEN fk.column_name IS NOT NULL THEN 'FOREIGN KEY'
                        ELSE ''
                    END as key_type,
                    fk.referenced_table_name,
                    fk.referenced_column_name
                FROM information_schema.columns c
                LEFT JOIN (
                    SELECT kcu.column_name, kcu.table_name, kcu.table_schema
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                        AND tc.table_name = $3 AND tc.table_schema = $4
                ) pk ON c.column_name = pk.column_name 
                    AND c.table_name = pk.table_name 
                    AND c.table_schema = pk.table_schema
                LEFT JOIN (
                    SELECT 
                        kcu.column_name, 
                        kcu.table_name, 
                        kcu.table_schema,
                        ccu.table_name AS referenced_table_name,
                        ccu.column_name AS referenced_column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage ccu 
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_name = $5 AND tc.table_schema = $6
                ) fk ON c.column_name = fk.column_name 
                    AND c.table_name = fk.table_name 
                    AND c.table_schema = fk.table_schema
                WHERE c.table_name = $7 AND c.table_schema = $8
                ORDER BY c.ordinal_position
            ),
            constraint_info AS (
                SELECT 
                    tc.constraint_name,
                    tc.constraint_type,
                    string_agg(kcu.column_name, ', ' ORDER BY kcu.ordinal_position) as columns,
                    CASE 
                        WHEN tc.constraint_type = 'FOREIGN KEY' THEN
                            ccu.table_name || '(' || ccu.column_name || ')'
                        ELSE ''
                    END as references
                FROM information_schema.table_constraints tc
                LEFT JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                LEFT JOIN information_schema.constraint_column_usage ccu 
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.table_name = $9 AND tc.table_schema = $10
                GROUP BY tc.constraint_name, tc.constraint_type, ccu.table_name, ccu.column_name
                ORDER BY tc.constraint_type, tc.constraint_name
            ),
            index_info AS (
                SELECT 
                    i.indexname as index_name,
                    i.indexdef as index_definition,
                    CASE WHEN idx.indisunique THEN 'UNIQUE' ELSE 'REGULAR' END as index_type
                FROM pg_indexes i
                JOIN pg_class c ON c.relname = i.indexname
                JOIN pg_index idx ON idx.indexrelid = c.oid
                WHERE i.tablename = $11 AND i.schemaname = $12
                ORDER BY i.indexname
            )
            SELECT * FROM (
                SELECT 
                    'TABLE_INFO' as section,
                    ti.table_schema || '.' || ti.table_name as name,
                    ti.table_type as type,
                    ti.table_size as size,
                    COALESCE(ti.estimated_rows::text, 'N/A') as rows,
                    COALESCE(ti.total_writes::text, 'N/A') as writes,
                    '' as extra1,
                    '' as extra2,
                    '' as extra3,
                    1 as sort_order
                FROM table_info ti
                
                UNION ALL
                
                SELECT 
                    'COLUMN' as section,
                    ci.column_name as name,
                    ci.data_type as type,
                    COALESCE(
                        CASE 
                            WHEN ci.character_maximum_length IS NOT NULL THEN '(' || ci.character_maximum_length || ')'
                            WHEN ci.numeric_precision IS NOT NULL AND ci.numeric_scale IS NOT NULL THEN '(' || ci.numeric_precision || ',' || ci.numeric_scale || ')'
                            WHEN ci.numeric_precision IS NOT NULL THEN '(' || ci.numeric_precision || ')'
                            ELSE ''
                        END, ''
                    ) as size,
                    ci.is_nullable as rows,
                    COALESCE(ci.column_default, '') as writes,
                    ci.key_type as extra1,
                    COALESCE(ci.referenced_table_name, '') as extra2,
                    COALESCE(ci.referenced_column_name, '') as extra3,
                    2 as sort_order
                FROM column_info ci
                
                UNION ALL
                
                SELECT 
                    'CONSTRAINT' as section,
                    co.constraint_name as name,
                    co.constraint_type as type,
                    co.columns as size,
                    co.references as rows,
                    '' as writes,
                    '' as extra1,
                    '' as extra2,
                    '' as extra3,
                    3 as sort_order
                FROM constraint_info co
                
                UNION ALL
                
                SELECT 
                    'INDEX' as section,
                    idx.index_name as name,
                    idx.index_type as type,
                    idx.index_definition as size,
                    '' as rows,
                    '' as writes,
                    '' as extra1,
                    '' as extra2,
                    '' as extra3,
                    4 as sort_order
                FROM index_info idx
            ) combined_results
            ORDER BY sort_order, name
            """
            
            # Parameters: table_name, schema_name repeated 6 times for different subqueries
            params = [table_name, schema_name] * 6  # 12 parameters total
            results = await execute_query(query, params, database=database_name)
            title = f"Schema Information for {schema_name}.{table_name}"
            if database_name:
                title += f" (Database: {database_name})"
        else:
            # All tables schema overview
            query = """
            WITH table_columns AS (
                SELECT 
                    t.table_schema,
                    t.table_name,
                    t.table_type,
                    COUNT(c.column_name) as column_count,
                    string_agg(
                        CASE WHEN pk.column_name IS NOT NULL THEN c.column_name || ' (PK)' 
                             ELSE c.column_name 
                        END, 
                        ', ' ORDER BY c.ordinal_position
                    ) as columns,
                    pg_size_pretty(COALESCE(pg_total_relation_size(quote_ident(t.table_schema)||'.'||quote_ident(t.table_name)), 0)) as table_size
                FROM information_schema.tables t
                LEFT JOIN information_schema.columns c 
                    ON t.table_name = c.table_name AND t.table_schema = c.table_schema
                LEFT JOIN (
                    SELECT kcu.column_name, kcu.table_name, kcu.table_schema
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                ) pk ON c.column_name = pk.column_name 
                    AND c.table_name = pk.table_name 
                    AND c.table_schema = pk.table_schema
                WHERE t.table_schema = $1 
                    AND t.table_type IN ('BASE TABLE', 'VIEW')
                GROUP BY t.table_schema, t.table_name, t.table_type
                ORDER BY t.table_schema, t.table_name
            )
            SELECT 
                table_schema || '.' || table_name as table_name,
                table_type,
                column_count,
                table_size,
                LEFT(columns, 100) || CASE WHEN LENGTH(columns) > 100 THEN '...' ELSE '' END as columns_preview
            FROM table_columns
            """
            
            results = await execute_query(query, [schema_name], database=database_name)
            title = f"Schema Overview for {schema_name} schema"
            if database_name:
                title += f" (Database: {database_name})"
            
        return format_table_data(results, title)
        
    except Exception as e:
        logger.error(f"Failed to get table schema info: {e}")
        return f"Error retrieving table schema information: {str(e)}"


@mcp.tool()
async def get_database_schema_info(database_name: str, schema_name: str = None) -> str:
    """
    [Tool Purpose]: Retrieve detailed information about database schemas (namespaces) and their contents
    
    [Exact Functionality]:
    - Show all schemas in a database with their owners and permissions
    - Display schema-level statistics including table count and total size
    - List all objects (tables, views, functions) within specific schema
    - Show schema access privileges and usage patterns
    
    [Required Use Cases]:
    - When user requests "database schema info", "schema overview", "namespace structure", etc.
    - When analyzing database organization and schema-level permissions
    - When exploring multi-schema database architecture
    
    [Strictly Prohibited Use Cases]:
    - Requests for actual data inside tables
    - Requests for schema structure changes or DDL operations
    - Requests for individual table details (use get_table_schema_info for that)
    
    Args:
        database_name: Database name to query (REQUIRED - specify which database to analyze)
        schema_name: Specific schema name to analyze (if None, shows all schemas)
    
    Returns:
        Detailed database schema information including objects, sizes, and permissions
    """
    try:
        if schema_name:
            # Specific schema detailed information
            query = """
            WITH schema_objects AS (
                SELECT 
                    n.nspname as schema_name,
                    n.nspowner::regrole::text as schema_owner,
                    obj_description(n.oid, 'pg_namespace') as schema_comment,
                    array_to_string(n.nspacl, ', ') as access_privileges
                FROM pg_namespace n
                WHERE n.nspname = $1
                  AND n.nspname NOT IN ('information_schema')
                  AND n.nspname NOT LIKE 'pg_%'
            ),
            schema_tables AS (
                SELECT 
                    schemaname,
                    COUNT(*) as table_count,
                    pg_size_pretty(SUM(pg_total_relation_size(schemaname||'.'||tablename))) as total_size
                FROM pg_tables 
                WHERE schemaname = $1
                GROUP BY schemaname
            ),
            schema_views AS (
                SELECT 
                    schemaname,
                    COUNT(*) as view_count
                FROM pg_views 
                WHERE schemaname = $1
                GROUP BY schemaname
            ),
            schema_functions AS (
                SELECT 
                    n.nspname as schemaname,
                    COUNT(*) as function_count
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = $1
                GROUP BY n.nspname
            ),
            table_details AS (
                SELECT 
                    'TABLE' as object_type,
                    schemaname || '.' || tablename as object_name,
                    tableowner::text as object_owner,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as object_size,
                    'Base table' as object_description
                FROM pg_tables 
                WHERE schemaname = $1
                
                UNION ALL
                
                SELECT 
                    'VIEW' as object_type,
                    schemaname || '.' || viewname as object_name,
                    viewowner::text as object_owner,
                    'N/A' as object_size,
                    'View definition' as object_description
                FROM pg_views 
                WHERE schemaname = $1
                
                UNION ALL
                
                SELECT 
                    'FUNCTION' as object_type,
                    n.nspname || '.' || p.proname as object_name,
                    p.proowner::regrole::text as object_owner,
                    'N/A' as object_size,
                    'Function/Procedure' as object_description
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = $1
                ORDER BY object_type, object_name
            )
            SELECT * FROM (
                SELECT 
                    'SCHEMA_INFO' as section,
                    'Schema: ' || so.schema_name as name,
                    'Owner: ' || so.schema_owner as type,
                    'Tables: ' || COALESCE(st.table_count::text, '0') as size,
                    'Views: ' || COALESCE(sv.view_count::text, '0') as rows,
                    'Functions: ' || COALESCE(sf.function_count::text, '0') as writes,
                    'Total Size: ' || COALESCE(st.total_size, '0 bytes') as extra1,
                    'Comment: ' || COALESCE(so.schema_comment, 'No comment') as extra2,
                    'Privileges: ' || COALESCE(so.access_privileges, 'Default') as extra3,
                    1 as sort_order
                FROM schema_objects so
                LEFT JOIN schema_tables st ON so.schema_name = st.schemaname
                LEFT JOIN schema_views sv ON so.schema_name = sv.schemaname
                LEFT JOIN schema_functions sf ON so.schema_name = sf.schemaname
                
                UNION ALL
                
                SELECT 
                    'OBJECT' as section,
                    td.object_name as name,
                    td.object_type as type,
                    td.object_size as size,
                    td.object_owner as rows,
                    '' as writes,
                    td.object_description as extra1,
                    '' as extra2,
                    '' as extra3,
                    2 as sort_order
                FROM table_details td
            ) combined_results
            ORDER BY sort_order, name
            """
            
            params = [schema_name]  # Only 1 parameter needed - schema_name is reused in all WHERE clauses
            results = await execute_query(query, params, database=database_name)
            title = f"Schema Details for '{schema_name}'"
            if database_name:
                title += f" (Database: {database_name})"
        else:
            # All schemas overview
            query = """
            WITH schema_stats AS (
                SELECT 
                    n.nspname as schema_name,
                    n.nspowner::regrole::text as schema_owner,
                    obj_description(n.oid, 'pg_namespace') as schema_comment,
                    COALESCE(t.table_count, 0) as table_count,
                    COALESCE(v.view_count, 0) as view_count,
                    COALESCE(f.function_count, 0) as function_count,
                    COALESCE(t.total_size_bytes, 0) as total_size_bytes,
                    pg_size_pretty(COALESCE(t.total_size_bytes, 0)) as total_size
                FROM pg_namespace n
                LEFT JOIN (
                    SELECT 
                        schemaname,
                        COUNT(*) as table_count,
                        SUM(pg_total_relation_size(schemaname||'.'||tablename)) as total_size_bytes
                    FROM pg_tables 
                    GROUP BY schemaname
                ) t ON n.nspname = t.schemaname
                LEFT JOIN (
                    SELECT 
                        schemaname,
                        COUNT(*) as view_count
                    FROM pg_views 
                    GROUP BY schemaname
                ) v ON n.nspname = v.schemaname
                LEFT JOIN (
                    SELECT 
                        n2.nspname as schemaname,
                        COUNT(*) as function_count
                    FROM pg_proc p
                    JOIN pg_namespace n2 ON p.pronamespace = n2.oid
                    GROUP BY n2.nspname
                ) f ON n.nspname = f.schemaname
                WHERE n.nspname NOT IN ('information_schema')
                  AND n.nspname NOT LIKE 'pg_%'
                ORDER BY total_size_bytes DESC, schema_name
            )
            SELECT 
                schema_name,
                schema_owner,
                table_count,
                view_count,
                function_count,
                total_size,
                COALESCE(schema_comment, 'No description') as description
            FROM schema_stats
            """
            
            results = await execute_query(query, [], database=database_name)
            title = f"Database Schema Overview"
            if database_name:
                title += f" (Database: {database_name})"
            
        return format_table_data(results, title)
        
    except Exception as e:
        logger.error(f"Failed to get database schema info: {e}")
        return f"Error retrieving database schema information: {str(e)}"


@mcp.tool()
async def get_table_relationships(database_name: str, table_name: str = None, schema_name: str = "public", relationship_type: str = "all") -> str:
    """
    [Tool Purpose]: Analyze table relationships including foreign keys, dependencies, and inheritance
    
    [Exact Functionality]:
    - Show foreign key relationships (inbound and outbound)
    - Display view dependencies and table references
    - Analyze inheritance and partition relationships
    - Identify orphaned tables and relationship patterns
    
    [Required Use Cases]:
    - When user requests "table relationships", "foreign keys", "dependencies", etc.
    - When analyzing database schema design and data model
    - When planning data migration or schema changes
    
    [Strictly Prohibited Use Cases]:
    - Requests for actual data inside tables
    - Requests for relationship modifications or DDL operations
    - Requests for performance statistics (use other tools for that)
    
    Args:
        database_name: Database name to query (REQUIRED - specify which database to analyze)
        table_name: Specific table name to analyze (if None, shows database-wide relationship overview)
        schema_name: Schema name to search in (default: "public")
        relationship_type: Type of relationships to show ("all", "foreign_keys", "dependencies", "inheritance")
    
    Returns:
        Detailed relationship information including foreign keys, dependencies, and metadata
    """
    try:
        if table_name:
            # Specific table relationship analysis
            query = """
            WITH table_info AS (
                SELECT 
                    t.table_schema,
                    t.table_name,
                    t.table_type
                FROM information_schema.tables t
                WHERE t.table_name = $1 AND t.table_schema = $2
                  AND t.table_type IN ('BASE TABLE', 'VIEW')
            ),
            foreign_keys_out AS (
                SELECT 
                    tc.constraint_name,
                    tc.table_schema || '.' || tc.table_name as source_table,
                    kcu.column_name as source_column,
                    ccu.table_schema || '.' || ccu.table_name AS target_table,
                    ccu.column_name AS target_column,
                    rc.match_option,
                    rc.update_rule,
                    rc.delete_rule,
                    'OUTBOUND' as direction
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                JOIN information_schema.referential_constraints AS rc
                    ON tc.constraint_name = rc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_name = $1 AND tc.table_schema = $2
                ORDER BY tc.constraint_name, kcu.ordinal_position
            ),
            foreign_keys_in AS (
                SELECT 
                    tc.constraint_name,
                    tc.table_schema || '.' || tc.table_name as source_table,
                    kcu.column_name as source_column,
                    ccu.table_schema || '.' || ccu.table_name AS target_table,
                    ccu.column_name AS target_column,
                    rc.match_option,
                    rc.update_rule,
                    rc.delete_rule,
                    'INBOUND' as direction
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                JOIN information_schema.referential_constraints AS rc
                    ON tc.constraint_name = rc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND ccu.table_name = $1 AND ccu.table_schema = $2
                ORDER BY tc.constraint_name, kcu.ordinal_position
            ),
            view_dependencies AS (
                SELECT DISTINCT
                    v.view_schema || '.' || v.view_name as view_name,
                    'Depends on this table' as dependency_type
                FROM information_schema.view_table_usage v
                WHERE v.table_schema = $2 AND v.table_name = $1
            ),
            inheritance_info AS (
                SELECT 
                    schemaname || '.' || tablename as child_table,
                    schemaname || '.' || tablename as parent_table,
                    'INHERITS' as relationship_type
                FROM pg_tables pt
                JOIN pg_inherits i ON i.inhrelid = (pt.schemaname||'.'||pt.tablename)::regclass::oid
                JOIN pg_class pc ON i.inhparent = pc.oid
                JOIN pg_namespace pn ON pc.relnamespace = pn.oid
                WHERE (pt.tablename = $1 AND pt.schemaname = $2)
                   OR (pc.relname = $1 AND pn.nspname = $2)
            )
            SELECT * FROM (
                SELECT 
                    'TABLE_INFO' as section,
                    'Table: ' || ti.table_schema || '.' || ti.table_name as name,
                    'Type: ' || ti.table_type as type,
                    'Analysis target table' as size,
                    '' as rows,
                    '' as writes,
                    '' as extra1,
                    '' as extra2,
                    '' as extra3,
                    1 as sort_order
                FROM table_info ti
                
                UNION ALL
                
                SELECT 
                    'FK_OUTBOUND' as section,
                    'FK: ' || fko.constraint_name as name,
                    fko.direction as type,
                    fko.source_column || ' → ' || fko.target_table as size,
                    'Column: ' || fko.target_column as rows,
                    'Update: ' || fko.update_rule || ', Delete: ' || fko.delete_rule as writes,
                    '' as extra1,
                    '' as extra2,
                    '' as extra3,
                    2 as sort_order
                FROM foreign_keys_out fko
                
                UNION ALL
                
                SELECT 
                    'FK_INBOUND' as section,
                    'FK: ' || fki.constraint_name as name,
                    fki.direction as type,
                    fki.source_table || ' → ' || fki.source_column as size,
                    'Referencing Column: ' || fki.target_column as rows,
                    'Update: ' || fki.update_rule || ', Delete: ' || fki.delete_rule as writes,
                    '' as extra1,
                    '' as extra2,
                    '' as extra3,
                    3 as sort_order
                FROM foreign_keys_in fki
                
                UNION ALL
                
                SELECT 
                    'VIEW_DEPENDENCY' as section,
                    'View: ' || vd.view_name as name,
                    vd.dependency_type as type,
                    'View depends on this table' as size,
                    '' as rows,
                    '' as writes,
                    '' as extra1,
                    '' as extra2,
                    '' as extra3,
                    4 as sort_order
                FROM view_dependencies vd
                
                UNION ALL
                
                SELECT 
                    'INHERITANCE' as section,
                    'Relation: ' || ii.child_table as name,
                    ii.relationship_type as type,
                    ii.parent_table as size,
                    '' as rows,
                    '' as writes,
                    '' as extra1,
                    '' as extra2,
                    '' as extra3,
                    5 as sort_order
                FROM inheritance_info ii
            ) combined_results
            ORDER BY sort_order, name
            """
            
            params = [table_name, schema_name]  # Only 2 parameters needed - table_name and schema_name reused in all WHERE clauses
            results = await execute_query(query, params, database=database_name)
            title = f"Relationships for {schema_name}.{table_name}"
            if database_name:
                title += f" (Database: {database_name})"
        else:
            # Database-wide relationship overview
            query = """
            WITH relationship_stats AS (
                SELECT 
                    'Foreign Key Relationships' as category,
                    COUNT(*) as count,
                    'Total FK constraints in database' as description
                FROM information_schema.table_constraints 
                WHERE constraint_type = 'FOREIGN KEY'
            
                UNION ALL
                
                SELECT 
                    'Referenced Tables' as category,
                    COUNT(DISTINCT ccu.table_schema || '.' || ccu.table_name) as count,
                    'Tables being referenced by foreign keys' as description
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                
                UNION ALL
                
                SELECT 
                    'Referencing Tables' as category,
                    COUNT(DISTINCT tc.table_schema || '.' || tc.table_name) as count,
                    'Tables that reference other tables' as description
                FROM information_schema.table_constraints AS tc 
                WHERE tc.constraint_type = 'FOREIGN KEY'
                
                UNION ALL
                
                SELECT 
                    'Orphaned Tables' as category,
                    COUNT(*) as count,
                    'Tables with no foreign key relationships' as description
                FROM information_schema.tables t
                WHERE t.table_type = 'BASE TABLE'
                  AND t.table_schema NOT IN ('information_schema', 'pg_catalog')
                  AND t.table_schema NOT LIKE 'pg_%'
                  AND NOT EXISTS (
                      SELECT 1 FROM information_schema.table_constraints tc
                      WHERE tc.table_name = t.table_name 
                        AND tc.table_schema = t.table_schema
                        AND tc.constraint_type = 'FOREIGN KEY'
                  )
                  AND NOT EXISTS (
                      SELECT 1 FROM information_schema.constraint_column_usage ccu
                      WHERE ccu.table_name = t.table_name 
                        AND ccu.table_schema = t.table_schema
                  )
            ),
            top_referenced_tables AS (
                SELECT 
                    ccu.table_schema || '.' || ccu.table_name as table_name,
                    COUNT(*) as reference_count,
                    'Most referenced table' as category
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                GROUP BY ccu.table_schema, ccu.table_name
                ORDER BY COUNT(*) DESC
                LIMIT 5
            ),
            relationship_details AS (
                SELECT 
                    tc.table_schema || '.' || tc.table_name as referencing_table,
                    kcu.column_name as referencing_column,
                    ccu.table_schema || '.' || ccu.table_name AS referenced_table,
                    ccu.column_name AS referenced_column,
                    rc.update_rule,
                    rc.delete_rule,
                    tc.constraint_name
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                JOIN information_schema.referential_constraints AS rc
                    ON tc.constraint_name = rc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                ORDER BY tc.table_schema, tc.table_name, kcu.ordinal_position
            )
            SELECT * FROM (
                SELECT 
                    'STATISTICS' as section,
                    rs.category as name,
                    rs.count::text as type,
                    rs.description as size,
                    '' as rows,
                    '' as writes,
                    '' as extra1,
                    '' as extra2,
                    '' as extra3,
                    1 as sort_order
                FROM relationship_stats rs
                
                UNION ALL
                
                SELECT 
                    'TOP_REFERENCED' as section,
                    trt.table_name as name,
                    'Referenced ' || trt.reference_count || ' times' as type,
                    'High-traffic table in relationships' as size,
                    '' as rows,
                    '' as writes,
                    '' as extra1,
                    '' as extra2,
                    '' as extra3,
                    2 as sort_order
                FROM top_referenced_tables trt
                
                UNION ALL
                
                SELECT 
                    'RELATIONSHIP' as section,
                    rd.constraint_name as name,
                    rd.referencing_table || ' → ' || rd.referenced_table as type,
                    rd.referencing_column || ' → ' || rd.referenced_column as size,
                    'Update: ' || rd.update_rule as rows,
                    'Delete: ' || rd.delete_rule as writes,
                    '' as extra1,
                    '' as extra2,
                    '' as extra3,
                    3 as sort_order
                FROM relationship_details rd
            ) combined_results
            ORDER BY sort_order, name
            """
            
            results = await execute_query(query, [], database=database_name)
            title = f"Database Relationship Overview"
            if database_name:
                title += f" (Database: {database_name})"
            
        return format_table_data(results, title)
        
    except Exception as e:
        logger.error(f"Failed to get table relationships: {e}")
        return f"Error retrieving table relationships: {str(e)}"


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
async def get_table_bloat_analysis(database_name: str = None, schema_name: str = None, table_pattern: str = None, min_dead_tuples: int = 1, limit: int = 20) -> str:
    """
    [Tool Purpose]: Analyze table bloat based on dead tuple statistics and size information
    
    [Exact Functionality]:
    - Calculate bloat ratio based on dead tuples vs total tuples
    - Estimate bloat size in bytes and human-readable format
    - Show last VACUUM/AUTOVACUUM timestamps for maintenance tracking
    - Identify tables requiring VACUUM maintenance
    - Filter tables by name pattern using SQL LIKE or ILIKE matching
    - Sort results by bloat severity (dead tuple ratio and count)
    
    [Required Use Cases]:
    - When user requests "table bloat", "bloat analysis", "dead tuples", etc.
    - When identifying tables that need VACUUM maintenance
    - When investigating database storage efficiency and space usage
    - When troubleshooting performance issues related to table bloat
    - When analyzing specific table groups (e.g., tables with "user", "log", "temp" in names)
    
    [Strictly Prohibited Use Cases]:
    - Requests for automatic VACUUM execution
    - Requests for bloat removal or cleanup operations
    - Requests for table restructuring or data modification
    
    Args:
        database_name: Target database name (uses default database from POSTGRES_DB env var if omitted)
        schema_name: Schema to analyze (analyzes all user schemas if omitted)
        table_pattern: Table name pattern to filter (SQL LIKE pattern, e.g., 'user%', '%log%', 'temp_*')
        min_dead_tuples: Minimum dead tuples to include in results (default: 1, shows all tables with any bloat)
        limit: Maximum number of results to return (1-100, default: 20)
    
    Returns:
        Table bloat analysis with bloat ratios, sizes, and maintenance recommendations
    """
    try:
        # Validate and constrain limit
        limit = max(1, min(limit, 100))
        
        # Build WHERE clause based on parameters
        where_conditions = []
        params = []
        param_index = 1
        
        # Schema filtering
        if schema_name:
            where_conditions.append(f"schemaname = ${param_index}")
            params.append(schema_name)
            param_index += 1
        else:
            # Exclude system schemas
            where_conditions.append("schemaname NOT IN ('information_schema', 'pg_catalog')")
            where_conditions.append("schemaname NOT LIKE 'pg_%'")
        
        # Table pattern filtering
        if table_pattern:
            where_conditions.append(f"relname ILIKE ${param_index}")
            params.append(table_pattern)
            param_index += 1
        
        # Dead tuples filtering
        where_conditions.append(f"n_dead_tup >= ${param_index}")
        params.append(min_dead_tuples)
        param_index += 1
        
        # Add LIMIT parameter
        params.append(limit)
        
        # Combine WHERE conditions
        schema_filter = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        query = f"""
        SELECT 
            schemaname as schema_name,
            relname as table_name,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) as total_size,
            pg_size_pretty(pg_relation_size(schemaname||'.'||relname)) as table_size,
            n_dead_tup as dead_tuples,
            n_live_tup as live_tuples,
            CASE 
                WHEN (n_live_tup + n_dead_tup) = 0 THEN 0
                ELSE round(100.0 * n_dead_tup / (n_live_tup + n_dead_tup), 2)
            END as bloat_ratio_percent,
            pg_size_pretty(
                (pg_relation_size(schemaname||'.'||relname) * 
                CASE 
                    WHEN (n_live_tup + n_dead_tup) = 0 THEN 0
                    ELSE n_dead_tup::float / (n_live_tup + n_dead_tup)
                END)::bigint
            ) as estimated_bloat_size,
            last_vacuum,
            last_autovacuum,
            CASE 
                WHEN last_vacuum IS NULL AND last_autovacuum IS NULL THEN 'Never vacuumed'
                WHEN last_vacuum IS NULL THEN 'Manual vacuum needed'
                WHEN last_autovacuum IS NULL THEN 'Auto vacuum available'
                WHEN last_vacuum > last_autovacuum THEN 'Recently manual vacuumed'
                ELSE 'Recently auto vacuumed'
            END as vacuum_status
        FROM pg_stat_user_tables
        {schema_filter}
        ORDER BY 
            CASE 
                WHEN (n_live_tup + n_dead_tup) = 0 THEN 0
                ELSE 100.0 * n_dead_tup / (n_live_tup + n_dead_tup)
            END DESC, 
            n_dead_tup DESC
        LIMIT ${len(params)}
        """
        
        bloat_stats = await execute_query(query, params, database=database_name)
        
        # Get actual database name for clarity
        if not database_name:
            actual_db_name = await get_current_database_name(database_name)
        else:
            actual_db_name = database_name
        
        if not bloat_stats:
            # Build descriptive error message
            conditions = []
            if schema_name:
                conditions.append(f"schema '{schema_name}'")
            else:
                conditions.append("any user schema")
            if table_pattern:
                conditions.append(f"table pattern '{table_pattern}'")
            
            condition_str = " and ".join(conditions)
            return f"No tables found with significant bloat (>= {min_dead_tuples} dead tuples) in {condition_str} (Database: {actual_db_name})"
        
        # Build title based on parameters - ALWAYS include actual database name
        title_parts = []
        if schema_name:
            title_parts.append(f"Schema: {schema_name}")
        else:
            title_parts.append("All Schemas")
        
        if table_pattern:
            title_parts.append(f"Pattern: '{table_pattern}'")
        
        title_parts.append(f"Min Dead Tuples: {min_dead_tuples}")
        
        # Always include database name in title for clarity
        title = f"Table Bloat Analysis (Database: {actual_db_name}, {', '.join(title_parts)})"
            
        return format_table_data(bloat_stats, title)
        
    except Exception as e:
        logger.error(f"Failed to analyze table bloat: {e}")
        return f"Error analyzing table bloat: {str(e)}"


@mcp.tool()
async def get_database_bloat_overview(database_name: str = None, limit: int = 20) -> str:
    """
    [Tool Purpose]: Provide database-wide bloat overview and summary statistics
    
    [Exact Functionality]:
    - Summarize bloat statistics across all schemas
    - Identify schemas and tables with highest bloat ratios
    - Calculate total estimated bloat size per schema
    - Show aggregate dead tuple counts and maintenance status
    
    [Required Use Cases]:
    - When user requests "database bloat overview", "bloat summary", etc.
    - When getting high-level view of database storage efficiency
    - When planning database maintenance activities
    - When investigating overall database performance issues
    
    [Strictly Prohibited Use Cases]:
    - Requests for automatic maintenance operations
    - Requests for bloat cleanup or removal
    - Requests for schema or database restructuring
    
    Args:
        database_name: Target database name (uses default database from POSTGRES_DB env var if omitted)
        limit: Maximum number of schemas to show (1-50, default: 10)
    
    Returns:
        Database-wide bloat summary by schema with totals and recommendations
    """
    try:
        # Validate and constrain limit
        limit = max(1, min(limit, 50))
        
        query = """
        SELECT 
            schemaname as schema_name,
            COUNT(*) as total_tables,
            COUNT(CASE WHEN n_dead_tup > 0 THEN 1 END) as tables_with_bloat,
            SUM(n_dead_tup) as total_dead_tuples,
            SUM(n_live_tup) as total_live_tuples,
            CASE 
                WHEN SUM(n_live_tup + n_dead_tup) = 0 THEN 0
                ELSE round(100.0 * SUM(n_dead_tup) / SUM(n_live_tup + n_dead_tup), 2)
            END as overall_bloat_percent,
            pg_size_pretty(
                SUM(
                    pg_relation_size(schemaname||'.'||relname) * 
                    CASE 
                        WHEN (n_live_tup + n_dead_tup) = 0 THEN 0
                        ELSE n_dead_tup::float / (n_live_tup + n_dead_tup)
                    END
                )::bigint
            ) as estimated_total_bloat,
            pg_size_pretty(SUM(pg_total_relation_size(schemaname||'.'||relname))::bigint) as total_schema_size,
            COUNT(CASE WHEN last_vacuum IS NULL AND last_autovacuum IS NULL THEN 1 END) as never_vacuumed_tables
        FROM pg_stat_user_tables
        GROUP BY schemaname
        HAVING SUM(n_dead_tup) > 0
        ORDER BY 
            CASE 
                WHEN SUM(n_live_tup + n_dead_tup) = 0 THEN 0
                ELSE 100.0 * SUM(n_dead_tup) / SUM(n_live_tup + n_dead_tup)
            END DESC
        LIMIT $1
        """
        
        bloat_overview = await execute_query(query, [limit], database=database_name)
        
        # Get actual database name for clarity
        if not database_name:
            actual_db_name = await get_current_database_name(database_name)
        else:
            actual_db_name = database_name
        
        if not bloat_overview:
            return f"No schemas found with table bloat (Database: {actual_db_name})"
        
        # Always include actual database name in title for clarity
        title = f"Database Bloat Overview (Database: {actual_db_name})"
            
        return format_table_data(bloat_overview, title)
        
    except Exception as e:
        logger.error(f"Failed to get database bloat overview: {e}")
        return f"Error getting database bloat overview: {str(e)}"


@mcp.tool()
async def get_autovacuum_status(database_name: str = None, schema_name: str = None, table_pattern: str = None, limit: int = 50) -> str:
    """
    [Tool Purpose]: Analyze autovacuum configuration and current maintenance status for tables
    
    [Exact Functionality]:
    - Analyze autovacuum trigger conditions based on dead tuple thresholds
    - Calculate current dead tuple ratios vs autovacuum trigger points
    - Show autovacuum configuration settings per table
    - Identify tables requiring immediate autovacuum attention
    - Estimate next autovacuum execution likelihood
    
    [Required Use Cases]:
    - When user requests "autovacuum status", "autovacuum configuration", "vacuum trigger analysis", etc.
    - When planning autovacuum optimization and tuning
    - When troubleshooting autovacuum performance issues
    - When identifying tables with autovacuum problems
    
    [Strictly Prohibited Use Cases]:
    - Requests for autovacuum configuration changes
    - Requests for manual VACUUM execution
    - Requests for autovacuum process restart or control
    
    Args:
        database_name: Target database name (uses default database from POSTGRES_DB env var if omitted)
        schema_name: Schema to analyze (analyzes all user schemas if omitted)
        table_pattern: Table name pattern to filter (SQL LIKE pattern, e.g., 'user%', '%log%', 'temp_*')
        limit: Maximum number of tables to analyze (1-100, default: 50)
    
    Returns:
        Autovacuum configuration status with trigger analysis and maintenance recommendations
    """
    try:
        # Validate and constrain limit
        limit = max(1, min(limit, 100))
        
        # Build WHERE clause based on parameters
        where_conditions = []
        params = []
        param_index = 1
        
        # Schema filtering
        if schema_name:
            where_conditions.append(f"schemaname = ${param_index}")
            params.append(schema_name)
            param_index += 1
        else:
            # Exclude system schemas
            where_conditions.append("schemaname NOT IN ('information_schema', 'pg_catalog')")
            where_conditions.append("schemaname NOT LIKE 'pg_%'")
        
        # Table pattern filtering
        if table_pattern:
            where_conditions.append(f"relname ILIKE ${param_index}")
            params.append(table_pattern)
            param_index += 1
        
        # Add LIMIT parameter
        params.append(limit)
        
        # Combine WHERE conditions
        where_filter = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        query = f"""
        SELECT 
            schemaname as schema_name,
            relname as table_name,
            n_dead_tup as current_dead_tuples,
            n_live_tup as live_tuples,
            CASE 
                WHEN n_live_tup + n_dead_tup = 0 THEN 0
                ELSE round(100.0 * n_dead_tup / (n_live_tup + n_dead_tup), 2)
            END as dead_tuple_ratio_percent,
            -- Standard autovacuum thresholds (default: 20% + 50 tuples)
            round(0.2 * n_live_tup + 50) as autovacuum_threshold,
            -- Calculate how close we are to autovacuum trigger
            CASE 
                WHEN n_dead_tup >= (0.2 * n_live_tup + 50) THEN 'NEEDS AUTOVACUUM NOW'
                WHEN n_dead_tup >= (0.15 * n_live_tup + 40) THEN 'APPROACHING THRESHOLD'  
                WHEN n_dead_tup >= (0.1 * n_live_tup + 25) THEN 'MONITOR CLOSELY'
                ELSE 'OK'
            END as autovacuum_urgency,
            -- Estimate percentage to autovacuum trigger
            CASE 
                WHEN (0.2 * n_live_tup + 50) = 0 THEN 0
                ELSE round(100.0 * n_dead_tup / (0.2 * n_live_tup + 50), 1)
            END as threshold_percentage,
            last_autovacuum,
            CASE 
                WHEN last_autovacuum IS NOT NULL 
                THEN extract(hours from now() - last_autovacuum)::int
                ELSE NULL 
            END as hours_since_autovacuum,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) as table_size
        FROM pg_stat_user_tables
        {where_filter}
        ORDER BY 
            CASE 
                WHEN n_dead_tup >= (0.2 * n_live_tup + 50) THEN 1
                WHEN n_dead_tup >= (0.15 * n_live_tup + 40) THEN 2
                WHEN n_dead_tup >= (0.1 * n_live_tup + 25) THEN 3
                ELSE 4
            END,
            n_dead_tup DESC
        LIMIT ${len(params)}
        """
        
        autovacuum_status = await execute_query(query, params, database=database_name)
        
        # Get actual database name for clarity
        if not database_name:
            actual_db_name = await get_current_database_name(database_name)
        else:
            actual_db_name = database_name
        
        if not autovacuum_status:
            # Build descriptive message
            conditions = []
            if schema_name:
                conditions.append(f"schema '{schema_name}'")
            else:
                conditions.append("any user schema")
            if table_pattern:
                conditions.append(f"table pattern '{table_pattern}'")
            
            condition_str = " and ".join(conditions)
            return f"No tables found for autovacuum analysis in {condition_str} (Database: {actual_db_name})"
        
        # Build title based on parameters - ALWAYS include actual database name
        title_parts = []
        if schema_name:
            title_parts.append(f"Schema: {schema_name}")
        else:
            title_parts.append("All Schemas")
        
        if table_pattern:
            title_parts.append(f"Pattern: '{table_pattern}'")
        
        # Always include database name in title for clarity
        title = f"Autovacuum Status Analysis (Database: {actual_db_name}, {', '.join(title_parts)})"
            
        return format_table_data(autovacuum_status, title)
        
    except Exception as e:
        logger.error(f"Failed to analyze autovacuum status: {e}")
        return f"Error analyzing autovacuum status: {str(e)}"


@mcp.tool()
async def get_autovacuum_activity(database_name: str = None, schema_name: str = None, hours_back: int = 24, limit: int = 50) -> str:
    """
    [Tool Purpose]: Monitor recent autovacuum and autoanalyze activity patterns and execution history
    
    [Exact Functionality]:
    - Track recent autovacuum and autoanalyze execution patterns
    - Analyze autovacuum frequency and timing intervals
    - Show tables with most/least autovacuum activity
    - Calculate average time between autovacuum executions
    - Identify tables with irregular autovacuum patterns
    
    [Required Use Cases]:
    - When user requests "autovacuum activity", "autovacuum history", "vacuum patterns", etc.
    - When monitoring autovacuum performance and effectiveness
    - When troubleshooting autovacuum scheduling issues
    - When analyzing autovacuum workload distribution
    
    [Strictly Prohibited Use Cases]:
    - Requests for autovacuum process control or restart
    - Requests for autovacuum configuration modifications
    - Requests for manual vacuum scheduling
    
    Args:
        database_name: Target database name (uses default database from POSTGRES_DB env var if omitted)
        schema_name: Schema to analyze (analyzes all user schemas if omitted)
        hours_back: Time period to analyze in hours (default: 24, max: 168 for 7 days)
        limit: Maximum number of tables to show (1-100, default: 50)
    
    Returns:
        Recent autovacuum activity analysis with patterns and timing statistics
    """
    try:
        # Validate and constrain parameters
        limit = max(1, min(limit, 100))
        hours_back = max(1, min(hours_back, 168))  # Max 7 days
        
        # Build WHERE clause based on parameters
        where_conditions = []
        params = []
        param_index = 1
        
        # Schema filtering
        if schema_name:
            where_conditions.append(f"schemaname = ${param_index}")
            params.append(schema_name)
            param_index += 1
        else:
            # Exclude system schemas
            where_conditions.append("schemaname NOT IN ('information_schema', 'pg_catalog')")
            where_conditions.append("schemaname NOT LIKE 'pg_%'")
        
        # Add LIMIT parameter
        params.append(limit)
        
        # Combine WHERE conditions
        where_filter = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        query = f"""
        SELECT 
            schemaname as schema_name,
            relname as table_name,
            last_autovacuum,
            last_autoanalyze,
            autovacuum_count as total_autovacuums,
            autoanalyze_count as total_autoanalyzes,
            -- Calculate time since last autovacuum
            CASE 
                WHEN last_autovacuum IS NOT NULL 
                THEN extract(hours from now() - last_autovacuum)::int
                ELSE NULL 
            END as hours_since_autovacuum,
            -- Calculate time since last autoanalyze
            CASE 
                WHEN last_autoanalyze IS NOT NULL 
                THEN extract(hours from now() - last_autoanalyze)::int
                ELSE NULL 
            END as hours_since_autoanalyze,
            -- Activity classification
            CASE 
                WHEN last_autovacuum IS NULL THEN 'NEVER AUTOVACUUMED'
                WHEN last_autovacuum < now() - interval '{hours_back} hours' THEN 'NO RECENT ACTIVITY'
                WHEN last_autovacuum > now() - interval '4 hours' THEN 'VERY RECENT'
                WHEN last_autovacuum > now() - interval '12 hours' THEN 'RECENT'
                ELSE 'MODERATE'
            END as autovacuum_activity_level,
            -- Current table statistics for context
            n_dead_tup as current_dead_tuples,
            n_live_tup as live_tuples,
            -- Activity frequency (rough estimate)
            CASE 
                WHEN autovacuum_count = 0 THEN 'No Activity'
                WHEN autovacuum_count = 1 THEN 'Low Activity'
                WHEN autovacuum_count <= 5 THEN 'Moderate Activity' 
                WHEN autovacuum_count <= 20 THEN 'High Activity'
                ELSE 'Very High Activity'
            END as activity_frequency,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) as table_size
        FROM pg_stat_user_tables
        {where_filter}
        ORDER BY 
            CASE 
                WHEN last_autovacuum IS NULL THEN 1
                WHEN last_autovacuum < now() - interval '{hours_back} hours' THEN 2
                ELSE 3
            END,
            hours_since_autovacuum ASC NULLS LAST,
            autovacuum_count DESC
        LIMIT ${len(params)}
        """
        
        autovacuum_activity = await execute_query(query, params, database=database_name)
        
        # Get actual database name for clarity
        if not database_name:
            actual_db_name = await get_current_database_name(database_name)
        else:
            actual_db_name = database_name
        
        if not autovacuum_activity:
            # Build descriptive message
            conditions = []
            if schema_name:
                conditions.append(f"schema '{schema_name}'")
            else:
                conditions.append("any user schema")
            
            condition_str = " and ".join(conditions)
            return f"No tables found for autovacuum activity analysis in {condition_str} (Database: {actual_db_name})"
        
        # Build title based on parameters - ALWAYS include actual database name
        title_parts = []
        if schema_name:
            title_parts.append(f"Schema: {schema_name}")
        else:
            title_parts.append("All Schemas")
        
        title_parts.append(f"Last {hours_back}h")
        
        # Always include database name in title for clarity
        title = f"Autovacuum Activity Analysis (Database: {actual_db_name}, {', '.join(title_parts)})"
            
        return format_table_data(autovacuum_activity, title)
        
    except Exception as e:
        logger.error(f"Failed to analyze autovacuum activity: {e}")
        return f"Error analyzing autovacuum activity: {str(e)}"


@mcp.tool()
async def get_running_vacuum_operations(database_name: str = None) -> str:
    """
    [Tool Purpose]: Monitor currently running VACUUM and ANALYZE operations in real-time
    
    [Exact Functionality]:
    - Show all currently active VACUUM, ANALYZE, and REINDEX operations
    - Display operation progress, elapsed time, and process details
    - Identify blocking or long-running maintenance operations
    - Provide process IDs for operation tracking
    
    [Required Use Cases]:
    - When user requests "running VACUUM", "active maintenance", "current VACUUM status", etc.
    - When troubleshooting slow or stuck VACUUM operations
    - When monitoring maintenance operation progress
    - When identifying maintenance operations that may be affecting performance
    
    [Strictly Prohibited Use Cases]:
    - Requests for terminating or controlling VACUUM processes
    - Requests for starting new VACUUM operations
    - Requests for changing VACUUM parameters or configuration
    
    Args:
        database_name: Target database name (shows operations in all databases if omitted)
    
    Returns:
        Real-time status of running VACUUM/ANALYZE operations with timing and progress information
    """
    try:
        # Build WHERE clause for database filtering
        where_conditions = ["state = 'active'", "pid <> pg_backend_pid()"]
        params = []
        
        if database_name:
            where_conditions.append("datname = $1")
            params.append(database_name)
        
        where_filter = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            pid,
            datname as database_name,
            usename as username,
            client_addr,
            state,
            query_start,
            now() - query_start as elapsed_time,
            -- Extract operation type from query
            CASE 
                WHEN query ILIKE '%VACUUM ANALYZE%' THEN 'VACUUM ANALYZE'
                WHEN query ILIKE '%VACUUM%' AND query ILIKE '%FREEZE%' THEN 'VACUUM FREEZE'
                WHEN query ILIKE '%VACUUM%' AND query ILIKE '%FULL%' THEN 'VACUUM FULL'
                WHEN query ILIKE '%VACUUM%' THEN 'VACUUM'
                WHEN query ILIKE '%ANALYZE%' THEN 'ANALYZE'
                WHEN query ILIKE '%REINDEX%' THEN 'REINDEX'
                WHEN query ILIKE '%CLUSTER%' THEN 'CLUSTER'
                ELSE 'OTHER MAINTENANCE'
            END as operation_type,
            -- Extract table name if possible
            CASE 
                WHEN query ~* 'vacuum.*?([a-zA-Z_][a-zA-Z0-9_]*\\.?[a-zA-Z_][a-zA-Z0-9_]*)' THEN
                    substring(query from '[a-zA-Z_][a-zA-Z0-9_]*\\.?[a-zA-Z_][a-zA-Z0-9_]*')
                WHEN query ~* 'analyze.*?([a-zA-Z_][a-zA-Z0-9_]*\\.?[a-zA-Z_][a-zA-Z0-9_]*)' THEN
                    substring(query from '[a-zA-Z_][a-zA-Z0-9_]*\\.?[a-zA-Z_][a-zA-Z0-9_]*')
                ELSE 'Multiple/Unknown'
            END as target_table,
            -- Performance impact indicators
            CASE 
                WHEN query ILIKE '%FULL%' THEN 'HIGH (Exclusive Lock)'
                WHEN query ILIKE '%FREEZE%' THEN 'MEDIUM (Shared Lock)'
                WHEN query ILIKE '%ANALYZE%' THEN 'LOW (Shared Lock)'
                ELSE 'LOW-MEDIUM'
            END as impact_level,
            -- Show partial query (first 150 characters)
            LEFT(query, 150) as operation_query
        FROM pg_stat_activity 
        WHERE {where_filter}
          AND (query ILIKE '%VACUUM%' 
               OR query ILIKE '%ANALYZE%' 
               OR query ILIKE '%REINDEX%'
               OR query ILIKE '%CLUSTER%')
        ORDER BY query_start ASC
        """
        
        running_ops = await execute_query(query, params, database=database_name)
        
        # Get actual database name for clarity
        if database_name:
            actual_db_name = database_name
        else:
            actual_db_name = "All Databases"
        
        if not running_ops:
            return f"No VACUUM/ANALYZE operations currently running (Target: {actual_db_name})"
        
        # Always include database context in title
        title = f"Currently Running VACUUM/ANALYZE Operations (Target: {actual_db_name})"
            
        return format_table_data(running_ops, title)
        
    except Exception as e:
        logger.error(f"Failed to get running VACUUM operations: {e}")
        return f"Error retrieving running VACUUM operations: {str(e)}"


@mcp.tool()
async def get_vacuum_effectiveness_analysis(database_name: str = None, schema_name: str = None, limit: int = 30) -> str:
    """
    [Tool Purpose]: Analyze VACUUM effectiveness and maintenance patterns using existing statistics
    
    [Exact Functionality]:
    - Compare manual VACUUM vs autovacuum effectiveness patterns
    - Analyze VACUUM frequency vs table activity (DML operations)
    - Identify tables with suboptimal VACUUM patterns
    - Calculate maintenance efficiency ratios without performance impact
    - Show VACUUM coverage analysis across all tables
    
    [Required Use Cases]:
    - When user requests "VACUUM effectiveness", "maintenance efficiency", "VACUUM analysis", etc.
    - When planning manual VACUUM schedules or autovacuum tuning
    - When identifying tables with poor maintenance patterns
    - When analyzing overall database maintenance health
    
    [Strictly Prohibited Use Cases]:
    - Requests for VACUUM execution or scheduling
    - Requests for autovacuum configuration changes
    - Requests for maintenance operation control
    
    Args:
        database_name: Target database name (uses default database from POSTGRES_DB env var if omitted)
        schema_name: Schema to analyze (analyzes all user schemas if omitted)
        limit: Maximum number of tables to analyze (1-100, default: 30)
    
    Returns:
        VACUUM effectiveness analysis with maintenance patterns and recommendations
    """
    try:
        # Validate and constrain limit
        limit = max(1, min(limit, 100))
        
        # Build WHERE clause based on parameters
        where_conditions = []
        params = []
        param_index = 1
        
        # Schema filtering
        if schema_name:
            where_conditions.append(f"schemaname = ${param_index}")
            params.append(schema_name)
            param_index += 1
        else:
            # Exclude system schemas
            where_conditions.append("schemaname NOT IN ('information_schema', 'pg_catalog')")
            where_conditions.append("schemaname NOT LIKE 'pg_%'")
        
        # Add LIMIT parameter
        params.append(limit)
        
        # Combine WHERE conditions
        where_filter = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        query = f"""
        SELECT 
            schemaname as schema_name,
            relname as table_name,
            -- Current table state
            n_dead_tup as current_dead_tuples,
            n_live_tup as live_tuples,
            CASE 
                WHEN (n_live_tup + n_dead_tup) = 0 THEN 0
                ELSE round(100.0 * n_dead_tup / (n_live_tup + n_dead_tup), 2)
            END as current_bloat_percent,
            -- VACUUM execution patterns
            vacuum_count as manual_vacuum_count,
            autovacuum_count as auto_vacuum_count,
            (vacuum_count + autovacuum_count) as total_vacuum_operations,
            -- Activity vs maintenance ratio
            (n_tup_ins + n_tup_upd + n_tup_del) as total_dml_operations,
            CASE 
                WHEN (vacuum_count + autovacuum_count) = 0 THEN 'NEVER VACUUMED'
                WHEN (n_tup_ins + n_tup_upd + n_tup_del) = 0 THEN 'NO DML ACTIVITY'
                ELSE round((n_tup_ins + n_tup_upd + n_tup_del)::numeric / (vacuum_count + autovacuum_count), 1)::text
            END as dml_per_vacuum_ratio,
            -- Maintenance pattern analysis
            CASE 
                WHEN vacuum_count = 0 AND autovacuum_count = 0 THEN 'NO MAINTENANCE'
                WHEN vacuum_count > autovacuum_count THEN 'MANUAL DOMINANT'
                WHEN autovacuum_count > vacuum_count THEN 'AUTO DOMINANT'
                WHEN vacuum_count = autovacuum_count THEN 'BALANCED'
                ELSE 'MIXED PATTERN'
            END as maintenance_pattern,
            -- Last maintenance timing
            GREATEST(last_vacuum, last_autovacuum) as last_any_vacuum,
            CASE 
                WHEN GREATEST(last_vacuum, last_autovacuum) IS NOT NULL 
                THEN extract(hours from now() - GREATEST(last_vacuum, last_autovacuum))::int
                ELSE NULL 
            END as hours_since_last_vacuum,
            -- Effectiveness assessment
            CASE 
                WHEN (vacuum_count + autovacuum_count) = 0 THEN 'CRITICAL: No maintenance'
                WHEN n_dead_tup > (0.3 * n_live_tup + 100) THEN 'POOR: High bloat despite VACUUM'
                WHEN n_dead_tup < (0.05 * n_live_tup + 10) THEN 'EXCELLENT: Very clean'
                WHEN n_dead_tup < (0.15 * n_live_tup + 50) THEN 'GOOD: Well maintained'
                ELSE 'MODERATE: Needs attention'
            END as vacuum_effectiveness,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) as table_size
        FROM pg_stat_user_tables
        {where_filter}
        ORDER BY 
            -- Priority: problems first, then by activity level
            CASE 
                WHEN (vacuum_count + autovacuum_count) = 0 THEN 1
                WHEN n_dead_tup > (0.3 * n_live_tup + 100) THEN 2
                ELSE 3
            END,
            (n_tup_ins + n_tup_upd + n_tup_del) DESC
        LIMIT ${len(params)}
        """
        
        effectiveness_analysis = await execute_query(query, params, database=database_name)
        
        # Get actual database name for clarity
        if not database_name:
            actual_db_name = await get_current_database_name(database_name)
        else:
            actual_db_name = database_name
        
        if not effectiveness_analysis:
            # Build descriptive message
            conditions = []
            if schema_name:
                conditions.append(f"schema '{schema_name}'")
            else:
                conditions.append("any user schema")
            
            condition_str = " and ".join(conditions)
            return f"No tables found for VACUUM effectiveness analysis in {condition_str} (Database: {actual_db_name})"
        
        # Build title based on parameters - ALWAYS include actual database name
        title_parts = []
        if schema_name:
            title_parts.append(f"Schema: {schema_name}")
        else:
            title_parts.append("All Schemas")
        
        # Always include database name in title for clarity
        title = f"VACUUM Effectiveness Analysis (Database: {actual_db_name}, {', '.join(title_parts)})"
            
        return format_table_data(effectiveness_analysis, title)
        
    except Exception as e:
        logger.error(f"Failed to analyze VACUUM effectiveness: {e}")
        return f"Error analyzing VACUUM effectiveness: {str(e)}"


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
    [Tool Purpose]: Analyze background writer and checkpoint performance statistics with version compatibility
    
    [Exact Functionality]:
    - Show checkpoint execution statistics (timed vs requested)
    - Display checkpoint timing information (write and sync times)
    - Provide buffer writing statistics by different processes
    - Analyze background writer performance and efficiency
    - Automatically adapts to PostgreSQL version (15+ uses separate checkpointer view)
    
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
        Background writer and checkpoint performance statistics with version-appropriate data
    """
    try:
        pg_version = await get_postgresql_version()
        
        if pg_version.has_checkpointer_split:
            # PostgreSQL 15 ONLY: Use separate views  
            query = """
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
                buffers_written as buffers_written_by_checkpoints,
                0 as buffers_written_by_bgwriter,
                0 as buffers_written_by_backend,
                0 as backend_fsync_calls,
                0 as buffers_allocated,
                0 as bgwriter_maxwritten_stops,
                0 as bgwriter_stop_ratio_percent,
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
                0 as buffers_written_by_checkpoints,
                buffers_clean as buffers_written_by_bgwriter,
                0 as buffers_written_by_backend,
                0 as backend_fsync_calls,
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
            explanation = f"PostgreSQL {pg_version} detected - using separate checkpointer and bgwriter views (PG15 only)"
        else:
            # PostgreSQL 12-14, 16+: Use combined bgwriter view
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
                CASE 
                    WHEN buffers_clean > 0 AND maxwritten_clean > 0 THEN
                        ROUND((maxwritten_clean::numeric / buffers_clean) * 100, 2)
                    ELSE 0
                END as bgwriter_stop_ratio_percent,
                stats_reset as stats_reset_time
            FROM pg_stat_bgwriter
            """
            explanation = f"PostgreSQL {pg_version} detected - using combined bgwriter view (includes checkpointer)"
        
        stats = await execute_query(query)
        
        result = []
        result.append("=== Background Writer & Checkpointer Statistics ===\n")
        result.append(explanation)
        result.append("")
        result.append(format_table_data(stats, "Background Process Performance"))
        
        if pg_version.has_checkpointer_split:
            result.append("\nNote: PostgreSQL 15 provides separate detailed statistics for checkpointer and background writer processes")
        else:
            result.append(f"\nNote: PostgreSQL {pg_version} uses combined bgwriter view with all background process statistics")
            result.append("\nNote: Upgrade to PostgreSQL 15+ for separate checkpointer and background writer statistics")
        
        return "\n".join(result)
        
    except Exception as e:
        logger.error(f"Failed to get bgwriter stats: {e}")
        return f"Error retrieving background writer statistics: {str(e)}"


@mcp.tool()
async def get_io_stats(limit: int = 20, database_name: str = None) -> str:
    """
    [Tool Purpose]: Analyze comprehensive I/O statistics across all database operations with version compatibility
    
    [Exact Functionality]:
    - PostgreSQL 16+: Shows detailed I/O statistics from pg_stat_io (reads, writes, hits, timing)
    - PostgreSQL 12-15: Falls back to pg_statio_* views with basic I/O information
    - Provides buffer cache efficiency analysis and I/O timing when available
    - Identifies I/O patterns and performance bottlenecks
    
    [Required Use Cases]:
    - When user requests "I/O stats", "I/O performance", "buffer cache analysis", etc.
    - When analyzing storage performance and buffer efficiency
    - When identifying I/O bottlenecks across different backend types
    - When comparing I/O patterns between relation types
    
    [Strictly Prohibited Use Cases]:
    - Requests for I/O configuration changes or buffer tuning
    - Requests for storage or filesystem modifications
    - Requests for I/O statistics reset
    
    Args:
        limit: Maximum number of results to return (1-100, default 20)
        database_name: Target database name (optional)
    
    Returns:
        Comprehensive I/O statistics with version-appropriate detail level
    """
    try:
        limit = max(1, min(limit, 100))
        pg_version = await get_postgresql_version(database_name)
        
        if pg_version.has_pg_stat_io:
            # PostgreSQL 16+: Use comprehensive pg_stat_io
            query = f"""
            SELECT 
                backend_type,
                object,
                context,
                reads,
                ROUND(read_time::numeric, 2) as read_time_ms,
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
            title = f"Comprehensive I/O Statistics (pg_stat_io - PostgreSQL {pg_version})"
            explanation = "Detailed I/O statistics showing all backend types, contexts, and timing information"
        else:
            # PostgreSQL 12-15: Fall back to pg_statio_* views
            query = f"""
            SELECT 
                'relation I/O (fallback)' as backend_type,
                'heap+index+toast' as object,
                'basic' as context,
                (heap_blks_read + idx_blks_read + toast_blks_read + tidx_blks_read) as reads,
                0 as read_time_ms,
                0 as writes,
                0 as write_time_ms,
                0 as extends,
                0 as extend_time_ms,
                (heap_blks_hit + idx_blks_hit + toast_blks_hit + tidx_blks_hit) as hits,
                0 as evictions,
                0 as reuses,
                0 as fsyncs,
                0 as fsync_time_ms,
                CASE 
                    WHEN ((heap_blks_read + idx_blks_read + toast_blks_read + tidx_blks_read) + 
                          (heap_blks_hit + idx_blks_hit + toast_blks_hit + tidx_blks_hit)) > 0 THEN
                        ROUND(((heap_blks_hit + idx_blks_hit + toast_blks_hit + tidx_blks_hit)::numeric / 
                               ((heap_blks_read + idx_blks_read + toast_blks_read + tidx_blks_read) +
                                (heap_blks_hit + idx_blks_hit + toast_blks_hit + tidx_blks_hit))) * 100, 2)
                    ELSE 0
                END as hit_ratio_percent,
                schemaname || '.' || relname as table_name
            FROM pg_statio_all_tables
            WHERE (heap_blks_read + idx_blks_read + toast_blks_read + tidx_blks_read +
                   heap_blks_hit + idx_blks_hit + toast_blks_hit + tidx_blks_hit) > 0
            ORDER BY ((heap_blks_read + idx_blks_read + toast_blks_read + tidx_blks_read) + 
                     (heap_blks_hit + idx_blks_hit + toast_blks_hit + tidx_blks_hit)) DESC
            LIMIT {limit}
            """
            title = f"Basic I/O Statistics (pg_statio_* fallback - PostgreSQL {pg_version})"
            explanation = "Basic I/O statistics from pg_statio_* views - limited data available on this version"
        
        stats = await execute_query(query, database=database_name)
        
        if not stats:
            return "No I/O statistics found"
        
        result = []
        result.append("=== Database I/O Statistics ===\n")
        result.append(explanation)
        result.append("")
        result.append(format_table_data(stats, title))
        
        # Add version-specific notes
        if pg_version.has_pg_stat_io:
            result.append(f"\n✅ PostgreSQL {pg_version} provides comprehensive I/O monitoring with timing details")
            result.append("📊 Backend types: client backend, checkpointer, background writer, autovacuum, etc.")
            result.append("🎯 Contexts: normal, vacuum, bulkread, bulkwrite operations")
        else:
            result.append(f"\n⚠️  PostgreSQL {pg_version} provides basic I/O statistics only")
            result.append("🚀 Upgrade to PostgreSQL 16+ for comprehensive I/O monitoring with:")
            result.append("   • Per-backend-type I/O statistics")
            result.append("   • I/O timing information (when track_io_timing enabled)")
            result.append("   • Context-aware I/O tracking (normal/vacuum/bulk operations)")
            result.append("   • Buffer eviction and reuse statistics")
        
        return "\n".join(result)
        
    except Exception as e:
        logger.error(f"Failed to get I/O stats: {e}")
        return f"Error retrieving I/O statistics: {str(e)}"


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
        # Build WHERE clause with proper filtering for schema and non-empty I/O stats
        where_conditions = []
        params = []
        param_count = 0
        
        if schema_name:
            param_count += 1
            where_conditions.append(f"schemaname = ${param_count}")
            params.append(schema_name)
        
        # Only show tables with actual I/O activity
        where_conditions.append("(heap_blks_read + heap_blks_hit + idx_blks_read + idx_blks_hit + COALESCE(toast_blks_read, 0) + COALESCE(toast_blks_hit, 0) + COALESCE(tidx_blks_read, 0) + COALESCE(tidx_blks_hit, 0)) > 0")
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
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
        # Build WHERE clause with proper filtering for schema and non-empty I/O stats
        where_conditions = []
        params = []
        param_count = 0
        
        if schema_name:
            param_count += 1
            where_conditions.append(f"schemaname = ${param_count}")
            params.append(schema_name)
        
        # Only show indexes with actual I/O activity
        where_conditions.append("(idx_blks_read + idx_blks_hit) > 0")
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
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
        # Use version-compatible query
        query = await VersionAwareQueries.get_all_tables_stats_query(include_system, database_name)
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
        WHERE calls > 0
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