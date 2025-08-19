#!/bin/bash
set -euo pipefail

# Run MCP Inspector with published package from PyPI
cd "$(dirname "$0")/.."

echo "🔍 Starting MCP Inspector with published package..."
echo "📦 Package: MCP-NAME"

# Check if package name has been customized
if grep -q "MCP-NAME" pyproject.toml; then
    echo "⚠️  Warning: Package name 'MCP-NAME' hasn't been customized."
    echo "   Run ./scripts/rename-template.sh first to customize the package."
    echo ""
fi

echo "🚀 Launching MCP Inspector with uvx..."

npx -y @modelcontextprotocol/inspector \
  -- uvx MCP-NAME
