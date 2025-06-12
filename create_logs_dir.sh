#!/bin/bash

# Create logs directory structure
mkdir -p logs/nginx
mkdir -p logs/redis
chmod -R 777 logs  # Ensure Docker containers can write to the logs directory

echo "Logs directory structure created successfully."
echo "Logs will be stored in:"
echo "  - ./logs/torah-search.log (Main application logs)"
echo "  - ./logs/celery-worker.log (Celery worker logs)"
echo "  - ./logs/nginx/ (Nginx logs)"
echo "  - ./logs/redis/ (Redis logs)"
