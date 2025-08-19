# MCP Server Template

Opinionated uv-based Python template to bootstrap an MCP server fast. One script updates project/package names and metadata so you can focus on core MCP tools.

## Features

- ✅ **Flexible Transport**: Support for both `stdio` and `streamable-http` transports
- ✅ **Comprehensive Logging**: Configurable logging levels with structured output  
- ✅ **Environment Configuration**: Support for environment variables and CLI arguments
- ✅ **Error Handling**: Robust error handling and configuration validation
- ✅ **Development Tools**: Built-in scripts for easy development and testing

## Quick start

1) Initialize template (once)

```bash
./scripts/rename-template.sh \
  --name "my-mcp-server" \
  --author "Your Name" \
  --email "you@example.com" \
  --version "0.1.0" \
  --desc "My awesome MCP server"
```

This script:
- Creates dist name (hyphen) and package name (underscore) automatically
- Renames src/MCP_NAME -> src/<pkg_name> and replaces placeholders (MCP_NAME, MCP-NAME, your-server-name)
- Regenerates pyproject.toml (metadata, src layout, console script entrypoint)
- Updates run scripts and workflow URLs
- Optionally runs uv sync (omit with --no-sync)

2) Prepare environment

```bash
uv venv
uv sync
```

3) Configure server (optional)

```bash
# Copy environment template
cp .env.example .env

# Edit configuration as needed
# MCP_LOG_LEVEL=INFO
# FASTMCP_TYPE=stdio
# FASTMCP_HOST=127.0.0.1
# FASTMCP_PORT=8080
```

4) Run server

```bash
# Development & Testing (recommended)
./scripts/run-mcp-inspector-local.sh

# Direct execution for debugging
python -m src.MCP_NAME.mcp_main --log-level DEBUG

# For Claude Desktop integration, add to config:
# {
#   "mcpServers": {
#     "your-server-name": {
#       "command": "uv",
#       "args": ["run", "python", "-m", "src.MCP_NAME.mcp_main"]
#     }
#   }
# }
```

## Server Configuration

### Command Line Options

```bash
python -m src.MCP_NAME.mcp_main --help

Options:
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Logging level
  --type {stdio,streamable-http}
                        Transport type (default: stdio)
  --host HOST          Host address for HTTP transport (default: 127.0.0.1)
  --port PORT          Port number for HTTP transport (default: 8080)
```

### Environment Variables

| Variable | Description | Default | Usage |
|----------|-------------|---------|--------|
| `MCP_LOG_LEVEL` | Logging level | `INFO` | Development debugging |
| `FASTMCP_TYPE` | Transport type | `stdio` | Rarely needed to change |
| `FASTMCP_HOST` | HTTP host address | `127.0.0.1` | For HTTP mode only |
| `FASTMCP_PORT` | HTTP port number | `8080` | For HTTP mode only |

**Note**: MCP servers typically use `stdio` transport. HTTP mode is mainly for testing and development.

## Project structure

```
.
├── main.py
├── MANIFEST.in
├── pyproject.toml
├── README.md
├── uv.lock
├── .env.example                    # Environment configuration template
├── docs/
├── scripts/
│   ├── rename-template.sh          # one-shot rename/customize
│   ├── run-mcp-inspector-local.sh  # development & testing (recommended)
│   └── run-mcp-inspector-pypi.sh   # test published package
└── src/
    └── MCP_NAME/                   # will be renamed to snake_case package
        ├── __init__.py
        ├── functions.py            # utility/helper functions with logging
        ├── mcp_main.py             # FastMCP server with transport config
        └── prompt_template.md
```

## Development

### Adding Tools

Edit `src/<pkg_name>/mcp_main.py` to add new MCP tools:

```python
@mcp.tool()
async def my_tool(param: str) -> str:
    """
    [도구 역할]: Tool description
    [정확한 기능]: What it does
    [필수 사용 상황]: When to use it
    """
    logger.info(f"Tool called with param: {param}")
    return f"Result: {param}"
```

### Helper Functions

Add utility functions to `src/<pkg_name>/functions.py`:

```python
async def my_helper_function(data: dict) -> str:
    """Helper function with logging support"""
    logger.debug(f"Processing data: {data}")
    # Implementation here
    return result
```

## Usage Examples

### Development & Testing
```bash
# Best way to test your MCP server
./scripts/run-mcp-inspector-local.sh

# Debug with verbose logging
MCP_LOG_LEVEL=DEBUG ./scripts/run-mcp-inspector-local.sh

# Direct execution for quick testing
python -m src.MCP_NAME.mcp_main --log-level DEBUG
```

### Claude Desktop Integration
Add to your Claude Desktop configuration file:

```json
{
  "mcpServers": {
    "your-server-name": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.MCP_NAME.mcp_main"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

### HTTP Mode (Advanced)
For special testing scenarios only:

```bash
# Run HTTP server for testing
python -m src.MCP_NAME.mcp_main \
  --type streamable-http \
  --host 127.0.0.1 \
  --port 8080 \
  --log-level DEBUG
```

### Testing & Development

```bash
# Test with MCP Inspector
./scripts/run-mcp-inspector-local.sh

# Direct execution for debugging
python -m src.MCP_NAME.mcp_main --log-level DEBUG

# Run tests (if you add any)
uv run pytest
```

## Logging

The server provides structured logging with configurable levels:

```
2024-08-19 10:30:15 - mcp_main - INFO - Starting MCP server with stdio transport
2024-08-19 10:30:15 - mcp_main - INFO - Log level set via CLI to INFO
2024-08-19 10:30:16 - functions - DEBUG - Fetching data from source: example.com
```

## Notes

- The script replaces MCP_NAME (underscore), MCP-NAME (hyphen), and your-server-name (display name)
- Configuration validation ensures proper setup before server start
- If you need to rename again, revert changes or re-clone and re-run
- A backup `pyproject.toml.bak` is created when overwriting pyproject
