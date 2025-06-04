"""
Optimized search service with caching and parallel processing
"""
import re
import itertools
import ahocorasick
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from flask import current_app
from app.services.torah_service import TorahService
from app.shared.metrics import track_search_metrics, search_phrase_length, results_found
from app.services.letter_mappings import LetterMappings
import structlog

logger = structlog.get_logger()


class SearchService:
    """Service for performing Torah searches."""
    
    def __init__(self):
        self.torah_service = TorahService()
        self.letter_mappings = LetterMappings()
        self.executor = None
    
    def __enter__(self):
        self.executor = ThreadPoolExecutor(
            max_workers=current_app.config.get('MAX_WORKERS', 4)
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.executor:
            self.executor.shutdown(wait=True)
    
    @track_search_metrics('web')
    def search(self, phrase, use_cache=True):
        """Perform search with caching and metrics."""
        try:
            # Validate input
            if not phrase or len(phrase) > current_app.config['MAX_PHRASE_LENGTH']:
                return {
                    'error': 'Invalid phrase length',
                    'success': False,
                    'results': []
                }
            
            # Track phrase length
            search_phrase_length.observe(len(phrase))
            
            # Check cache
            if use_cache:
                cached_result = self.torah_service.get_cached_result(phrase)
                if cached_result:
                    logger.info("cache_hit", phrase=phrase)
                    return cached_result
            
            # Perform search
            start_time = time.time()
            results = self._perform_search(phrase)
            search_time = time.time() - start_time
            
            # Format response
            response = {
                'input_phrase': phrase,
                'results': results['results'],
                'total_variants': results['total_variants'],
                'search_time': round(search_time, 3),
                'success': True
            }
            
            # Cache result
            if use_cache and search_time < 300:  # Only cache if search took less than 5 minutes
                self.torah_service.cache_result(phrase, response, search_time)
            
            return response
            
        except Exception as e:
            logger.error("search_error", phrase=phrase, error=str(e), exc_info=True)
            return {
                'error': str(e),
                'success': False,
                'results': []
            }
    
    def _perform_search(self, phrase):
        """Perform the actual search."""
        # Get Torah text
        lines = self.torah_service.get_torah_lines()
        full_text = self.torah_service.get_torah_text()
        
        if not lines:
            raise ValueError("Torah text not loaded")
        
        # Generate variants and build automaton
        variant_tuples = self.letter_mappings.generate_all_variants(phrase)
        automaton = self._build_automaton(variant_tuples)
        
        # Perform parallel search
        grouped_matches = self._search_parallel(
            automaton, lines, len(phrase.replace(' ', '')), phrase, full_text
        )
        
        # Format results
        results = []
        max_results = current_app.config['MAX_RESULTS']
        
        for (variant, sources), locations in grouped_matches.items():
            if len(results) >= max_results:
                break
            
            results.append({
                'variant': variant,
                'sources': list(sources),
                'locations': locations[:100]  # Limit locations per variant
            })
        
        # Track results count
        results_found.observe(len(grouped_matches))
        
        return {
            'results': results,
            'total_variants': len(grouped_matches)
        }
    
    def _build_automaton(self, variant_tuples):
        """Build Aho-Corasick automaton for efficient pattern matching."""
        automaton = ahocorasick.Automaton()
        for variant, source in variant_tuples:
            automaton.add_word(variant, (variant, source))
        automaton.make_automaton()
        return automaton
    
    def _search_parallel(self, automaton, lines, phrase_length, input_phrase, full_text):
        """Perform parallel search across Torah text with AWS optimization."""
        grouped_matches = defaultdict(list)
        
        # Optimize for t3.2xlarge (8 vCPU, 32GB RAM)
        num_workers = current_app.config['MAX_WORKERS']  # Use full worker capacity
        batch_multiplier = current_app.config.get('BATCH_SIZE_MULTIPLIER', 150)
        batch_size = max(batch_multiplier, len(lines) // num_workers)
        batches = [lines[i:i+batch_size] for i in range(0, len(lines), batch_size)]
        
        # Use context manager for thread pool
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            # Submit all batch searches
            future_to_batch = {
                executor.submit(
                    self._search_batch,
                    batch, automaton, phrase_length, input_phrase, full_text
                ): batch_idx
                for batch_idx, batch in enumerate(batches)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_batch):
                try:
                    batch_results = future.result(timeout=30)
                    
                    for variant, source, book, chapter, verse_num, marked_text in batch_results:
                        grouped_matches[(variant, source)].append({
                            'book': book,
                            'chapter': chapter,
                            'verse': verse_num,
                            'text': marked_text
                        })
                        
                except Exception as e:
                    batch_idx = future_to_batch[future]
                    logger.error("batch_search_error", batch=batch_idx, error=str(e))
        
        return grouped_matches
    
    def _search_batch(self, batch_lines, automaton, phrase_length, input_phrase, full_text):
        """Search for patterns in a batch of lines."""
        results = []
        book = chapter = None
        
        for line in batch_lines:
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
                verse_num = verse_num_match.group(1) if verse_num_match else "?"
                clean_verse = re.sub(r'\{[^}]+\}', '', verse).strip()
                
                if len(clean_verse) < phrase_length:
                    continue
                
                # Search for patterns
                for end_index, (variant, source) in automaton.iter(clean_verse):
                    start_index = end_index - len(variant) + 1
                    matched_text = clean_verse[start_index:end_index + 1]
                    
                    if matched_text == variant and variant != input_phrase:
                        if variant in full_text:
                            marked_text = clean_verse.replace(variant, f'[{variant}]', 1)
                            results.append((variant, tuple(source), book, chapter, verse_num, marked_text))
                            break
        
        return results
