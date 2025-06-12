"""
Script to add test statistics data to the database
"""
import os
import sys
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import SearchStatistics, SearchResult

def add_test_data():
    """Add test statistics data to the database."""
    # Get database URL from environment or use default
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    
    # Create engine and session
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Add some test search statistics
        for i in range(10):
            # Create statistics for searches over the past few days
            days_ago = i % 3  # Some today, some yesterday, some day before
            timestamp = datetime.datetime.now() - datetime.timedelta(days=days_ago)
            
            stat = SearchStatistics(
                search_phrase=f"Test search {i}",
                word_count=i + 1,
                search_time=0.5 + (i * 0.1),  # Varying search times
                results_count=i * 5,
                cache_hit=(i % 2 == 0),  # Alternate between cache hit and miss
                client_ip="127.0.0.1",
                user_agent="Test Script",
                created_at=timestamp
            )
            session.add(stat)
        
        # Add some test search results (cached searches)
        for i in range(5):
            result = SearchResult(
                search_phrase=f"Cached search {i}",
                search_hash=f"hash_{i}",
                results_json='{"success": true, "results": []}',
                total_variants=i * 3,
                search_time=0.3 + (i * 0.2),
                hit_count=i + 1,
                last_accessed=datetime.datetime.now()
            )
            session.add(result)
        
        # Commit the changes
        session.commit()
        print("Added test statistics data to the database")
        
    except Exception as e:
        session.rollback()
        print(f"Error adding test data: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    add_test_data()
