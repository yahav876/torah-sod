"""
Torah text service with caching and database integration
"""
import re
import os
import hashlib
import json
import time
import threading
from flask import current_app
from app.models.database import db, TorahVerse, SearchResult
from app.shared.metrics import torah_verses_indexed, track_cache_hit
import structlog

logger = structlog.get_logger()


class TorahService:
    """Service for managing Torah text and verses."""
    
    _instance = None
    _lock = threading.RLock()
    _initialized = False
    _torah_lines = None
    _torah_text = None
    _verse_cache = {}
    _search_cache = {}  # In-memory search cache
    _max_cache_size = 1000
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(TorahService, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def initialize(cls):
        """Initialize the Torah service."""
        instance = cls()
        with cls._lock:
            if not cls._initialized:
                instance._load_torah_text()
                instance._index_verses_if_needed()
                cls._initialized = True
    
    def _load_torah_text(self):
        """Load Torah text from file with preloading optimization."""
        try:
            torah_file = current_app.config['TORAH_FILE']
            if not os.path.exists(torah_file):
                logger.error("torah_file_not_found", path=torah_file)
                return
            
            # Pre-read entire file for better performance
            with open(torah_file, encoding="utf-8") as f:
                content = f.read()
                self._torah_lines = content.splitlines(keepends=True)
                self._torah_text = content
            
            # Pre-process for faster searching
            self._normalized_lines = [self._normalize_text(line) for line in self._torah_lines]
            
            logger.info("torah_text_loaded", lines=len(self._torah_lines), 
                       size_mb=len(content) / 1024 / 1024)
        except Exception as e:
            logger.error("torah_load_error", error=str(e), exc_info=True)
    
    def _index_verses_if_needed(self):
        """Index Torah verses in database if not already done."""
        try:
            verse_count = TorahVerse.query.count()
            torah_verses_indexed.set(verse_count)
            
            if verse_count > 0:
                logger.info("torah_already_indexed", verses=verse_count)
                return
            
            logger.info("starting_torah_indexing")
            self._index_torah_verses()
            
        except Exception as e:
            logger.error("indexing_check_error", error=str(e))
    
    def _index_torah_verses(self):
        """Index Torah verses into the database."""
        if not self._torah_lines:
            return
        
        book = chapter = None
        verses_to_insert = []
        
        for line in self._torah_lines:
            line = line.strip()
            
            # Check for book/chapter headers
            match = re.match(r'^(\S+)\s+\u05e4\u05e8\u05e7-([\u05d0-\u05ea]+)$', line)
            if match:
                book, chapter = match.groups()
                continue
            
            # Find verses
            verses = re.findall(r'\{[^}]+\}[^{}]+', line)
            for verse in verses:
                verse_num_match = re.search(r'\{([^}]+)\}', verse)
                if not verse_num_match:
                    continue
                
                verse_num = verse_num_match.group(1)
                clean_verse = re.sub(r'\{[^}]+\}', '', verse).strip()
                
                if book and chapter and clean_verse:
                    verse_obj = TorahVerse(
                        book=book,
                        chapter=chapter,
                        verse=verse_num,
                        text=clean_verse,
                        text_normalized=self._normalize_text(clean_verse),
                        word_count=len(clean_verse.split())
                    )
                    verses_to_insert.append(verse_obj)
        
        # Bulk insert
        if verses_to_insert:
            try:
                db.session.bulk_save_objects(verses_to_insert)
                db.session.commit()
                torah_verses_indexed.set(len(verses_to_insert))
                logger.info("torah_verses_indexed", count=len(verses_to_insert))
            except Exception as e:
                db.session.rollback()
                logger.error("indexing_error", error=str(e), exc_info=True)
    
    def _normalize_text(self, text):
        """Normalize Hebrew text for searching."""
        # Remove vowels and cantillation marks
        normalized = re.sub(r'[\u0591-\u05C7]', '', text)
        # Normalize final letters
        final_to_regular = {'ך': 'כ', 'ם': 'מ', 'ן': 'נ', 'ף': 'פ', 'ץ': 'צ'}
        for final, regular in final_to_regular.items():
            normalized = normalized.replace(final, regular)
        return normalized
    
    def get_torah_lines(self):
        """Get Torah lines."""
        return self._torah_lines or []
    
    def get_torah_text(self):
        """Get full Torah text."""
        return self._torah_text or ""
    
    def search_verses(self, phrase, limit=1000):
        """Search for verses containing the phrase."""
        try:
            normalized_phrase = self._normalize_text(phrase)
            
            # Try to find in database
            verses = TorahVerse.query.filter(
                TorahVerse.text_normalized.contains(normalized_phrase)
            ).limit(limit).all()
            
            return [verse.to_dict() for verse in verses]
            
        except Exception as e:
            logger.error("verse_search_error", error=str(e), exc_info=True)
            return []
    
    def get_cached_result(self, search_phrase):
        """Get cached search result with memory-first approach."""
        try:
            # Check in-memory cache first (fastest)
            if search_phrase in self._search_cache:
                track_cache_hit('memory')
                return self._search_cache[search_phrase]
            
            # Create hash of search phrase
            search_hash = hashlib.sha256(search_phrase.encode()).hexdigest()
            
            # Look for cached result in database
            cached = SearchResult.query.filter_by(search_hash=search_hash).first()
            
            if cached:
                # Update hit count and last accessed
                cached.hit_count += 1
                cached.last_accessed = db.func.now()
                db.session.commit()
                
                result = json.loads(cached.results_json)
                
                # Store in memory cache for next time
                self._add_to_memory_cache(search_phrase, result)
                
                track_cache_hit('database')
                return result
            
            return None
            
        except Exception as e:
            logger.error("cache_lookup_error", error=str(e))
            return None
    
    def _add_to_memory_cache(self, search_phrase, result):
        """Add result to in-memory cache with size limit."""
        if len(self._search_cache) >= self._max_cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._search_cache))
            del self._search_cache[oldest_key]
        
        self._search_cache[search_phrase] = result
    
    def cache_result(self, search_phrase, results, search_time):
        """Cache search results."""
        try:
            search_hash = hashlib.sha256(search_phrase.encode()).hexdigest()
            
            # Check if already exists
            existing = SearchResult.query.filter_by(search_hash=search_hash).first()
            if existing:
                return
            
            # Store new result
            cached_result = SearchResult(
                search_phrase=search_phrase,
                search_hash=search_hash,
                results_json=json.dumps(results),
                total_variants=results.get('total_variants', 0),
                search_time=search_time
            )
            
            db.session.add(cached_result)
            db.session.commit()
            
            logger.info("search_result_cached", phrase=search_phrase)
            
        except Exception as e:
            db.session.rollback()
            logger.error("cache_store_error", error=str(e))


def normalize_hebrew_text(text):
    """Normalize Hebrew text for searching (standalone function for imports)."""
    # Remove vowels and cantillation marks
    normalized = re.sub(r'[\u0591-\u05C7]', '', text)
    # Normalize final letters
    final_to_regular = {'ך': 'כ', 'ם': 'מ', 'ן': 'נ', 'ף': 'פ', 'ץ': 'צ'}
    for final, regular in final_to_regular.items():
        normalized = normalized.replace(final, regular)
    return normalized
