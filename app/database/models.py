"""
Database models for Torah Search
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, Optional

Base = declarative_base()


class SearchResult(Base):
    """Search results storage for caching and analytics"""
    __tablename__ = 'search_results'
    
    id = Column(Integer, primary_key=True)
    query_hash = Column(String(64), nullable=False, index=True)
    original_phrase = Column(Text, nullable=False)
    variant = Column(Text, nullable=False)
    mapping_sources = Column(JSON, nullable=False)  # List of mapping method names
    book = Column(String(50), nullable=False)
    chapter = Column(String(10), nullable=False)
    verse = Column(String(10), nullable=False)
    matched_text = Column(Text, nullable=False)
    relevance_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=func.now())
    
    # Composite indexes for performance
    __table_args__ = (
        Index('idx_query_hash_relevance', 'query_hash', 'relevance_score'),
        Index('idx_book_chapter_verse', 'book', 'chapter', 'verse'),
        Index('idx_variant_sources', 'variant', 'mapping_sources'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'variant': self.variant,
            'sources': self.mapping_sources,
            'location': {
                'book': self.book,
                'chapter': self.chapter,
                'verse': self.verse,
                'text': self.matched_text
            },
            'relevance_score': self.relevance_score
        }


class SearchCache(Base):
    """Cache for search results"""
    __tablename__ = 'search_cache'
    
    id = Column(Integer, primary_key=True)
    query_hash = Column(String(64), unique=True, nullable=False, index=True)
    original_phrase = Column(Text, nullable=False)
    search_results = Column(JSON, nullable=False)  # Serialized search results
    total_variants = Column(Integer, default=0)
    search_time_seconds = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False, index=True)
    hit_count = Column(Integer, default=0)
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return datetime.utcnow() > self.expires_at
    
    def increment_hit_count(self) -> None:
        """Increment cache hit counter"""
        self.hit_count += 1


class UserQuery(Base):
    """Track user queries for analytics and optimization"""
    __tablename__ = 'user_queries'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(128), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    original_phrase = Column(Text, nullable=False)
    query_hash = Column(String(64), nullable=False, index=True)
    word_count = Column(Integer, nullable=False)
    character_count = Column(Integer, nullable=False)
    processing_type = Column(String(20), nullable=False)  # 'sync', 'async', 'cached'
    search_time_seconds = Column(Float, nullable=True)
    results_count = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False)  # 'success', 'error', 'timeout'
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), index=True)
    
    # Indexes for analytics queries
    __table_args__ = (
        Index('idx_status_created', 'status', 'created_at'),
        Index('idx_processing_type_created', 'processing_type', 'created_at'),
        Index('idx_word_count_performance', 'word_count', 'search_time_seconds'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for analytics"""
        return {
            'id': self.id,
            'phrase': self.original_phrase,
            'word_count': self.word_count,
            'processing_type': self.processing_type,
            'search_time': self.search_time_seconds,
            'results_count': self.results_count,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class TorahIndex(Base):
    """Elasticsearch-synchronized Torah text index"""
    __tablename__ = 'torah_index'
    
    id = Column(Integer, primary_key=True)
    book = Column(String(50), nullable=False, index=True)
    chapter = Column(String(10), nullable=False)
    verse = Column(String(10), nullable=False)
    text = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=False)  # For exact matching
    search_vector = Column(Text, nullable=True)  # For full-text search
    word_count = Column(Integer, nullable=False)
    character_count = Column(Integer, nullable=False)
    indexed_at = Column(DateTime, default=func.now())
    
    # Full-text search index
    __table_args__ = (
        Index('idx_book_chapter_verse_unique', 'book', 'chapter', 'verse', unique=True),
        Index('idx_fulltext_search', 'normalized_text'),
        Index('idx_word_count', 'word_count'),
    )
    
    def to_elasticsearch_doc(self) -> Dict[str, Any]:
        """Convert to Elasticsearch document format"""
        return {
            'book': self.book,
            'chapter': self.chapter,
            'verse': self.verse,
            'text': self.text,
            'normalized_text': self.normalized_text,
            'word_count': self.word_count,
            'character_count': self.character_count,
            'location': f"{self.book} {self.chapter}:{self.verse}",
            'indexed_at': self.indexed_at.isoformat() if self.indexed_at else None
        }


class PerformanceStats(Base):
    """Performance statistics tracking"""
    __tablename__ = 'performance_stats'
    
    id = Column(Integer, primary_key=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    tags = Column(JSON, nullable=True)  # Additional metadata
    timestamp = Column(DateTime, default=func.now(), index=True)
    
    # Time-series indexing
    __table_args__ = (
        Index('idx_metric_time', 'metric_name', 'timestamp'),
    )
