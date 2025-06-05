"""
WSGI entry point for production deployment
"""
import os
from app.app_factory import create_app

# Create application
app = create_app(os.environ.get('FLASK_ENV', 'production'))

if __name__ == "__main__":
    app.run()
