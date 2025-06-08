#!/bin/bash
echo "Updating code from git repository..."
git pull

echo "Stopping and removing all containers..."
docker compose -f docker-compose.aws.yml down
docker stop torah-sod-torah-search-1 || true
docker rm torah-sod-torah-search-1 || true

echo "Building and starting new containers with no cache to apply all changes..."
docker compose -f docker-compose.aws.yml build --no-cache
docker compose -f docker-compose.aws.yml up -d

echo "Update complete! Running containers:"
docker ps
