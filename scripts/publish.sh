#!/bin/bash

# TODO: move this process to an external Vana-only location

# Typically you will want to run it like this: ./scripts/publish.sh -t satori or ./scripts/publish.sh
# This will build and push IMAGE:satori or IMAGE:latest to the Docker Hub registry.

source "$(dirname "$0")/env.sh"

IMAGE=${IMAGE:-validator}
TAG=${TAG:-latest}

parse_args() {
    while getopts "i:t:h" opt; do
        case $opt in
            i) IMAGE=$OPTARG ;;
            t) TAG=$OPTARG ;;
            h) echo "Usage: $0 [-i image] [-t tag]"; exit ;;
            \?) echo "Invalid option: -$OPTARG. Use -h for help." >&2; exit 1 ;;
        esac
    done
}
parse_args "$@"

IMAGE_TAG="${IMAGE}:${TAG}"

docker build -f Dockerfile.validator -t "$IMAGE_TAG" .
docker push "$IMAGE_TAG"
# Optionally run the image locally:
#docker run --rm -it \
#  -e OD_NODESERVER_EXTERNAL_IP=peregrine \
#  -e OD_NODESERVER_EXTERNAL_PORT=5870 \
#  -e OD_NODESERVER_PORT=7000 \
#  -p 5870:7000 \
#  "$IMAGE_TAG"
