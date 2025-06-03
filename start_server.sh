#!/bin/bash

# Torah Search Application Startup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔍 Starting Torah Search Application...${NC}"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed.${NC}"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    echo -e "${RED}❌ pip is required but not available.${NC}"
    exit 1
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    python3 -m pip install -r requirements.txt
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}📝 Creating .env file from example...${NC}"
    cp .env.example .env
    echo -e "${RED}⚠️  Please edit .env file with your configuration before running in production!${NC}"
fi

# Check if Torah file exists
if [ ! -f "torah.txt" ]; then
    echo -e "${RED}❌ Error: torah.txt file not found!${NC}"
    echo -e "${YELLOW}Please ensure the Torah text file is in the project directory.${NC}"
    exit 1
fi

echo -e "${GREEN}📚 Torah file found with $(wc -l < torah.txt) lines${NC}"

# Start the application
echo -e "${GREEN}🚀 Starting application...${NC}"

# Check command line arguments
if [ "$1" == "dev" ]; then
    echo -e "${YELLOW}🔧 Starting in development mode...${NC}"
    python3 app_web.py
elif [ "$1" == "prod" ]; then
    echo -e "${YELLOW}🏭 Starting in production mode with Gunicorn...${NC}"
    if command -v gunicorn &> /dev/null; then
        gunicorn -c gunicorn.conf.py wsgi:app
    else
        echo -e "${RED}❌ Gunicorn not found. Installing...${NC}"
        python3 -m pip install gunicorn
        gunicorn -c gunicorn.conf.py wsgi:app
    fi
elif [ "$1" == "docker" ]; then
    echo -e "${YELLOW}🐳 Starting with Docker Compose...${NC}"
    if command -v docker-compose &> /dev/null; then
        docker-compose up --build -d
        echo -e "${GREEN}✅ Application started! Access at: http://localhost:8080${NC}"
    else
        echo -e "${RED}❌ Docker Compose not found.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Usage: $0 [dev|prod|docker]${NC}"
    echo -e "${YELLOW}  dev    - Start development server${NC}"
    echo -e "${YELLOW}  prod   - Start production server with Gunicorn${NC}"
    echo -e "${YELLOW}  docker - Start with Docker Compose${NC}"
    echo -e "${YELLOW}Starting development server by default...${NC}"
    python3 app_web.py
fi
