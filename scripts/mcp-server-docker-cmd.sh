#!/bin/bash
set -euo pipefail

# .env 파일 로드
ENV="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.env"
[ -f "$ENV" ] && set -a && . "$ENV" && set +a

echo "Starting MCP server with:"
echo "  FASTMCP_TYPE: ${FASTMCP_TYPE:-stdio}"
echo "  FASTMCP_HOST: ${FASTMCP_HOST:-127.0.0.1}"
echo "  FASTMCP_PORT: ${FASTMCP_PORT:-8080}"
echo "  POSTGRES_HOST: ${POSTGRES_HOST:-localhost}"
echo "  POSTGRES_PORT: ${POSTGRES_PORT:-5432}"

python -m mcp_postgresql_ops.mcp_main --type ${FASTMCP_TYPE} --host ${FASTMCP_HOST} --port ${FASTMCP_PORT}
