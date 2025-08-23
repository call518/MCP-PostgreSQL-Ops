# MCP Server for PostgreSQL Operations and Database Monitoring

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Deploy to PyPI with tag](https://github.com/call518/MCP-PostgreSQL-Ops/actions/workflows/pypi-publish.yml/badge.svg)](https://github.com/call518/MCP-PostgreSQL-Ops/actions/workflows/pypi-publish.yml)
[![BuyMeACoffee](https://raw.githubusercontent.com/pachadotdev/buymeacoffee-badges/main/bmc-donate-yellow.svg)](https://www.buymeacoffee.com/call518)

A professional MCP server for PostgreSQL database server operations, monitoring, and management. Most features work independently, but advanced performance analysis capabilities are available when the `pg_stat_statements` and (optionally) `pg_stat_monitor` extensions are installed.

## Features

- ✅ **Version Compatibility**: Transparent PostgreSQL version support (12-17) - automatically detects your PostgreSQL version and adapts functionality accordingly with zero configuration
- ✅ **PostgreSQL Monitoring**: Performance analysis based on pg_stat_statements and pg_stat_monitor with full backward compatibility
- ✅ **Structure Exploration**: Database, table, and user listing with detailed schema information
- ✅ **Schema Analysis**: Detailed table structure with columns, constraints, indexes, and relationships
- ✅ **Performance Analysis**: Slow query identification and index usage analysis with version-aware query optimization
- ✅ **Capacity Management**: Database and table size analysis
- ✅ **Bloat Analysis**: Table bloat monitoring and dead tuple analysis with maintenance recommendations
- ✅ **VACUUM/Autovacuum Analysis**: Comprehensive maintenance operation monitoring, effectiveness analysis, and real-time status tracking
- ✅ **Configuration Retrieval**: PostgreSQL configuration parameter verification
- ✅ **Database Performance Statistics**: Comprehensive transaction, I/O, and buffer cache analysis
- ✅ **I/O Performance Monitoring**: Version-aware I/O statistics (comprehensive on PG16+, basic on PG12-15)
- ✅ **Background Process Monitoring**: Version-aware checkpoint and background writer analysis (split on PG15+)
- ✅ **Table Statistics Monitoring**: Version-aware comprehensive table usage and maintenance statistics (enhanced vacuum tracking on PG13+)
- ✅ **Replication Monitoring**: Standby server conflict detection and replication lag analysis with version-compatible WAL status tracking
- ✅ **Function Performance Analysis**: User-defined function execution statistics
- ✅ **Query Performance Analysis**: Version-compatible pg_stat_statements integration (PG12: total_time mapping, PG13+: native columns)
- ✅ **Safe Read-Only**: All operations are read-only and safe

- 🛠️ **Easy Customization**: Simple and clean codebase makes it very easy to add new tools or customize existing ones

## Tool Usage Examples

### 📸 **[More Examples with Screenshots →](https://github.com/call518/MCP-PostgreSQL-Ops/wiki/Tool-Usage-Example)**

---

![MCP-PostgreSQL-Ops Usage Screenshot](img/screenshot-000.png)

---

![MCP-PostgreSQL-Ops Usage Screenshot](img/screenshot-004.png)

---

![MCP-PostgreSQL-Ops Usage Screenshot](img/screenshot-005.png)

---

## ⭐ Quickstart (5 minutes)

> **Note:** The `postgresql` container included in `docker-compose.yml` is intended for quickstart testing purposes only. You can connect to your own PostgreSQL instance by adjusting the environment variables as needed.

> **If you want to use your own PostgreSQL instance instead of the built-in test container:**
> - Update the target PostgreSQL connection information in your `.env` file (see POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB).
> - In `docker-compose.yml`, comment out (disable) the `postgres` and `postgres-init-extensions` containers to avoid starting the built-in test database.

### 1. Environment Setup

> **Note**: While superuser privileges provide access to all databases and system information, the MCP server also works with regular user permissions for basic monitoring tasks.

```bash
git clone https://github.com/call518/MCP-PostgreSQL-Ops.git
cd MCP-PostgreSQL-Ops

### Check and modify .env file
```bash
cp .env.example .env
```

### No need to modify defaults, but if using your own PostgreSQL server, edit below:
```bash
POSTGRES_HOST=host.docker.internal
POSTGRES_PORT=15432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeme!@34
POSTGRES_DB=ecommerce # Default connection DB. Superusers can access all DBs.
```

> ⚠️ **Important**: `PGDATA=/data/db` is configured for Docker container internal use and **must not be modified**. This variable defines PostgreSQL's data directory inside the container and changing it will break the Docker setup.
```

### 2. Start Demo Containers

```bash
# Start all containers including built-in PostgreSQL for testing
docker-compose up -d

# Alternative: If using your own PostgreSQL instance
# Comment out postgres and postgres-init-extensions services in docker-compose.yml
# Then use the custom configuration:
# docker-compose -f docker-compose.custom-db.yml up -d
```

### 3. Access to OpenWebUI

http://localhost:3003/

- The list of MCP tool features provided by `swagger` can be found in the MCPO API Docs URL.
  - e.g: `http://localhost:8003/docs`

### 4. Registering the Tool in OpenWebUI

1. logging in to OpenWebUI with an admin account
1. go to "Settings" → "Tools" from the top menu.
1. Enter the `postgresql-ops` Tool address (e.g., `http://localhost:8003/postgresql-ops`) to connect MCP Tools.
1. Setup Ollama or OpenAI.

---

## (NOTE) Sample Test Data Overview

The `create-test-data.sql` script is executed by the `postgres-init-extensions` container (defined in docker-compose.yml) on first startup, automatically generating comprehensive test databases for MCP tool testing:

| Database | Purpose | Schema & Tables | Scale |
|----------|---------|-----------------|-------|
| **ecommerce** | E-commerce system | **public**: categories, products, customers, orders, order_items | 10 categories, 500 products, 100 customers, 200 orders, 400 order items |
| **analytics** | Analytics & reporting | **public**: page_views, sales_summary | 1,000 page views, 30 sales summaries |
| **inventory** | Warehouse management | **public**: suppliers, inventory_items, purchase_orders | 10 suppliers, 100 items, 50 purchase orders |
| **hr_system** | HR management | **public**: departments, employees, payroll | 5 departments, 50 employees, 150 payroll records |

**Test users created:** `app_readonly`, `app_readwrite`, `analytics_user`, `backup_user`

**Optimized for testing:** Intentional table bloat, various indexes (used/unused), time-series data, complex relationships

---

## Tool Compatibility Matrix

> **Automatic Adaptation:** All tools work transparently across supported versions - no configuration needed!

### 🟢 **Extension-Independent Tools (No Extensions Required)**

| Tool Name | Extensions Required | PG 12 | PG 13 | PG 14 | PG 15 | PG 16 | PG 17 | System Views/Tables Used |
|-----------|-------------------|-------|-------|-------|-------|-------|-------|--------------------------|
| `get_server_info` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `version()`, `pg_extension` |
| `get_active_connections` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_stat_activity` |
| `get_postgresql_config` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_settings` |
| `get_database_list` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_database` |
| `get_table_list` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `information_schema.tables` |
| `get_table_schema_info` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `information_schema.*`, `pg_indexes` |
| `get_database_schema_info` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_namespace`, `pg_class`, `pg_proc` |
| `get_table_relationships` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `information_schema.*` (constraints) |
| `get_user_list` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_user`, `pg_roles` |
| `get_index_usage_stats` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_stat_user_indexes` |
| `get_database_size_info` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_database_size()` |
| `get_table_size_info` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_total_relation_size()` |
| `get_vacuum_analyze_stats` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_stat_user_tables` |
| `get_current_database_info` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_database`, `current_database()` |
| `get_table_bloat_analysis` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_stat_user_tables` |
| `get_database_bloat_overview` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_stat_user_tables` |
| `get_autovacuum_status` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_stat_user_tables` |
| `get_autovacuum_activity` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_stat_user_tables` |
| `get_running_vacuum_operations` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_stat_activity` |
| `get_vacuum_effectiveness_analysis` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_stat_user_tables` |
| `get_table_bloat_analysis` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_stat_user_tables` |
| `get_database_bloat_overview` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_stat_user_tables` |
| `get_lock_monitoring` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_locks`, `pg_stat_activity` |
| `get_wal_status` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_current_wal_lsn()` |
| `get_database_stats` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_stat_database` |
| `get_table_io_stats` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_statio_user_tables` |
| `get_index_io_stats` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_statio_user_indexes` |
| `get_database_conflicts_stats` | ❌ None | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `pg_stat_database_conflicts` |

### 🚀 **Version-Aware Tools (Auto-Adapting)**

| Tool Name | Extensions Required | PG 12 | PG 13 | PG 14 | PG 15 | PG 16 | PG 17 | Special Features |
|-----------|-------------------|-------|-------|-------|-------|-------|-------|------------------|
| `get_io_stats` | ❌ None | ✅ Basic | ✅ Basic | ✅ Basic | ✅ Basic | ✅ **Enhanced** | ✅ **Enhanced** | PG16+: `pg_stat_io` support |
| `get_bgwriter_stats` | ❌ None | ✅ | ✅ | ✅ | ✅ **Special** | ✅ | ✅ | PG15: Separate checkpointer stats |
| `get_replication_status` | ❌ None | ✅ Compatible | ✅ **Enhanced** | ✅ **Enhanced** | ✅ **Enhanced** | ✅ **Enhanced** | ✅ **Enhanced** | PG13+: `wal_status`, `safe_wal_size`; PG16+: enhanced WAL receiver |
| `get_all_tables_stats` | ❌ None | ✅ Compatible | ✅ **Enhanced** | ✅ **Enhanced** | ✅ **Enhanced** | ✅ **Enhanced** | ✅ **Enhanced** | PG13+: `n_ins_since_vacuum` tracking for vacuum maintenance optimization |
| `get_user_functions_stats` | ⚙️ Config Required | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Requires `track_functions=pl` |

### 🟡 **Extension-Dependent Tools (Extensions Required)**

| Tool Name | Required Extension | PG 12 | PG 13 | PG 14 | PG 15 | PG 16 | PG 17 | Notes |
|-----------|-------------------|-------|-------|-------|-------|-------|-------|-------|
| `get_pg_stat_statements_top_queries` | `pg_stat_statements` | ✅ **Compatible** | ✅ **Enhanced** | ✅ **Enhanced** | ✅ **Enhanced** | ✅ **Enhanced** | ✅ **Enhanced** | PG12: `total_time` → `total_exec_time`; PG13+: native `total_exec_time` |
| `get_pg_stat_monitor_recent_queries` | `pg_stat_monitor` | ✅ **Compatible** | ✅ **Enhanced** | ✅ **Enhanced** | ✅ **Enhanced** | ✅ **Enhanced** | ✅ **Enhanced** | PG12: `total_time` → `total_exec_time`; PG13+: native `total_exec_time` |

> **📋 PostgreSQL 18 Support**: PostgreSQL 18 is currently in beta phase and not yet supported by Percona Distribution PostgreSQL. Support will be added once PostgreSQL 18 reaches stable release and distribution support becomes available.

---

## Usage Examples

### Claude Desktop Integration
(Recommended) Add to your Claude Desktop configuration file:

```json
{
  "mcpServers": {
    "postgresql-ops": {
      "command": "uvx",
      "args": ["--python", "3.11", "mcp-postgresql-ops"],
      "env": {
        "POSTGRES_HOST": "127.0.0.1",
        "POSTGRES_PORT": "15432",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "changeme!@34",
        "POSTGRES_DB": "ecommerce"
      }
    }
  }
}
```

"Show all active connections in a clear and readable html table format."
![Claude Desktop Integration](img/screenshot-claude-desktop-airflow-connections-html.png)

"Show all relationships for customers table in ecommerce database as a Mermaid diagram."
![Claude Desktop Integration](img/screenshot-claude-desktop-mermaid-diagram.png)

(Optional) Run with Local Source:

```json
{
  "mcpServers": {
    "postgresql-ops": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.mcp_postgresql_ops.mcp_main"],
      "cwd": "/path/to/MCP-PostgreSQL-Ops",
      "env": {
        "POSTGRES_HOST": "127.0.0.1",
        "POSTGRES_PORT": "15432",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "changeme!@34",
        "POSTGRES_DB": "ecommerce"
      }
    }
  }
}
```

### Run MCP-Server as Standalon

#### /w Pypi and uvx (Recommended)

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

#### /w Local Source

```bash
# Stdio mode
PYTHONPATH=/path/to/MCP-PostgreSQL-Ops
python -m src.mcp_postgresql_ops.mcp_main \
  --type stdio

# HTTP mode
PYTHONPATH=/path/to/MCP-PostgreSQL-Ops
python -m src.mcp_postgresql_ops.mcp_main \
  --type streamable-http \
  --host 127.0.0.1 \
  --port 8080 \
  --log-level DEBUG
```

---

## Environment Variables

| Variable | Description | Default | Project Default |
|----------|-------------|---------|-----------------|
| `PYTHONPATH` | Python module search path for MCP server imports | - | `/app/src` |
| `MCP_LOG_LEVEL` | Server logging verbosity (DEBUG, INFO, WARNING, ERROR) | `INFO` | `INFO` |
| `FASTMCP_TYPE` | MCP transport protocol (stdio for CLI, streamable-http for web) | `stdio` | `streamable-http` |
| `FASTMCP_HOST` | HTTP server bind address (0.0.0.0 for all interfaces) | `127.0.0.1` | `0.0.0.0` |
| `FASTMCP_PORT` | HTTP server port for MCP communication | `8080` | `8080` |
| `PGSQL_VERSION` | PostgreSQL major version for Docker image selection | `17` | `17` |
| `PGDATA` | PostgreSQL data directory inside Docker container (**Do not modify**) | `/var/lib/postgresql/data` | `/data/db` |
| `POSTGRES_HOST` | PostgreSQL server hostname or IP address | `127.0.0.1` | `host.docker.internal` |
| `POSTGRES_PORT` | PostgreSQL server port number | `5432` | `15432` |
| `POSTGRES_USER` | PostgreSQL connection username (needs read permissions) | `postgres` | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL user password (supports special characters) | `changeme!@34` | `changeme!@34` |
| `POSTGRES_DB` | Default database name for connections | `testdb` | `ecommerce` |
| `POSTGRES_MAX_CONNECTIONS` | PostgreSQL max_connections configuration parameter | `200` | `200` |
| `DOCKER_EXTERNAL_PORT_OPENWEBUI` | Host port mapping for Open WebUI container | `8080` | `3003` |
| `DOCKER_EXTERNAL_PORT_MCP_SERVER` | Host port mapping for MCP server container | `8080` | `18003` |
| `DOCKER_EXTERNAL_PORT_MCPO_PROXY` | Host port mapping for MCPO proxy container | `8000` | `8003` |

**Note**: `POSTGRES_DB` serves as the default target database for operations when no specific database is specified. In Docker environments, if set to a non-default name, this database will be automatically created during initial PostgreSQL startup.

---

## Prerequisites

### Required PostgreSQL Extensions

> For more details, see the [## Tool Compatibility Matrix](#tool-compatibility-matrix)

**Note**: Most MCP tools work without any PostgreSQL extensions. section below. Some advanced performance analysis tools require the following extensions:

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
- PostgreSQL 12+ (tested with PostgreSQL 17)
- Python 3.11
- Network access to PostgreSQL server
- Read permissions on system catalogs

### Required PostgreSQL Configuration

**⚠️ Statistics Collection Settings**:
Some MCP tools require specific PostgreSQL configuration parameters to collect statistics. Choose one of the following configuration methods:

**Tools affected by these settings**:
- **get_user_functions_stats**: Requires `track_functions = pl` or `track_functions = all`
- **get_table_io_stats** & **get_index_io_stats**: More accurate timing with `track_io_timing = on`
- **get_database_stats**: Enhanced I/O timing with `track_io_timing = on`

**Verification**:
After applying any method, verify the settings:
```sql
SELECT name, setting, context FROM pg_settings WHERE name IN ('track_activities', 'track_counts', 'track_io_timing', 'track_functions') ORDER BY name;

       name       | setting |  context  
------------------+---------+-----------
 track_activities | on      | superuser
 track_counts     | on      | superuser
 track_functions  | pl      | superuser
 track_io_timing  | on      | superuser
(4 rows)
```

#### Method 1: postgresql.conf (Recommended for Self-Managed PostgreSQL)
Add the following to your `postgresql.conf`:

```ini
# Basic statistics collection (usually enabled by default)
track_activities = on
track_counts = on

# Required for function statistics tools
track_functions = pl    # Enables PL/pgSQL function statistics collection

# Optional but recommended for accurate I/O timing
track_io_timing = on    # Enables I/O timing statistics collection
```

Then restart PostgreSQL server.

#### Method 2: PostgreSQL Startup Parameters
For Docker or command-line PostgreSQL startup:

```bash
# Docker example
docker run -d \
  -e POSTGRES_PASSWORD=mypassword \
  postgres:17 \
  -c track_activities=on \
  -c track_counts=on \
  -c track_functions=pl \
  -c track_io_timing=on

# Direct postgres command
postgres -D /data \
  -c track_activities=on \
  -c track_counts=on \
  -c track_functions=pl \
  -c track_io_timing=on
```

#### Method 3: Dynamic Configuration (AWS RDS, Azure, GCP, Managed Services)
For managed PostgreSQL services where you cannot modify `postgresql.conf`, use SQL commands to change settings dynamically:

```sql
-- Enable basic statistics collection (usually enabled by default)
ALTER SYSTEM SET track_activities = 'on';
ALTER SYSTEM SET track_counts = 'on';

-- Enable function statistics collection (requires superuser privileges)
ALTER SYSTEM SET track_functions = 'pl';

-- Enable I/O timing statistics (optional but recommended)
ALTER SYSTEM SET track_io_timing = 'on';

-- Reload configuration without restart (run separately)
SELECT pg_reload_conf();
```

**Alternative for session-level testing**:
```sql
-- Set for current session only (temporary)
SET track_activities = 'on';
SET track_counts = 'on';
SET track_functions = 'pl';
SET track_io_timing = 'on';
```

**Note**: When using command-line tools, run each SQL statement separately to avoid transaction block errors.

---

## RDS/Aurora Compatibility

- This server is read-only and works with regular roles on RDS/Aurora. For advanced analysis enable pg_stat_statements; pg_stat_monitor is not available on managed engines.
- On RDS/Aurora, prefer DB Parameter Group over ALTER SYSTEM for persistent settings.
  ```sql
  -- Verify preload setting
  SHOW shared_preload_libraries;

  -- Enable extension in target DB
  CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

  -- Recommended visibility for monitoring
  GRANT pg_read_all_stats TO <app_user>;
  ```

---

## Example Queries

### 🟢 Extension-Independent Tools (Always Available)

- **get_server_info**
  - "Show PostgreSQL server version and extension status."
  - "Check if pg_stat_statements is installed."
- **get_active_connections**
  - "Show all active connections."
  - "List current sessions with database and user."
- **get_postgresql_config**
  - "Show all PostgreSQL configuration parameters."
  - "Find all memory-related configuration settings."
- **get_database_list**
  - "List all databases and their sizes."
  - "Show database list with owner information."
- **get_table_list**
  - "List all tables in the ecommerce database."
  - "Show table sizes in the public schema."
- **get_table_schema_info**
  - "Show detailed schema information for the customers table in ecommerce database."
  - "Get column details and constraints for products table in ecommerce database."
  - "Analyze table structure with indexes and foreign keys for orders table in sales schema of ecommerce database."
  - "Show schema overview for all tables in public schema of inventory database."
  - 📋 **Features**: Column types, constraints, indexes, foreign keys, table metadata
  - ⚠️ **Required**: `database_name` parameter must be specified
- **get_database_schema_info**
  - "Show all schemas in ecommerce database with their contents."
  - "Get detailed information about sales schema in ecommerce database."
  - "Analyze schema structure and permissions for inventory database."
  - "Show schema overview with table counts and sizes for hr_system database."
  - 📋 **Features**: Schema owners, permissions, object counts, sizes, contents
  - ⚠️ **Required**: `database_name` parameter must be specified
- **get_table_relationships**
  - "Show all relationships for customers table in ecommerce database."
  - "Analyze foreign key relationships for orders table in sales schema of ecommerce database."
  - "Get database-wide relationship overview for ecommerce database."
  - "Find all tables that reference products table in ecommerce database."
  - "Show cross-schema relationships in inventory database."
  - 📋 **Features**: Foreign key relationships (inbound/outbound), cross-schema dependencies, constraint details
  - ⚠️ **Required**: `database_name` parameter must be specified
  - 💡 **Usage**: Leave `table_name` empty for database-wide relationship analysis
- **get_user_list**
  - "List all database users and their roles."
  - "Show user permissions for a specific database."
- **get_index_usage_stats**
  - "Analyze index usage efficiency."
  - "Find unused indexes in the current database."
- **get_database_size_info**
  - "Show database capacity analysis."
  - "Find the largest databases by size."
- **get_table_size_info**
  - "Show table and index size analysis."
  - "Find largest tables in a specific schema."
- **get_vacuum_analyze_stats**
  - "Show recent VACUUM and ANALYZE operations."
  - "List tables needing VACUUM."
- **get_current_database_info**
  - "What database am I connected to?"
  - "Show current database information and connection details."
  - "Display database encoding, collation, and size information."
  - 📋 **Features**: Database name, encoding, collation, size, connection limits
  - 🔧 **PostgreSQL 12-17**: Fully compatible, no extensions required
- **get_table_bloat_analysis**
  - "Analyze table bloat in the current database."
  - "Show dead tuple ratios and bloat estimates for user_logs table pattern."
  - "Find tables with high bloat that need VACUUM maintenance."
  - "Analyze bloat in specific schema with minimum 100 dead tuples."
  - 📋 **Features**: Dead tuple ratios, bloat size estimates, VACUUM recommendations, pattern filtering
  - 🔧 **PostgreSQL 12-17**: Fully compatible, no extensions required
  - 💡 **Usage**: Extension-Independent approach using pg_stat_user_tables
- **get_database_bloat_overview**
  - "Show database-wide bloat summary by schema."
  - "Get high-level view of storage efficiency across all schemas."
  - "Identify schemas requiring maintenance attention."
  - 📋 **Features**: Schema-level aggregation, total bloat estimates, maintenance status
  - 🔧 **PostgreSQL 12-17**: Fully compatible, no extensions required
- **get_autovacuum_status**
  - "Check autovacuum configuration and trigger conditions."
  - "Show tables needing immediate autovacuum attention."
  - "Analyze autovacuum threshold percentages for public schema."
  - "Find tables approaching autovacuum trigger points."
  - 📋 **Features**: Trigger threshold analysis, urgency classification, configuration status
  - 🔧 **PostgreSQL 12-17**: Fully compatible, no extensions required
  - 💡 **Usage**: Extension-Independent autovacuum monitoring using pg_stat_user_tables
- **get_autovacuum_activity**
  - "Show autovacuum activity patterns for the last 48 hours."
  - "Monitor autovacuum execution frequency and timing."
  - "Find tables with irregular autovacuum patterns."
  - "Analyze recent autovacuum and autoanalyze history."
  - 📋 **Features**: Activity patterns, execution frequency, timing analysis
  - 🔧 **PostgreSQL 12-17**: Fully compatible, no extensions required
  - 💡 **Usage**: Historical autovacuum pattern analysis
- **get_running_vacuum_operations**
  - "Show currently running VACUUM and ANALYZE operations."
  - "Monitor active maintenance operations and their progress."
  - "Check if any VACUUM operations are blocking queries."
  - "Find long-running maintenance operations."
  - 📋 **Features**: Real-time operation status, elapsed time, impact level, process details
  - 🔧 **PostgreSQL 12-17**: Fully compatible, no extensions required
  - 💡 **Usage**: Real-time maintenance monitoring using pg_stat_activity
- **get_vacuum_effectiveness_analysis**
  - "Analyze VACUUM effectiveness and maintenance patterns."
  - "Compare manual VACUUM vs autovacuum efficiency."
  - "Find tables with suboptimal maintenance patterns."
  - "Check VACUUM frequency vs table activity ratios."
  - 📋 **Features**: Maintenance pattern analysis, effectiveness assessment, DML-to-VACUUM ratios
  - 🔧 **PostgreSQL 12-17**: Fully compatible, no extensions required
  - 💡 **Usage**: Strategic VACUUM analysis using existing statistics
- **get_table_bloat_analysis**
  - "Analyze table bloat in the public schema."
  - "Show tables with high dead tuple ratios in ecommerce database."
  - "Find tables requiring VACUUM maintenance."
  - "Check bloat for tables with more than 5000 dead tuples."
  - 📋 **Features**: Dead tuple ratios, estimated bloat size, VACUUM recommendations
  - ⚠️ **Required**: Specify `database_name` for cross-database analysis
- **get_database_bloat_overview**
  - "Show database-wide bloat summary by schema."
  - "Get bloat overview for inventory database."
  - "Identify schemas with highest bloat ratios."
  - "Database maintenance planning with bloat statistics."
  - 📋 **Features**: Schema-level aggregation, maintenance priorities, size recommendations
- **get_lock_monitoring**
  - "Show all current locks and blocked sessions."
  - "Show only blocked sessions with granted=false filter."
  - "Monitor locks by specific user with username filter."
  - "Check exclusive locks with mode filter."
- **get_wal_status**
  - "Show WAL status and archiving information."
  - "Monitor WAL generation and current LSN position."
- **get_replication_status**
  - "Check replication connections and lag status."
  - "Monitor replication slots and WAL receiver status."
- **get_database_stats**
  - "Show comprehensive database performance metrics."
  - "Analyze transaction commit ratios and I/O statistics."
  - "Monitor buffer cache hit ratios and temporary file usage."
- **get_bgwriter_stats**
  - "Analyze checkpoint performance and timing."
  - "Show me checkpoint performance."
  - "Show background writer efficiency statistics."
  - "Monitor buffer allocation and fsync patterns."
- **get_user_functions_stats**
  - "Analyze user-defined function performance."
  - "Show function call counts and execution times."
  - "Identify performance bottlenecks in custom functions."
  - ⚠️ **Requires**: `track_functions = pl` in postgresql.conf
- **get_table_io_stats**
  - "Analyze table I/O performance and buffer hit ratios."
  - "Identify tables with poor buffer cache performance."
  - "Monitor TOAST table I/O statistics."
  - 💡 **Enhanced with**: `track_io_timing = on` for accurate timing
- **get_index_io_stats**
  - "Show index I/O performance and buffer efficiency."
  - "Identify indexes causing excessive disk I/O."
  - "Monitor index cache-friendliness patterns."
  - 💡 **Enhanced with**: `track_io_timing = on` for accurate timing
- **get_database_conflicts_stats**
  - "Check replication conflicts on standby servers."
  - "Analyze conflict types and resolution statistics."
  - "Monitor standby server query cancellation patterns."
  - "Monitor WAL generation and current LSN position."
- **get_replication_status**
  - "Check replication connections and lag status."
  - "Monitor replication slots and WAL receiver status."

### 🚀 Version-Aware Tools (Auto-Adapting)

- **get_io_stats** (New!)
  - "Show comprehensive I/O statistics." (PostgreSQL 16+ provides detailed breakdown)
  - "Analyze I/O statistics."
  - "Analyze buffer cache efficiency and I/O timing."
  - "Monitor I/O patterns by backend type and context."
  - 📈 **PG16+**: Full pg_stat_io with timing, backend types, and contexts
  - 📊 **PG12-15**: Basic pg_statio_* fallback with buffer hit ratios
- **get_bgwriter_stats** (Enhanced!)
  - "Show background writer and checkpoint performance."
  - 📈 **PG15**: Separate checkpointer and bgwriter statistics (unique feature)
  - 📊 **PG12-14, 16+**: Combined bgwriter stats (includes checkpointer data)
- **get_server_info** (Enhanced!)
  - "Show server version and compatibility features."
  - "Check server compatibility."
  - "Check what MCP tools are available on this PostgreSQL version."
  - "Displays feature availability matrix and upgrade recommendations."
- **get_all_tables_stats** (Enhanced!)
  - "Show comprehensive statistics for all tables." (version-compatible for PG12-17)
  - "Include system tables with include_system=true parameter."
  - "Analyze table access patterns and maintenance needs."
  - 📈 **PG13+**: Tracks insertions since vacuum (`n_ins_since_vacuum`) for optimal maintenance scheduling
  - 📊 **PG12**: Compatible mode with NULL for unsupported columns

### 🟡 Extension-Dependent Tools

- **get_pg_stat_statements_top_queries** (Requires `pg_stat_statements`)
  - "Show top 10 slowest queries."
  - "Analyze slow queries in the inventory database."
  - 📈 **Version-Compatible**: PG12 uses `total_time` → `total_exec_time` mapping; PG13+ uses native columns
  - 💡 **Cross-Version**: Automatically adapts query structure for PostgreSQL 12-17 compatibility
- **get_pg_stat_monitor_recent_queries** (Optional, uses `pg_stat_monitor`)
  - "Show recent queries in real time."
  - "Monitor query activity for the last 5 minutes."
  - 📈 **Version-Compatible**: PG12 uses `total_time` → `total_exec_time` mapping; PG13+ uses native columns
  - 💡 **Cross-Version**: Automatically adapts query structure for PostgreSQL 12-17 compatibility

**💡 Pro Tip**: All tools support multi-database operations using the `database_name` parameter. This allows PostgreSQL superusers to analyze and monitor multiple databases from a single MCP server instance.

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

### Configuration Issues
1. **"No data found" for function statistics**: Check `track_functions` setting
   ```sql
   SHOW track_functions;  -- Should be 'pl' or 'all'
   ```
   
   **Quick fix for managed services (AWS RDS, etc.)**:
   ```sql
   ALTER SYSTEM SET track_functions = 'pl';
   SELECT pg_reload_conf();
   ```

2. **Missing I/O timing data**: Enable timing collection
   ```sql
   SHOW track_io_timing;  -- Should be 'on'
   ```
   
   **Quick fix**:
   ```sql
   ALTER SYSTEM SET track_io_timing = 'on';
   SELECT pg_reload_conf();
   ```

3. **Apply configuration changes**:
   - **Self-managed**: Add settings to `postgresql.conf` and restart server
   - **Managed services**: Use `ALTER SYSTEM SET` + `SELECT pg_reload_conf()`
   - **Temporary testing**: Use `SET parameter = value` for current session
   - Generate some database activity to populate statistics

### Performance Issues
1. Use `limit` parameters to reduce result size
2. Run monitoring during off-peak hours
3. Check database load before running analysis

### Version Compatibility Issues

> For more details, see the [## Tool Compatibility Matrix](#tool-compatibility-matrix)

1. **Run compatibility check first**:
   ```bash
   # "Use get_server_info to check version and available features"
   ```

2. **Understanding feature availability**:
   - **PostgreSQL 16-17**: All features available
   - **PostgreSQL 15+**: Separate checkpointer stats
   - **PostgreSQL 14+**: Parallel query tracking
   - **PostgreSQL 12-13**: Core functionality only

3. **If a tool shows "Not Available"**:
   - Feature requires newer PostgreSQL version
   - Tool will automatically use best available alternative
   - Consider upgrading PostgreSQL for enhanced monitoring

---

## Development

### Testing & Development

```bash
# Test with MCP Inspector
./scripts/run-mcp-inspector-local.sh

# Direct execution for debugging
python -m src.mcp_postgresql_ops.mcp_main --log-level DEBUG

# Test version compatibility (requires different PostgreSQL versions)
# Modify POSTGRES_HOST in .env to point to different versions

# Run tests (if you add any)
uv run pytest
```

### Version Compatibility Testing

The MCP server automatically adapts to PostgreSQL versions 12-17. To test across versions:

1. **Set up test databases**: Different PostgreSQL versions (12, 14, 15, 16, 17)
2. **Run compatibility tests**: Point to each version and verify tool behavior
3. **Check feature detection**: Ensure proper version detection and feature availability
4. **Verify fallback behavior**: Confirm graceful degradation on older versions

---

## Security Notes

- All tools are **read-only** - no data modification capabilities
- Sensitive information (passwords) are masked in outputs
- No direct SQL execution - only predefined queries
- Follows principle of least privilege

---

## Contributing

🤝 **Got ideas? Found bugs? Want to add cool features?**

We're always excited to welcome new contributors! Whether you're fixing a typo, adding a new monitoring tool, or improving documentation - every contribution makes this project better.

**Ways to contribute:**
- 🐛 Report issues or bugs
- 💡 Suggest new PostgreSQL monitoring features
- 📝 Improve documentation 
- 🚀 Submit pull requests
- ⭐ Star the repo if you find it useful!

**Pro tip:** The codebase is designed to be super friendly for adding new tools. Check out the existing `@mcp.tool()` functions in `mcp_main.py`.

---

## Example: MCPO Swagger APIs

> [MCPO Swagger URL] http://localhost:8003/postgresql-ops/docs

![MCPO Swagger APIs](img/screenshot-swagger-api.png)

---

## License
Freely use, modify, and distribute under the **MIT License**.

---

## ⭐ Other Projects

**Other MCP servers by the same author:**

- [MCP-Ambari-API](https://github.com/call518/MCP-Ambari-API)
- [MCP-Airflow-API](https://github.com/call518/MCP-Airflow-API)
- [LogSentinelAI - LLB-Based Log Analyzer](https://github.com/call518/LogSentinelAI)