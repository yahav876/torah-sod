"""
Database models and initialization
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
Base = declarative_base()


class TorahVerse(db.Model):
    """Model for individual Torah verses with full-text search indexing."""
    __tablename__ = 'torah_verses'
    
    id = db.Column(db.Integer, primary_key=True)
    book = db.Column(db.String(50), nullable=False, index=True)
    chapter = db.Column(db.String(20), nullable=False, index=True)
    verse = db.Column(db.String(20), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    text_normalized = db.Column(db.Text, nullable=False)  # For search optimization
    word_count = db.Column(db.Integer, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    words = db.relationship('TorahWord', backref='verse', lazy='dynamic', cascade='all, delete-orphan')
    
    # Composite indexes for faster searches
    __table_args__ = (
        Index('idx_book_chapter_verse', 'book', 'chapter', 'verse'),
        Index('idx_text_search', 'text_normalized'),
        Index('idx_word_count', 'word_count'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'book': self.book,
            'chapter': self.chapter,
            'verse': self.verse,
            'text': self.text,
            'word_count': self.word_count
        }


class TorahWord(db.Model):
    """Model for individual words with position tracking for ultra-fast phrase searches."""
    __tablename__ = 'torah_words'
    
    id = db.Column(db.Integer, primary_key=True)
    verse_id = db.Column(db.Integer, db.ForeignKey('torah_verses.id'), nullable=False, index=True)
    word_original = db.Column(db.String(200), nullable=False)
    word_normalized = db.Column(db.String(200), nullable=False, index=True)
    word_position = db.Column(db.Integer, nullable=False)  # Position within verse
    word_length = db.Column(db.Integer, nullable=False)
    
    # Advanced indexes for lightning-fast searches
    __table_args__ = (
        Index('idx_word_normalized_verse', 'word_normalized', 'verse_id'),
        Index('idx_verse_position', 'verse_id', 'word_position'),
        Index('idx_normalized_prefix', db.text('word_normalized varchar_pattern_ops')),  # For LIKE queries
        Index('idx_word_search_combo', 'word_normalized', 'verse_id', 'word_position'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'verse_id': self.verse_id,
            'word_original': self.word_original,
            'word_normalized': self.word_normalized,
            'position': self.word_position,
            'length': self.word_length
        }


class TorahPhrase(db.Model):
    """Model for pre-computed phrase searches (for commonly searched phrases)."""
    __tablename__ = 'torah_phrases'
    
    id = db.Column(db.Integer, primary_key=True)
    phrase_normalized = db.Column(db.String(500), nullable=False, index=True)
    phrase_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    word_count = db.Column(db.Integer, nullable=False)
    occurrences_json = db.Column(db.Text)  # JSON array of verse locations
    search_count = db.Column(db.Integer, default=1)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_occurrences(self):
        """Get occurrences as Python list."""
        if self.occurrences_json:
            import json
            return json.loads(self.occurrences_json)
        return []
    
    def set_occurrences(self, occurrences):
        """Set occurrences from Python list."""
        import json
        self.occurrences_json = json.dumps(occurrences)


class SearchResult(db.Model):
    """Model for caching search results."""
    __tablename__ = 'search_results'
    
    id = db.Column(db.Integer, primary_key=True)
    search_phrase = db.Column(db.String(200), nullable=False, index=True)
    search_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    results_json = db.Column(db.Text, nullable=False)  # JSON string of results
    total_variants = db.Column(db.Integer, nullable=False)
    search_time = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    hit_count = db.Column(db.Integer, default=1)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_search_phrase', 'search_phrase'),
        Index('idx_created_at', 'created_at'),
    )


class SearchJob(db.Model):
    """Model for tracking background search jobs."""
    __tablename__ = 'search_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(100), nullable=False, unique=True, index=True)
    search_phrase = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False, index=True)  # pending, running, completed, failed
    progress = db.Column(db.Integer, default=0)  # 0-100
    result_id = db.Column(db.Integer, db.ForeignKey('search_results.id'), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    client_ip = db.Column(db.String(45), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'search_phrase': self.search_phrase,
            'status': self.status,
            'progress': self.progress,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class SearchStatistics(db.Model):
    """Model for tracking search analytics."""
    __tablename__ = 'search_statistics'
    
    id = db.Column(db.Integer, primary_key=True)
    search_phrase = db.Column(db.String(200), nullable=False, index=True)
    word_count = db.Column(db.Integer, nullable=False, index=True)
    search_time = db.Column(db.Float, nullable=False)
    results_count = db.Column(db.Integer, nullable=False)
    cache_hit = db.Column(db.Boolean, default=False, index=True)
    client_ip = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_stats_created_at', 'created_at'),
        Index('idx_stats_word_count', 'word_count'),
    )


def init_db(app):
    """Initialize database with Flask app."""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if Torah verses are indexed
        verse_count = TorahVerse.query.count()
        if verse_count == 0:
            app.logger.info("Torah verses not found in database. Starting background indexing...")
            # Trigger background indexing task
            from app.tasks.index_tasks import index_torah_text
            index_torah_text.delay()
        else:
            app.logger.info(f"Torah database initialized with {verse_count} verses")
    
    return db
