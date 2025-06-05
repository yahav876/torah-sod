#!/bin/bash
git pull
docker compose -f docker-compose.aws.yml down
docker compose -f docker-compose.aws.yml up -d --build