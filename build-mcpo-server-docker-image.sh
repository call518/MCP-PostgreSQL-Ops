#!/bin/bash
set -eo pipefail

Dockerfile_PATH="./Dockerfile.MCPO-Proxy"
IMAGE_NAME="call518/mcpo-proxy-postgresql-ops"

echo "=== Building Docker image Name: ${IMAGE_NAME} ==="

VERSION="1.0.3"
TAGs="latest"

# Build once with version tag
docker build -t ${IMAGE_NAME}:${VERSION} -f ${Dockerfile_PATH} .

# Tag as latest
for TAG in ${TAGs}
do
    docker tag ${IMAGE_NAME}:${VERSION} ${IMAGE_NAME}:${TAG}
done

echo

read -p "Do you want to push the images to Docker Hub? (y/N): " answer
if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
    echo "Pushing version ${VERSION}..."
    docker push ${IMAGE_NAME}:${VERSION}

    echo "Pushing latest tag..."
    for TAG in ${TAGs}
    do
        docker push ${IMAGE_NAME}:${TAG}
    done
fi
