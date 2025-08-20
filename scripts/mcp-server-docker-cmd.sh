#!/bin/bash
set -euo pipefail

# .env 파일 로드
ENV="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.env"
[ -f "$ENV" ] && set -a && . "$ENV" && set +a

python -m mcp_postgresql_ops.mcp_main --type ${FASTMCP_TYPE} --host ${FASTMCP_HOST} --port ${FASTMCP_PORT}
