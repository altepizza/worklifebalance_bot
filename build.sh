#!/bin/bash

# Build and push the image to GitHub Container Registry

docker build -t ghcr.io/altepizza/worklifebalance_bot:latest .
docker push ghcr.io/altepizza/worklifebalance_bot:latest
