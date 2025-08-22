# MCP PostgreSQL Operations Server - AI Coding Agent Instructions

## Architecture Overview

This is a **Model Context Protocol (MCP) server** built with **FastMCP** that provides PostgreSQL database monitoring and operations through natural language queries. The server acts as a safe, read-only bridge between AI assistants and PostgreSQL databases.

### Core Components
- **`mcp_main.py`**: Main MCP server with 24+ `@mcp.tool()` decorated functions
- **`functions.py`**: Database connection layer using `asyncpg` with multi-database support
- **`version_compat.py`**: PostgreSQL 12-18 version detection and adaptive feature handling
- **`prompt_template.md`**: Comprehensive prompt definitions loaded via `@mcp.prompt()` decorators
- **Docker stack**: PostgreSQL + MCP server + MCPO proxy + Open WebUI integration

### Key Patterns

**Multi-Database Architecture**: All tools accept optional `database_name` parameter to target specific databases while maintaining a default connection database from `POSTGRES_DB` env var.

**Extension Dependencies**: Core functionality requires `pg_stat_statements` extension; `pg_stat_monitor` is optional. Always check extension availability with `check_extension_exists()` before using related tools.

**Version-Aware Tools**: Use `version_compat.py` for PostgreSQL 12-18 compatibility. Tools auto-adapt features based on detected version.

**Tool Structure**: Each MCP tool follows this pattern:
```python
@mcp.tool()
async def get_something(limit: int = 20, database_name: str = None) -> str:
    """Detailed docstring with [Tool Purpose], [Exact Functionality], [Required Use Cases], [Strictly Prohibited Use Cases]"""
    try:
        # Validate inputs (limit constraints: max 1-100)
        # Check extension dependencies if needed
        # Execute queries via functions.py
        # Return formatted table data
    except Exception as e:
        logger.error(f"Failed to...: {e}")
        return f"Error: {str(e)}"
```

**Schema Analysis Tools**: New extension-independent tools for database schema analysis:
- `get_table_schema_info()`: Detailed table structure with columns, constraints, indexes
- `get_database_schema_info()`: Complete database schema overview with metadata
- `get_table_relationships()`: Foreign key relationships and cross-schema dependencies

## Development Workflows

### Local Development
```bash
# Primary development command - loads .env, starts MCP Inspector
./scripts/run-mcp-inspector-local.sh

# Direct execution for debugging with custom log levels
python -m src.mcp_postgresql_ops.mcp_main --log-level DEBUG --type streamable-http
```

### Docker Development
```bash
# Full stack with PostgreSQL + test data
docker-compose up -d

# Test data generation (creates 4 databases with 83k+ records)
./scripts/create-test-data.sh
```

### Environment Configuration
- Copy `.env.example` to `.env` and modify connection parameters
- **Critical**: `POSTGRES_DB` serves dual purpose - default connection target AND Docker database creation name
- Use `host.docker.internal` for `POSTGRES_HOST` when connecting from containers to host PostgreSQL

## Code Conventions

### Database Connection Pattern
```python
# Multi-database support - database parameter overrides POSTGRES_CONFIG default
async def get_db_connection(database: str = None) -> asyncpg.Connection:
    config = POSTGRES_CONFIG.copy()
    if database:
        config["database"] = database  # Override default
    return await asyncpg.connect(**config)
```

### Error Handling
- All MCP tools must return `str` (never raise exceptions to MCP layer)
- Log errors with `logger.error()` then return user-friendly error messages
- Mask sensitive information in connection info with `sanitize_connection_info()`

### Query Formatting
- Use `format_table_data(results, title)` for consistent table output
- Apply `format_bytes()` and `format_duration()` for human-readable values
- Enforce limit constraints: `limit = max(1, min(limit, 100))`

### Tool Compatibility Matrix
When adding new tools, **must** update the compatibility matrix in `README.md`:
- Classify as Extension-Independent, Version-Aware, or Extension-Dependent
- Document PostgreSQL version support (12-18)
- List system views/tables used
- Update tool count statistics

## Project-Specific Integrations

### Prompt Template System
The server loads prompts from `prompt_template.md` using a custom parsing system:
- `@mcp.prompt("prompt_template_full")` - complete template
- `@mcp.prompt("prompt_template_headings")` - section list only
- `get_prompt_template(section="specific_section")` - targeted content

### Docker Multi-Service Architecture
- **postgres**: Percona PostgreSQL 16 with pre-configured extensions
- **postgres-init-extensions**: One-shot container that installs extensions and creates comprehensive test data
- **mcp-server**: Main MCP server container
- **mcpo-proxy**: HTTP proxy for web-based MCP clients
- **open-webui**: Web interface for testing

### Critical Dependencies
```python
# Required for all database operations
import asyncpg  # Not psycopg2 - uses asyncpg exclusively

# MCP framework
from fastmcp import FastMCP

# Extension checks are mandatory for performance tools
await check_extension_exists("pg_stat_statements")
```

## Testing Strategy

### Test Data Generation
- Run `./scripts/create-test-data.sh` to create 4 realistic databases:
  - `ecommerce`: E-commerce with products, orders, customers (~9k records)
  - `analytics`: Web analytics and sales data (~59k records) 
  - `inventory`: Warehouse management (~3k records)
  - `hr_system`: Employee and payroll data (~12k records)

### Natural Language Testing
Test tools with realistic prompts - never use function names directly:
- ✅ "Show me the slowest queries"
- ❌ "Run get_pg_stat_statements_top_queries"

### Configuration Files
- `mcp-config.json.stdio`: Standard CLI integration
- `mcp-config.json.http`: HTTP mode for web clients
- Both must have matching port configurations with `docker-compose.yml`

## Common Pitfalls

1. **Database Parameter Confusion**: `POSTGRES_DB` is the default connection database, not a constraint on which databases can be accessed
2. **Extension Assumptions**: Always check `pg_stat_statements`/`pg_stat_monitor` availability before using performance tools
3. **Port Misalignment**: `FASTMCP_PORT`, Docker external port, and MCP config files must all match
4. **Environment Loading**: Use `scripts/run-mcp-inspector-local.sh` which properly loads `.env` - direct Python execution won't load environment
5. **Query Limits**: All tools enforce 1-100 limits for performance; don't assume unlimited results
6. **asyncpg Parameter Binding**: Use `$1, $2, ...` format, not `%s` - all SQL queries must use asyncpg-compatible parameter binding
