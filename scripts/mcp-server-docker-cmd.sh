#!/bin/bash
set -euo pipefail

# 어디서 실행하든지, 스크립트 위치의 상위 경로에 있는 .env 파일 export 로드
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd -P)"
env_file="${script_dir%/*}/.env"
if [[ -f "$env_file" ]]; then
  set -o allexport
  . "$env_file"
  set +o allexport
else
  echo "error: .env not found: $env_file" >&2
  return 1 2>/dev/null || exit 1
fi

echo "Starting MCP server with:"
echo "  PYTHONPATH: ${PYTHONPATH}"
echo "  FASTMCP_TYPE: ${FASTMCP_TYPE}"
echo "  FASTMCP_HOST: ${FASTMCP_HOST}"
echo "  FASTMCP_PORT: ${FASTMCP_PORT}"
echo "  MCP_LOG_LEVEL: ${MCP_LOG_LEVEL}"
echo "  PGSQL_VERSION: ${PGSQL_VERSION}"
echo "  POSTGRES_HOST: ${POSTGRES_HOST}"
echo "  POSTGRES_PORT: ${POSTGRES_PORT}"
echo "  POSTGRES_USER: ${POSTGRES_USER}"
echo "  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}"
echo "  POSTGRES_DB: ${POSTGRES_DB}"

python -m mcp_postgresql_ops.mcp_main --type ${FASTMCP_TYPE} --host ${FASTMCP_HOST} --port ${FASTMCP_PORT}
