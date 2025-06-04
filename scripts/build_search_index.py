#!/usr/bin/env python3
"""
Build high-performance search index for Torah text
This script creates word-level indexes for lightning-fast searches
"""
import sys
import os
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.app_factory import create_app
from app.models.database import db, TorahVerse, TorahWord
from app.services.indexed_search_service import build_word_index, normalize_word
import structlog

logger = structlog.get_logger()


def main():
    """Build the search index."""
    print("🔍 Torah Search Index Builder")
    print("=" * 50)
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        # Check if verses exist
        verse_count = TorahVerse.query.count()
        print(f"📚 Found {verse_count} Torah verses in database")
        
        if verse_count == 0:
            print("❌ No Torah verses found. Please run Torah indexing first.")
            print("💡 Run: python scripts/index_torah.py")
            return 1
        
        # Check current word index
        word_count = TorahWord.query.count()
        print(f"📝 Current word index: {word_count} words")
        
        if word_count > 0:
            response = input("⚠️  Word index already exists. Rebuild? (y/N): ")
            if response.lower() != 'y':
                print("✅ Keeping existing index")
                return 0
        
        print("\n🚀 Building word index...")
        start_time = time.time()
        
        try:
            # Build the index
            words_indexed = build_word_index()
            
            build_time = time.time() - start_time
            
            print(f"✅ Index built successfully!")
            print(f"📊 Statistics:")
            print(f"   - Words indexed: {words_indexed:,}")
            print(f"   - Build time: {build_time:.2f} seconds")
            print(f"   - Words per second: {words_indexed/build_time:,.0f}")
            
            # Test the index
            print("\n🧪 Testing search performance...")
            test_search_performance(app)
            
            print("\n🎉 Search index is ready for lightning-fast searches!")
            
        except Exception as e:
            print(f"❌ Error building index: {e}")
            logger.error("index_build_error", error=str(e), exc_info=True)
            return 1
    
    return 0


def test_search_performance(app):
    """Test the search performance with sample queries."""
    from app.services.indexed_search_service import IndexedSearchService
    
    test_phrases = [
        "אלהים",           # Single word
        "בראשית ברא",      # Two words  
        "ויאמר אלהים",     # Common phrase
    ]
    
    search_service = IndexedSearchService()
    
    for phrase in test_phrases:
        try:
            start_time = time.time()
            result = search_service.search(phrase, use_cache=False)
            search_time = time.time() - start_time
            
            if result['success']:
                print(f"   ✅ '{phrase}': {search_time*1000:.1f}ms, {result['total_variants']} variants")
            else:
                print(f"   ❌ '{phrase}': Failed - {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ '{phrase}': Error - {e}")


if __name__ == "__main__":
    exit(main())
