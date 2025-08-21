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

## Sample Prompts

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

### 📊 Server Information & Status Examples

**get_server_info**
- "Check PostgreSQL server version and connection status"
- "Verify if pg_stat_statements and pg_stat_monitor extensions are installed"

**get_active_connections**
- "Show all current active database connections"
- "Monitor current sessions and their running queries"

**get_postgresql_config**
- "Show PostgreSQL configuration parameter for shared_buffers"
- "Find all memory-related configuration settings"

### 🗄️ Structure Exploration Examples

**get_database_list**
- "List all databases with their owners and sizes"
- "Show database encoding and connection limits"

**get_table_list**
- "List all tables in the default database:"
- "Show tables in specific database"

**get_user_list**
- "Display all database users with their permissions"
- "Show superuser status and account limitations for all users"

### ⚡ Performance Monitoring Examples

**get_pg_stat_statements_top_queries**
- "Show top 10 slowest queries"
- "Analyze slow queries in specific database"

**get_pg_stat_monitor_recent_queries**
- "Monitor recent 15 queries with detailed stats"
- "Track recent queries in testdb database"

**get_index_usage_stats**
- "Analyze index usage in default database:"
- "Check index efficiency in specific database"

### 💾 Capacity Management Examples

**get_database_size_info**
- "Show disk usage for all databases sorted by size"
- "Calculate total storage consumption across all databases"

**get_table_size_info**
- "Analyze table sizes in public schema"
- "Check table sizes in specific database schema"

**get_vacuum_analyze_stats**
- "Review VACUUM and ANALYZE history for all tables"
- "Check maintenance status in specific database"

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

### 🔧 Advanced Usage Examples

**Multi-Database Analysis**
- "Compare table sizes across databases"
- "Monitor performance across multiple databases using database_name parameter"

**Configuration Troubleshooting**
- "Search for connection-related settings"
- "Find logging configuration"
- "Check specific parameter"

**Performance Deep Dive**
- "Identify unused indexes with zero scans (look for 'Never used' entries)"
- "Find tables needing maintenance (check last_vacuum dates)"

This MCP server provides comprehensive PostgreSQL monitoring and management capabilities while maintaining read-only safety and providing detailed insights for database administration.
