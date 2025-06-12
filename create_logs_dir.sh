#!/bin/bash

# Create logs directory structure
mkdir -p logs/nginx
mkdir -p logs/redis

# Create log files if they don't exist
touch logs/torah-search.log
touch logs/celery-worker.log

# Set permissions to ensure Docker containers can write to the logs
chmod -R 777 logs
chmod 666 logs/torah-search.log
chmod 666 logs/celery-worker.log

echo "Logs directory structure created successfully."
echo "Logs will be stored in:"
echo "  - ./logs/torah-search.log (Main application logs)"
echo "  - ./logs/celery-worker.log (Celery worker logs)"
echo "  - ./logs/nginx/ (Nginx logs)"
echo "  - ./logs/redis/ (Redis logs)"
