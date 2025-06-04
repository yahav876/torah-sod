"""
Background tasks for indexing Torah text
"""
import os
import re
from app.tasks.celery_app import celery
from app.models.database import db, TorahVerse
from app.services.torah_service import normalize_hebrew_text
import structlog

logger = structlog.get_logger()


@celery.task(bind=True)
def index_torah_text(self):
    """
    Background task to index Torah text into database.
    This task reads the Torah text file and indexes each verse.
    """
    try:
        torah_file = os.environ.get('TORAH_FILE', '/app/torah.txt')
        
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100})
        
        # Read Torah file
        with open(torah_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        logger.info(f"Starting Torah indexing: {total_lines} lines to process")
        
        # Track current book and chapter
        current_book = None
        current_chapter = None
        verses_created = 0
        
        # Patterns for parsing
        book_pattern = re.compile(r'^ספר\s+(.+)$')
        chapter_pattern = re.compile(r'^(.+)\s+פרק\s+(.+)$')
        verse_pattern = re.compile(r'^(.+):(.+)$')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Update progress
            if i % 100 == 0:
                progress = int((i / total_lines) * 100)
                self.update_state(state='PROGRESS', meta={'current': progress, 'total': 100})
            
            # Check for book header
            book_match = book_pattern.match(line)
            if book_match:
                current_book = book_match.group(1).strip()
                continue
            
            # Check for chapter header
            chapter_match = chapter_pattern.match(line)
            if chapter_match:
                current_chapter = chapter_match.group(2).strip()
                continue
            
            # Check for verse
            verse_match = verse_pattern.match(line)
            if verse_match and current_book and current_chapter:
                verse_num = verse_match.group(1).strip()
                verse_text = verse_match.group(2).strip()
                
                # Create verse entry
                verse = TorahVerse(
                    book=current_book,
                    chapter=current_chapter,
                    verse=verse_num,
                    text=verse_text,
                    text_normalized=normalize_hebrew_text(verse_text),
                    word_count=len(verse_text.split())
                )
                
                db.session.add(verse)
                verses_created += 1
                
                # Commit in batches
                if verses_created % 100 == 0:
                    db.session.commit()
                    logger.info(f"Indexed {verses_created} verses...")
        
        # Final commit
        db.session.commit()
        
        logger.info(f"Torah indexing completed: {verses_created} verses indexed")
        
        return {
            'status': 'completed',
            'verses_indexed': verses_created
        }
        
    except Exception as e:
        logger.error(f"Error indexing Torah: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise
