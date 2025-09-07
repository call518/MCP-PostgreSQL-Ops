#!/bin/bash
set -eo pipefail

# Run MCP Inspector with published package from PyPI
cd "$(dirname "$0")/.."

echo "🔍 Starting MCP Inspector with published package..."
echo "📦 Package: mcp-postgresql-ops"

# Check if package name has been customized
if grep -q "mcp-postgresql-ops" pyproject.toml; then
    echo "⚠️  Warning: Package name 'mcp-postgresql-ops' hasn't been customized."
    echo "   Run ./scripts/rename-template.sh first to customize the package."
    echo ""
fi

echo "🚀 Launching MCP Inspector with uvx..."

npx -y @modelcontextprotocol/inspector \
  -- uvx mcp-postgresql-ops
