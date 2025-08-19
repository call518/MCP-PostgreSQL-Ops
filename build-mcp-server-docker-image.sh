#!/bin/bash
set -euo pipefail

Dockerfile_PATH="./Dockerfile.MCP-Server"
IMAGE_NAME="call518/mcp-server-postgresql-ops"

echo "=== Building Docker image Name: ${IMAGE_NAME} ==="

# CUSTOM_TAG="${1:-latest}"
TAGs="
1.0.0
latest
"

for TAG in ${TAGs}
do
    docker build -t ${IMAGE_NAME}:${TAG} -f ${Dockerfile_PATH} .
done

echo

read -p "Do you want to push the images to Docker Hub? (y/N): " answer
if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
    for TAG in ${TAGs}
    do
        docker push ${IMAGE_NAME}:${TAG}
    done
fi
