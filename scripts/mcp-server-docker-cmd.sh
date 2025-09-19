#!/bin/bash
set -eo pipefail

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

echo "Starting OpenStack MCP server with environment variables from .env:"
echo "================================"

# Read and display all environment variables from .env file
while IFS='=' read -r key value || [[ -n "$key" ]]; do
  # Skip empty lines and comments
  [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
  
  # Remove leading/trailing whitespace from key
  key=$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  
  # Get the actual environment variable value
  actual_value=$(printenv "$key" 2>/dev/null || echo "")
  
  # Display the variable (mask sensitive values)
  if [[ "$key" =~ PASSWORD|SECRET|KEY ]]; then
    echo "  $key: ***MASKED***"
  else
    echo "  $key: ${actual_value}"
  fi
done < "$env_file"

echo "================================"

python -m mcp_postgresql_ops --type ${FASTMCP_TYPE} --host ${FASTMCP_HOST} --port ${FASTMCP_PORT}
