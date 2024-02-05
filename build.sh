#!/bin/bash

# Build and push the image to GitHub Container Registry

docker buildx build --platform=linux/amd64 -t ghcr.io/altepizza/worklifebalance_bot:latest .
docker push ghcr.io/altepizza/worklifebalance_bot:latest
