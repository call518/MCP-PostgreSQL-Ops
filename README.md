# MCP PostgreSQL Operations Server

A professional MCP server for PostgreSQL database server operations, monitoring, and management. Provides advanced performance analysis capabilities using `pg_stat_statements` and `pg_stat_monitor` extensions.

## Features

- ✅ **PostgreSQL Monitoring**: Performance analysis based on pg_stat_statements and pg_stat_monitor
- ✅ **Structure Exploration**: Database, table, and user listing
- ✅ **Performance Analysis**: Slow query identification and index usage analysis
- ✅ **Capacity Management**: Database and table size analysis
- ✅ **Configuration Retrieval**: PostgreSQL configuration parameter verification
- ✅ **Safe Read-Only**: All operations are read-only and safe

## Quick start

1) Environment Setup

```bash
# Check and modify .env file
cp .env.example .env
# Configure PostgreSQL connection information:
# POSTGRES_HOST=host.docker.internal
# POSTGRES_PORT=5432
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=your-password
# POSTGRES_DB=postgres
```

2) Install Dependencies

```bash
uv venv --python 3.11 --seed
uv sync
```

3) Run Server

```bash
# Development & Testing (recommended)
./scripts/run-mcp-inspector-local.sh

# Direct execution for debugging
python -m src.mcp_postgresql_ops.mcp_main --log-level DEBUG
```

## Available Tools

### 📊 Server Information & Status
- `get_server_info` - PostgreSQL server information and extension status
- `get_active_connections` - Current active connections and session information
- `get_postgresql_config` - PostgreSQL configuration parameters with keyword search capability

### 🗄️ Structure Exploration
- `get_database_list` - All database list and size information
- `get_table_list` - Table list and size information
- `get_user_list` - Database user list and permissions

### ⚡ Performance Monitoring
- `get_pg_stat_statements_top_queries` - Slow query analysis based on performance statistics
- `get_pg_stat_monitor_recent_queries` - Real-time query monitoring
- `get_index_usage_stats` - Index usage rate and efficiency analysis

### 💾 Capacity Management
- `get_database_size_info` - Database capacity analysis
- `get_table_size_info` - Table and index size analysis
- `get_vacuum_analyze_stats` - VACUUM/ANALYZE status and history

## Usage Examples

### Claude Desktop Integration
Add to your Claude Desktop configuration file:

```json
{
  "mcpServers": {
    "postgresql-ops": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.mcp_postgresql_ops.mcp_main"],
      "cwd": "/path/to/MCP-PostgreSQL-Ops",
      "env": {
        "POSTGRES_HOST": "host.docker.internal",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "your-password",
        "POSTGRES_DB": "postgres"
      }
    }
  }
}
```

### Command Line Usage

```bash
# HTTP mode for testing
python -m src.mcp_postgresql_ops.mcp_main \
  --type streamable-http \
  --host 127.0.0.1 \
  --port 8080 \
  --log-level DEBUG
```

### Configuration Search Examples

The `get_postgresql_config` tool supports flexible parameter searching:

```bash
# Search for specific parameter
"Show the shared_buffers configuration"

# Search by keyword for related parameters
"Find all memory-related configuration settings"
"Show logging configuration parameters" 
"Display connection-related settings"
"Find all timeout configurations"

# Browse all configurations
"Show all PostgreSQL configuration parameters"
```

## Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `MCP_LOG_LEVEL` | Logging level | `INFO` | `DEBUG` |
| `FASTMCP_TYPE` | Transport type | `stdio` | `streamable-http` |
| `FASTMCP_HOST` | HTTP host address | `127.0.0.1` | `0.0.0.0` |
| `FASTMCP_PORT` | HTTP port number | `8080` | `9090` |
| `POSTGRES_HOST` | PostgreSQL host | `localhost` | `host.docker.internal` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` | `5432` |
| `POSTGRES_USER` | PostgreSQL user | `postgres` | `your-user` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `` | `your-password` |
| `POSTGRES_DB` | PostgreSQL database | `postgres` | `your-db` |

## Prerequisites

### Required PostgreSQL Extensions

For full functionality, your PostgreSQL instance should have these extensions installed:

```sql
-- Query performance statistics (required)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Advanced monitoring (optional)
CREATE EXTENSION IF NOT EXISTS pg_stat_monitor;
```

### Minimum Requirements
- PostgreSQL 12+ (tested with PostgreSQL 16)
- Python 3.11
- Network access to PostgreSQL server
- Read permissions on system catalogs

## Sample Prompts

### 🔍 Server Health Check
- "Check PostgreSQL server status"
- "Verify if extensions are installed"
- "Show current active connection count"

### 📊 Performance Analysis
- "Show top 20 slowest queries"
- "Find unused indexes"
- "Analyze recent query activity"

### 💾 Capacity Management
- "Check database sizes"
- "Find largest tables"
- "Show tables that need VACUUM"

## Troubleshooting

### Connection Issues
1. Check PostgreSQL server status
2. Verify connection parameters in `.env` file
3. Ensure network connectivity
4. Check user permissions

### Extension Errors
1. Run `get_server_info` to check extension status
2. Install missing extensions:
   ```sql
   CREATE EXTENSION pg_stat_statements;
   CREATE EXTENSION pg_stat_monitor;
   ```
3. Restart PostgreSQL if needed

### Performance Issues
1. Use `limit` parameters to reduce result size
2. Run monitoring during off-peak hours
3. Check database load before running analysis

## Development

### Testing & Development

```bash
# Test with MCP Inspector
./scripts/run-mcp-inspector-local.sh

# Direct execution for debugging
python -m src.mcp_postgresql_ops.mcp_main --log-level DEBUG

# Run tests (if you add any)
uv run pytest
```

## Security Notes

- All tools are **read-only** - no data modification capabilities
- Sensitive information (passwords) are masked in outputs
- No direct SQL execution - only predefined queries
- Follows principle of least privilege

