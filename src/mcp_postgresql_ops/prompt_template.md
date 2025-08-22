# PostgreSQL Operations MCP Server - Prompt Templates

## Server Overview

A professional MCP server for PostgreSQL database server operations, monitoring, and management. Provides advanced performance analysis capabilities using pg_stat_statements and pg_stat_monitor extensions.

## Key Features

- ✅ **PostgreSQL Monitoring**: Performance analysis based on pg_stat_statements and pg_stat_monitor
- ✅ **Structure Exploration**: Database, table, and user listing
- ✅ **Performance Analysis**: Slow query identification and index usage analysis
- ✅ **Capacity Management**: Database and table size analysis
- ✅ **Configuration Retrieval**: PostgreSQL configuration parameter verification
- ✅ **Safe Read-Only**: All operations are read-only and safe

## Available Tools

### 📊 Server Information & Status
1. **get_server_info**: PostgreSQL server information and extension status
2. **get_active_connections**: Current active connections and session information
3. **get_postgresql_config**: PostgreSQL configuration parameters

### 🗄️ Structure Exploration
4. **get_database_list**: All database list and size information
5. **get_table_list**: Table list and size information
6. **get_user_list**: Database user list and permissions

### ⚡ Performance Monitoring
7. **get_pg_stat_statements_top_queries**: Slow query analysis based on performance statistics
8. **get_pg_stat_monitor_recent_queries**: Real-time query monitoring
9. **get_index_usage_stats**: Index usage rate and efficiency analysis

### 💾 Capacity Management
10. **get_database_size_info**: Database capacity analysis
11. **get_table_size_info**: Table and index size analysis
12. **get_vacuum_analyze_stats**: VACUUM/ANALYZE status and history

### 🔒 Lock & Deadlock Monitoring
13. **get_lock_monitoring**: Current locks and blocked sessions analysis

### 📝 WAL & Replication Monitoring
14. **get_wal_status**: WAL status and archiving information
15. **get_replication_status**: Replication connections and lag monitoring

### 📈 Database Performance Statistics
16. **get_database_stats**: Comprehensive database-wide performance metrics
17. **get_bgwriter_stats**: Background writer and checkpoint performance analysis
18. **get_all_tables_stats**: Complete table statistics (including system tables)
19. **get_user_functions_stats**: User-defined function performance analysis

### 💿 I/O Performance Analysis
20. **get_table_io_stats**: Table I/O statistics (disk reads vs buffer cache hits)
21. **get_index_io_stats**: Index I/O performance and buffer efficiency analysis

### 🔄 Replication Monitoring
22. **get_database_conflicts_stats**: Query conflicts in standby/replica environments

## Sample Prompts

### � Database Performance Analysis
- "Show database-wide performance statistics"
- "Analyze transaction commit ratios and I/O patterns"
- "Check buffer cache hit ratios for all databases"
- "Monitor temporary file usage and deadlock counts"

### 🔧 Background Writer & Checkpoints
- "Analyze checkpoint performance and timing"
- "Show background writer efficiency statistics"
- "Check buffer allocation and writing patterns"
- "Monitor checkpoint scheduling vs requested ratios"

### 🔍 Server Health Check
- "Check PostgreSQL server status"
- "Verify if extensions are installed"
- "Show current active connection count"
- "Display PostgreSQL version and configuration"

### 📊 Performance Analysis
- "Show top 20 slowest queries"
- "Find unused indexes"
- "Analyze recent query activity"
- "Identify performance bottlenecks"
- "Show cache hit ratios for queries"

### 💾 Capacity Management
- "Check database sizes"
- "Find largest tables"
- "Show tables that need VACUUM"
- "Analyze disk usage by database"
- "Display table and index sizes"

### 🗄️ Structure Analysis
- "List all databases with owners"
- "Show tables in public schema"
- "Display user accounts and permissions"
- "Explore database structure"

### 📈 Advanced Monitoring
- "Monitor active sessions and queries"
- "Analyze index usage efficiency"
- "Check VACUUM and ANALYZE history"
- "Review PostgreSQL configuration settings"
- "Find memory-related configuration parameters"
- "Show all logging configuration options"
- "Search for connection-related settings"
- "Identify connection patterns"

## Usage Guidelines

### When to Use Each Tool

#### Server Information Tools
- Use `get_server_info` first to verify connectivity and extensions
- Use `get_active_connections` to check current load
- Use `get_postgresql_config` for configuration analysis:
  - Specific parameter: `get_postgresql_config(config_name="shared_buffers")`
  - Keyword search: `get_postgresql_config(filter_text="memory")` for memory-related settings
  - Browse all: `get_postgresql_config()` without parameters

#### Structure Exploration Tools
- Use `get_database_list` to overview all databases
- Use `get_table_list` to explore database structure
- Use `get_user_list` for user management overview

#### Performance Analysis Tools
- Use `get_pg_stat_statements_top_queries` for query optimization
- Use `get_pg_stat_monitor_recent_queries` for real-time monitoring
- Use `get_index_usage_stats` to identify inefficient indexes

#### Capacity Management Tools
- Use `get_database_size_info` for disk space planning
- Use `get_table_size_info` for detailed table analysis
- Use `get_vacuum_analyze_stats` for maintenance planning

### Best Practices

1. **Start with Server Info**: Always check server status first
2. **Use Limits**: Specify reasonable limits for query results
3. **Monitor Regularly**: Set up regular monitoring workflows
4. **Analyze Patterns**: Look for trends in performance data
5. **Document Findings**: Keep track of performance issues

## Tool Parameters

### Limit Parameters
- Most tools accept `limit` parameter (default: 20, max: 100)
- Use smaller limits for initial analysis
- Increase limits for comprehensive reviews

### Database/Schema Parameters
- `get_table_list(database_name)`: Specify target database
- `get_table_size_info(schema_name)`: Specify target schema
- `get_postgresql_config(config_name, filter_text)`: Specify configuration parameter or search by keyword
  - `config_name`: Exact parameter name (optional)
  - `filter_text`: Search for parameters containing specific keywords (optional)

## Prerequisites

### Required Extensions
```sql
-- Essential for query performance analysis
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Optional for advanced monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_monitor;
```

### Permissions
- Read access to system catalogs
- Connection to PostgreSQL database
- Sufficient privileges for statistics views

## Troubleshooting Prompts

### Connection Issues
- "Check PostgreSQL server connectivity"
- "Verify connection parameters"
- "Test database access permissions"

### Extension Problems
- "Check if pg_stat_statements is installed"
- "Verify pg_stat_monitor availability"
- "Show installed extensions status"

### Performance Issues
- "Analyze slow query performance"
- "Check database load and connections"
- "Review index usage efficiency"
- "Monitor recent query patterns"

## Integration Examples

### Regular Health Checks
1. "Check server status and active connections"
2. "Show top 10 slowest queries from last hour"
3. "Verify all databases are accessible"
4. "Check if any tables need maintenance"

### Capacity Planning
1. "Analyze database sizes and growth trends"
2. "Identify largest tables and indexes"
3. "Review disk usage by schema"
4. "Plan storage capacity requirements"

### Performance Optimization
1. "Find queries consuming most resources"
2. "Identify unused or inefficient indexes"
3. "Analyze cache hit ratios"
4. "Monitor query execution patterns"

## Example Queries

### � Extension-Independent Tools (Always Available)

**get_server_info**
- "Show PostgreSQL server version and extension status"
- "Check if pg_stat_statements is installed"
- "Check server compatibility"
- "Show server version and compatibility features"
- "Check what MCP tools are available on this PostgreSQL version"
- "Displays feature availability matrix and upgrade recommendations"

**get_active_connections**
- "Show all active connections"
- "List current sessions with database and user"
- "Monitor current sessions and their running queries"

**get_postgresql_config**
- "Show all PostgreSQL configuration parameters"
- "Find all memory-related configuration settings"
- "Show PostgreSQL configuration parameter for shared_buffers"
- "Search for connection-related settings"
- "Find logging configuration"
- "Check specific parameter"

**get_database_list**
- "List all databases and their sizes"
- "Show database list with owner information"
- "List all databases with their owners and sizes"
- "Show database encoding and connection limits"

**get_table_list**
- "List all tables in the current database"
- "Show table sizes in the public schema"
- "List all tables in the default database"
- "Show tables in specific database"

**get_user_list**
- "List all database users and their roles"
- "Show user permissions for a specific database"
- "Display all database users with their permissions"
- "Show superuser status and account limitations for all users"

**get_index_usage_stats**
- "Analyze index usage efficiency"
- "Find unused indexes in the current database"
- "Analyze index usage in default database"
- "Check index efficiency in specific database"
- "Identify unused indexes with zero scans (look for 'Never used' entries)"

**get_database_size_info**
- "Show database capacity analysis"
- "Find the largest databases by size"
- "Show disk usage for all databases sorted by size"
- "Calculate total storage consumption across all databases"

**get_table_size_info**
- "Show table and index size analysis"
- "Find largest tables in a specific schema"
- "Analyze table sizes in public schema"
- "Check table sizes in specific database schema"

**get_vacuum_analyze_stats**
- "Show recent VACUUM and ANALYZE operations"
- "List tables needing VACUUM"
- "Review VACUUM and ANALYZE history for all tables"
- "Check maintenance status in specific database"
- "Find tables needing maintenance (check last_vacuum dates)"

**get_lock_monitoring**
- "Show all current locks and blocked sessions"
- "Show only blocked sessions with granted=false filter"
- "Monitor locks by specific user with username filter"
- "Check exclusive locks with mode filter"

**get_wal_status**
- "Show WAL status and archiving information"
- "Monitor WAL generation and current LSN position"

**get_replication_status**
- "Check replication connections and lag status"
- "Monitor replication slots and WAL receiver status"

**get_database_stats**
- "Show comprehensive database performance metrics"
- "Analyze transaction commit ratios and I/O statistics"
- "Monitor buffer cache hit ratios and temporary file usage"
- "Show database-wide performance statistics"
- "Analyze transaction commit ratios across all databases"
- "Check buffer cache hit ratios and I/O statistics"
- "Monitor temporary file usage and deadlock counts"

**get_bgwriter_stats**
- "Analyze checkpoint performance and timing"
- "Show me checkpoint performance"
- "Show background writer efficiency statistics"
- "Monitor buffer allocation and fsync patterns"
- "Show background writer efficiency and buffer statistics"
- "Monitor checkpoint scheduling patterns"
- "Check buffer allocation and fsync performance"
- "Monitor checkpoint scheduling vs requested ratios"

**get_all_tables_stats**
- "Show comprehensive statistics for all tables"
- "Include system tables with include_system=true parameter"
- "Analyze table access patterns and maintenance needs"
- "Show comprehensive statistics for all user tables"
- "Include system tables in statistics analysis with include_system=true"
- "Monitor dead tuple ratios and table activity"

**get_user_functions_stats**
- "Analyze user-defined function performance"
- "Show function call counts and execution times"
- "Identify performance bottlenecks in custom functions"
- "Identify slow or frequently called functions"
- "Monitor function performance bottlenecks"
- ⚠️ **Requires**: `track_functions = pl` in postgresql.conf

**get_table_io_stats**
- "Analyze table I/O performance and buffer hit ratios"
- "Identify tables with poor buffer cache performance"
- "Monitor TOAST table I/O statistics"
- "Show disk reads vs buffer cache hits for tables in public schema"
- 💡 **Enhanced with**: `track_io_timing = on` for accurate timing

**get_index_io_stats**
- "Show index I/O performance and buffer efficiency"
- "Identify indexes causing excessive disk I/O"
- "Monitor index cache-friendliness patterns"
- "Analyze index buffer hit ratios in specific schema"
- 💡 **Enhanced with**: `track_io_timing = on` for accurate timing

**get_database_conflicts_stats**
- "Check replication conflicts on standby servers"
- "Analyze conflict types and resolution statistics"
- "Monitor standby server query cancellation patterns"
- "Check replication conflicts on standby server"
- "Monitor replication slots and WAL receiver status"

### 🚀 Version-Aware Tools (Auto-Adapting)

**get_io_stats** (New!)
- "Show comprehensive I/O statistics" (PostgreSQL 16+ provides detailed breakdown)
- "Analyze I/O statistics"
- "Analyze buffer cache efficiency and I/O timing"
- "Monitor I/O patterns by backend type and context"
- 📈 **PG16+**: Full pg_stat_io with timing, backend types, and contexts
- 📊 **PG12-15**: Basic pg_statio_* fallback with buffer hit ratios

**get_bgwriter_stats** (Enhanced!)
- "Show background writer and checkpoint performance"
- 📈 **PG15**: Separate checkpointer and bgwriter statistics (unique feature)
- 📊 **PG12-14, 16+**: Combined bgwriter stats (includes checkpointer data)

**get_server_info** (Enhanced!)
- "Show server version and compatibility features"
- "Check server compatibility"
- "Check what MCP tools are available on this PostgreSQL version"
- "Displays feature availability matrix and upgrade recommendations"

### 🟡 Extension-Dependent Tools

**get_pg_stat_statements_top_queries** (Requires `pg_stat_statements`)
- "Show top 10 slowest queries"
- "Analyze slow queries in the inventory database"
- "Show top 20 slowest queries"
- "Find queries consuming most resources"
- "Monitor query execution patterns"
- "Show cache hit ratios for queries"

**get_pg_stat_monitor_recent_queries** (Optional, uses `pg_stat_monitor`)
- "Show recent queries in real time"
- "Monitor query activity for the last 5 minutes"
- "Monitor recent 15 queries with detailed stats"
- "Track recent queries in testdb database"

### 🔧 Advanced Usage Examples

**Multi-Database Analysis**
- "Compare table sizes across databases"
- "Monitor performance across multiple databases using database_name parameter"
- "Analyze slow queries in specific database"
- "Check index efficiency in specific database"

**Performance Deep Dive**
- "Find unused indexes"
- "Analyze recent query activity"
- "Identify performance bottlenecks"
- "Analyze cache hit ratios"
- "Monitor query execution patterns"

**Capacity Planning**
- "Analyze database sizes and growth trends"
- "Identify largest tables and indexes"
- "Review disk usage by schema"
- "Plan storage capacity requirements"

**Configuration Troubleshooting**
- "Search for connection-related settings"
- "Find logging configuration"
- "Check specific parameter"

**💡 Pro Tip**: All tools support multi-database operations using the `database_name` parameter. This allows PostgreSQL superusers to analyze and monitor multiple databases from a single MCP server instance.

This MCP server provides comprehensive PostgreSQL monitoring and management capabilities while maintaining read-only safety and providing detailed insights for database administration with automatic version compatibility across PostgreSQL 12-18.
