[![MSeeP.ai Security Assessment Badge](https://mseep.net/pr/call518-mcp-postgresql-ops-badge.png)](https://mseep.ai/app/call518-mcp-postgresql-ops)

# MCP PostgreSQL Operations Server

A professional MCP server for PostgreSQL database server operations, monitoring, and management. Most features work independently, but advanced performance analysis capabilities are available when the `pg_stat_statements` and (optionally) `pg_stat_monitor` extensions are installed.

## Features

- ✅ **PostgreSQL Monitoring**: Performance analysis based on pg_stat_statements and pg_stat_monitor
- ✅ **Structure Exploration**: Database, table, and user listing
- ✅ **Performance Analysis**: Slow query identification and index usage analysis
- ✅ **Capacity Management**: Database and table size analysis
- ✅ **Configuration Retrieval**: PostgreSQL configuration parameter verification
- ✅ **Safe Read-Only**: All operations are read-only and safe

- 🛠️ **Easy Customization**: Simple and clean codebase makes it very easy to add new tools or customize existing ones

# Example Usage

![MCP-PostgreSQL-Ops Usage Screenshot](img/screenshot-000.png)

---

## Quick start

> **Note:** The `postgresql` container included in `docker-compose.yml` is intended for quickstart testing purposes only. You can connect to your own PostgreSQL instance by adjusting the environment variables as needed.

### 1. Environment Setup

```bash
### Check and modify .env file
cp .env.example .env

### If you use other postgresql server, configure connection information:
# POSTGRES_HOST=your-address
# POSTGRES_PORT=your-listen-port
# POSTGRES_USER=your-username
# POSTGRES_PASSWORD=your-password
# POSTGRES_DB=your-database
```

### 2. Install Dependencies

```bash
docker-compose up -d
```

### 3. Access to OpenWebUI

http://localhost:3003/

- The list of MCP tool features provided by `swagger` can be found in the MCPO API Docs URL.
  - e.g: `http://localhost:8003/docs`

### 4. Registering the Tool in OpenWebUI

1. logging in to OpenWebUI with an admin account
1. go to "Settings" → "Tools" from the top menu.
1. Enter the `postgresql-ops` Tool address (e.g., `http://localhost:8003/postgresql-ops`) to connect MCP Tools.

---


## Available Tools

### 🟡 Extension-Independent Tools (Always Available)

- `get_server_info` — PostgreSQL server information and extension status
- `get_active_connections` — Current active connections and session information
- `get_postgresql_config` — PostgreSQL configuration parameters with keyword search capability
- `get_database_list` — All database list and size information
- `get_table_list` — Table list and size information
- `get_user_list` — Database user list and permissions
- `get_index_usage_stats` — Index usage rate and efficiency analysis (uses system catalogs only)
- `get_database_size_info` — Database capacity analysis
- `get_table_size_info` — Table and index size analysis
- `get_vacuum_analyze_stats` — VACUUM/ANALYZE status and history

### 🟡 Extension-Dependent Tools

- `get_pg_stat_statements_top_queries` — Slow query analysis based on performance statistics  
  (Requires `pg_stat_statements` extension)
- `get_pg_stat_monitor_recent_queries` — Real-time query monitoring  
  (Optional, uses `pg_stat_monitor` extension if available)

---

## Usage Examples

### Claude Desktop Integration (Examples)
Add to your Claude Desktop configuration file:

```json
{
  "mcpServers": {
    "postgresql-ops": {
      "command": "uvx",
      "args": ["--python", "3.11", "mcp-postgresql-ops"],
      "env": {
        "POSTGRES_HOST": "127.0.0.1",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "passwd",
        "POSTGRES_DB": "testdb"
      }
    }
  }
}
```

![Claude Desktop Integration](img/screenshot-003.png)

Options: Run with Local Source:

```json
{
  "mcpServers": {
    "postgresql-ops": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.mcp_postgresql_ops.mcp_main"],
      "cwd": "/path/to/MCP-PostgreSQL-Ops",
      "env": {
        "POSTGRES_HOST": "127.0.0.1",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "passwd",
        "POSTGRES_DB": "testdb"
      }
    }
  }
}
```

### Command Line Usage

#### /w Local Source

```bash
# Stdio mode
python -m src.mcp_postgresql_ops.mcp_main \
  --type stdio

# HTTP mode
python -m src.mcp_postgresql_ops.mcp_main \
  --type streamable-http \
  --host 127.0.0.1 \
  --port 8080 \
  --log-level DEBUG
```

#### /w Pypi and uvx

```bash
# Stdio mode
uvx --python 3.11 mcp-postgresql-ops \
  --type stdio

# HTTP mode
uvx --python 3.11 mcp-postgresql-ops
  --type streamable-http \
  --host 127.0.0.1 \
  --port 8080 \
  --log-level DEBUG
```

---

## Environment Variables

| Variable | Description | Default | Project Default |
|----------|-------------|---------|-----------------|
| `PYTHONPATH` | Python module search path for MCP server imports | `/app/src` | `/app/src` |
| `MCP_LOG_LEVEL` | Server logging verbosity (DEBUG, INFO, WARNING, ERROR) | `INFO` | `INFO` |
| `FASTMCP_TYPE` | MCP transport protocol (stdio for CLI, streamable-http for web) | `stdio` | `streamable-http` |
| `FASTMCP_HOST` | HTTP server bind address (0.0.0.0 for all interfaces) | `127.0.0.1` | `0.0.0.0` |
| `FASTMCP_PORT` | HTTP server port for MCP communication | `8080` | `8080` |
| `PGSQL_VERSION` | PostgreSQL major version for Docker image selection | `16` | `15` |
| `POSTGRES_HOST` | PostgreSQL server hostname or IP address | `localhost` | `127.0.0.1` |
| `POSTGRES_PORT` | PostgreSQL server port number | `5432` | `15432` |
| `POSTGRES_USER` | PostgreSQL connection username (needs read permissions) | `postgres` | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL user password (supports special characters) | `` | `changeme!@34` |
| `POSTGRES_DB` | Default database name for connections | `postgres` | `mcp_postgres_ops` |
| `POSTGRES_MAX_CONNECTIONS` | PostgreSQL max_connections configuration parameter | `100` | `200` |
| `DOCKER_EXTERNAL_PORT_OPENWEBUI` | Host port mapping for Open WebUI container | `8080` | `3003` |
| `DOCKER_EXTERNAL_PORT_MCP_SERVER` | Host port mapping for MCP server container | `8080` | `18003` |
| `DOCKER_EXTERNAL_PORT_MCPO_PROXY` | Host port mapping for MCPO proxy container | `8000` | `8003` |

**Note**: `POSTGRES_DB` serves as the default target database for operations when no specific database is specified. In Docker environments, if set to a non-default name, this database will be automatically created during initial PostgreSQL startup.

---

## Prerequisites

### Required PostgreSQL Extensions

**⚠️ Note**:
Most MCP tools work without any PostgreSQL extensions.
However, advanced performance analysis tools require the following extensions:

```sql
-- Query performance statistics (required only for get_pg_stat_statements_top_queries)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Advanced monitoring (optional, used by get_pg_stat_monitor_recent_queries)
CREATE EXTENSION IF NOT EXISTS pg_stat_monitor;
```

**Quick Setup**: For new PostgreSQL installations, add to `postgresql.conf`:
```
shared_preload_libraries = 'pg_stat_statements'
```
Then restart PostgreSQL and run the CREATE EXTENSION commands above.

- `pg_stat_statements` is required only for slow query analysis tools.
- `pg_stat_monitor` is optional and used for real-time query monitoring.
- All other tools work without these extensions.

### Minimum Requirements
- PostgreSQL 12+ (tested with PostgreSQL 16)
- Python 3.11
- Network access to PostgreSQL server
- Read permissions on system catalogs

---

## Example Queries

**Server Status & Health Check**
```bash
"Check PostgreSQL server status"
"Check PostgreSQL server version and connection status" 
"Verify if extensions are installed"
"Show current active connection count"
```

**Configuration Management**
```bash
"Show the shared_buffers configuration"
"Show PostgreSQL configuration parameter for shared_buffers"
"Find all memory-related configuration settings"
"Show logging configuration parameters"
"Display connection-related settings" 
"Find all timeout configurations"
"Show all PostgreSQL configuration parameters"
```

**Performance Analysis**
```bash
"Show top 10 slowest queries"
"Show top 20 slowest queries"
"Analyze slow queries in specific database"
"Find unused indexes"
"Analyze recent query activity"
"Check index efficiency in specific database"
```

**Capacity & Structure Management**
```bash
"Check database sizes"
"Find largest tables"
"Show tables that need VACUUM"
"Check table sizes in specific database schema"
"List tables in specific database"
"Check maintenance status in specific database"
```

**💡 Pro Tip**: All tools support multi-database operations using the `database_name` parameter. This allows PostgreSQL superusers to analyze and monitor multiple databases from a single MCP server instance.

📖 **[More Useful Example Queries →](src/mcp_postgresql_ops/prompt_template.md#example-queries)**

---

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

---

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

---

## Security Notes

- All tools are **read-only** - no data modification capabilities
- Sensitive information (passwords) are masked in outputs
- No direct SQL execution - only predefined queries
- Follows principle of least privilege

