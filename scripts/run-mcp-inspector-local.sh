#!/bin/bash
set -euo pipefail

# Run MCP Inspector with local source using uv
cd "$(dirname "$0")/.."

echo "🔍 Starting MCP Inspector with PostgreSQL Operations server..."
echo "📁 Working directory: $(pwd)"

# Load environment variables if .env exists
if [ -f ".env" ]; then
    echo "📄 Loading environment from .env file"
    set -o allexport
    source .env
    set +o allexport
fi

# Set default log level for development
export MCP_LOG_LEVEL=${MCP_LOG_LEVEL:-INFO}

echo "🚀 Launching MCP Inspector..."
echo "   Log Level: $MCP_LOG_LEVEL"
echo "   PostgreSQL Host: ${POSTGRES_HOST:-localhost}:${POSTGRES_PORT:-5432}"

npx -y @modelcontextprotocol/inspector \
  -- uv run python -m src.mcp_postgresql_ops.mcp_main
