#!/bin/bash
# Startup script for the Torah Search application

echo "🚀 Starting Optimized Torah Search Application"
echo "============================================"

# Check if running with Docker or locally
if command -v docker-compose &> /dev/null; then
    echo "Docker Compose detected. Starting with Docker..."
    echo ""
    
    # Use the docker-compose file
    if [ -f "docker-compose.aws.yml" ]; then
        # Create logs directory structure
        echo "Creating logs directory structure..."
        ./create_logs_dir.sh
        
        echo "Starting all services..."
        docker-compose -f docker-compose.aws.yml up -d
        
        echo ""
        echo "Waiting for services to be ready..."
        sleep 10
        
        echo ""
        echo "Services status:"
        docker-compose -f docker-compose.aws.yml ps
        
        echo ""
        echo "✅ Application is running!"
        echo ""
        echo "Access points:"
        echo "- Web Interface: http://localhost"
        echo "- API Endpoint: http://localhost/api/search"
        echo "- Health Check: http://localhost/health"
        echo "- Statistics: http://localhost/api/stats"
        echo ""
        echo "To view logs: docker-compose -f docker-compose.aws.yml logs -f"
        echo "To stop: docker-compose -f docker-compose.aws.yml down"
    else
        echo "❌ Error: docker-compose.aws.yml not found!"
        exit 1
    fi
else
    echo "Docker Compose not found. Starting locally..."
    echo ""
    echo "⚠️  Note: For full optimization benefits, use Docker Compose!"
    echo ""
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Error: Python 3 is required!"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    echo "Activating virtual environment..."
    source venv/bin/activate
    
    # Install dependencies
    echo "Installing dependencies..."
    pip install -r requirements.txt
    
    # Initialize database
    echo "Initializing database..."
    python migrations/init_db.py
    
    # Start the application
    echo ""
    echo "Starting application..."
    echo ""
    
    # Export environment variables
    export FLASK_ENV=development
    export DATABASE_URL=sqlite:///torah_search.db
    
    # Run the application
    python app.py
fi
