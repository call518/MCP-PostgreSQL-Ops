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

# =============================================================================
# MCP Tools (PostgreSQL Operations Tools)
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
        
        tables = await execute_query(query)
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
        query = """
        SELECT 
            usename as username,
            usesysid as user_id,
            CASE WHEN usesuper THEN 'Yes' ELSE 'No' END as is_superuser,
            CASE WHEN usecreatedb THEN 'Yes' ELSE 'No' END as can_create_db,
            CASE WHEN usecatupd THEN 'Yes' ELSE 'No' END as can_update_catalog,
            valuntil as valid_until
        FROM pg_user
        ORDER BY usename
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
async def get_pg_stat_statements_top_queries(limit: int = 20) -> str:
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
    
    Returns:
        Performance statistics including query text, call count, total execution time, average execution time, and cache hit rate
    """
    try:
        # Check extension exists
        if not await check_extension_exists("pg_stat_statements"):
            return "Error: pg_stat_statements extension is not installed or enabled"
        
        # Limit range constraint
        limit = max(1, min(limit, 100))
        
        data = await get_pg_stat_statements_data(limit)
        return format_table_data(data, f"Top {limit} Queries by Total Execution Time (pg_stat_statements)")
        
    except Exception as e:
        logger.error(f"Failed to get pg_stat_statements data: {e}")
        return f"Error retrieving pg_stat_statements data: {str(e)}"


@mcp.tool()
async def get_pg_stat_monitor_recent_queries(limit: int = 20) -> str:
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
    
    Returns:
        Detailed monitoring information including query text, execution statistics, client info, and bucket time
    """
    try:
        # Check extension exists
        if not await check_extension_exists("pg_stat_monitor"):
            return "Error: pg_stat_monitor extension is not installed or enabled"
        
        # Limit range constraint
        limit = max(1, min(limit, 100))
        
        data = await get_pg_stat_monitor_data(limit)
        return format_table_data(data, f"Recent {limit} Queries (pg_stat_monitor)")
        
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
async def get_table_size_info(schema_name: str = "public") -> str:
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
        
        tables = await execute_query(query, [schema_name])
        
        if not tables:
            return f"No tables found in schema '{schema_name}'"
        
        # Calculate total size
        total_size = sum(row['total_size_bytes'] for row in tables)
        
        result = []
        result.append(f"Total size of tables in schema '{schema_name}': {format_bytes(total_size)}\n")
        
        # Remove total_size_bytes column
        for row in tables:
            del row['total_size_bytes']
            
        result.append(format_table_data(tables, f"Table Sizes in Schema '{schema_name}'"))
        
        return "\n".join(result)
        
    except Exception as e:
        logger.error(f"Failed to get table size info: {e}")
        return f"Error retrieving table size information: {str(e)}"


@mcp.tool()
async def get_postgresql_config(config_name: str = None) -> str:
    """
    [Tool Purpose]: Retrieve and analyze PostgreSQL server configuration parameter values
    
    [Exact Functionality]:
    - Retrieve all PostgreSQL configuration parameters (when config_name is not specified)
    - Retrieve current value and description of specific configuration parameter
    - Display whether configuration can be changed and if restart is required
    
    [Required Use Cases]:
    - When user requests "PostgreSQL config", "config", "parameters", etc.
    - When checking specific configuration values is needed
    - When configuration status identification is needed for performance tuning
    
    [Strictly Prohibited Use Cases]:
    - Requests for configuration value changes or modifications
    - Requests for PostgreSQL restart or reload
    - Requests for system-level configuration changes
    
    Args:
        config_name: Specific configuration parameter name to retrieve (shows key configs if omitted)
    
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
        else:
            # Retrieve key configurations
            query = """
            SELECT 
                name,
                setting,
                unit,
                short_desc
            FROM pg_settings 
            WHERE name IN (
                'max_connections',
                'shared_buffers',
                'effective_cache_size',
                'maintenance_work_mem',
                'checkpoint_completion_target',
                'wal_buffers',
                'default_statistics_target',
                'random_page_cost',
                'effective_io_concurrency',
                'work_mem',
                'max_worker_processes',
                'max_parallel_workers_per_gather'
            )
            ORDER BY name
            """
            configs = await execute_query(query)
            return format_table_data(configs, "Key PostgreSQL Configuration Parameters")
            
    except Exception as e:
        logger.error(f"Failed to get PostgreSQL config: {e}")
        return f"Error retrieving PostgreSQL configuration: {str(e)}"


@mcp.tool()
async def get_index_usage_stats() -> str:
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
    
    Returns:
        Index usage statistics including schema, table, index name, scans, and tuples read
    """
    try:
        query = """
        SELECT 
            schemaname as schema_name,
            tablename as table_name,
            indexname as index_name,
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
        ORDER BY idx_scan DESC, schemaname, tablename, indexname
        """
        
        indexes = await execute_query(query)
        return format_table_data(indexes, "Index Usage Statistics")
        
    except Exception as e:
        logger.error(f"Failed to get index usage stats: {e}")
        return f"Error retrieving index usage statistics: {str(e)}"


@mcp.tool()
async def get_vacuum_analyze_stats() -> str:
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
        
        stats = await execute_query(query)
        return format_table_data(stats, "VACUUM/ANALYZE Statistics")
        
    except Exception as e:
        logger.error(f"Failed to get vacuum/analyze stats: {e}")
        return f"Error retrieving VACUUM/ANALYZE statistics: {str(e)}"


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