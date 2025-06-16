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
    def search(self, phrase, use_cache=True, partial_results_callback=None, is_memory_search=False, 
              filter_book=None, filter_chapter=None, filter_verse=None):
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
            
            # Extract filters from phrase if they exist
            # Format: "search_term book:Book chapter:X verse:Y"
            filters = {}
            words = phrase.split()
            filtered_phrase = []
            
            for word in words:
                if word.startswith('book:'):
                    filters['book'] = word[5:]
                elif word.startswith('chapter:'):
                    filters['chapter'] = word[8:]
                elif word.startswith('verse:'):
                    filters['verse'] = word[6:]
                else:
                    filtered_phrase.append(word)
            
            # Use provided filters if not extracted from phrase
            if filter_book and 'book' not in filters:
                filters['book'] = filter_book
            if filter_chapter and 'chapter' not in filters:
                filters['chapter'] = filter_chapter
            if filter_verse and 'verse' not in filters:
                filters['verse'] = filter_verse
            
            # Use the filtered phrase for search
            clean_phrase = ' '.join(filtered_phrase)
            
            # Log search parameters
            logger.info("search_with_filters", 
                       original_phrase=phrase,
                       clean_phrase=clean_phrase,
                       filters=filters,
                       is_memory_search=is_memory_search)
            
            # Check cache only if no filters
            if use_cache and not filters:
                cached_result = self.torah_service.get_cached_result(clean_phrase)
                if cached_result:
                    logger.info("cache_hit", phrase=clean_phrase)
                    return cached_result
            
            # Log that we're using the memory search approach
            logger.info("using_memory_search", phrase=clean_phrase, is_memory_search=is_memory_search)
            
            # Perform search
            start_time = time.time()
            # Pass the book filter to _perform_search if it exists
            filter_book = filters.get('book')
            results = self._perform_search(clean_phrase, partial_results_callback, is_memory_search=is_memory_search, filter_book=filter_book)
            
            # Apply filters if any
            if filters:
                filtered_results = self._apply_filters(results, filters)
                search_time = time.time() - start_time
                
                # Format response with filtered results
                response = {
                    'input_phrase': phrase,
                    'clean_phrase': clean_phrase,
                    'filters': filters,
                    'results': filtered_results['results'],
                    'total_variants': filtered_results['total_variants'],
                    'search_time': round(search_time, 3),
                    'success': True
                }
                
                return response
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
    
    def _perform_search(self, phrase, partial_results_callback=None, is_memory_search=False, filter_book=None):
        """Perform the actual search."""
        # Get Torah text, filtered by book if specified
        lines = self.torah_service.get_torah_lines(filter_book=filter_book)
        full_text = self.torah_service.get_torah_text()
        
        if not lines:
            raise ValueError("Torah text not loaded")
        
        logger.info("search_text_loaded", 
                   filter_book=filter_book, 
                   lines_count=len(lines))
        
        # Check if this is a multi-word search
        words = phrase.strip().split()
        is_multi_word = len(words) > 1
        
        # For multi-word searches where words can be anywhere in the verse
        if is_multi_word:
            logger.info("multi_word_search", 
                       phrase=phrase, 
                       word_count=len(words),
                       is_memory_search=is_memory_search)
            
            # Generate variants for each word separately
            word_variants = []
            for word in words:
                word_variant_tuples = self.letter_mappings.generate_all_variants(word)
                word_automaton = self._build_automaton(word_variant_tuples)
                word_variants.append((word, word_automaton))
            
            # Perform parallel search for multi-word phrases
            grouped_matches = self._search_parallel_multi_word(
                word_variants, lines, phrase, full_text, 
                partial_results_callback, is_memory_search
            )
        else:
            # Original single-word or exact phrase search
            variant_tuples = self.letter_mappings.generate_all_variants(phrase)
            automaton = self._build_automaton(variant_tuples)
            
            # Log the search parameters
            logger.info("search_parameters", 
                       phrase=phrase, 
                       phrase_length=len(phrase.replace(' ', '')),
                       is_memory_search=is_memory_search,
                       variant_count=len(variant_tuples))
            
            # Perform parallel search
            grouped_matches = self._search_parallel(
                automaton, lines, len(phrase.replace(' ', '')), phrase, full_text, 
                partial_results_callback, is_memory_search
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
    
    def _search_parallel(self, automaton, lines, phrase_length, input_phrase, full_text, 
                        partial_results_callback=None, is_memory_search=False):
        """Perform parallel search across Torah text with AWS optimization."""
        grouped_matches = defaultdict(list)
        
        # Check if we should use book-based parallelization
        use_book_parallel = current_app.config.get('USE_BOOK_PARALLEL_SEARCH', False)
        
        # Log the parallelization method being used
        logger.info("search_parallelization_method", 
                   use_book_parallel=use_book_parallel, 
                   max_workers=current_app.config.get('MAX_WORKERS', 4),
                   input_phrase=input_phrase,
                   is_memory_search=is_memory_search)
        
        if use_book_parallel:
            # Use book-based parallelization
            return self._search_parallel_by_books(automaton, lines, phrase_length, input_phrase, 
                                                full_text, partial_results_callback, is_memory_search)
        
        # Original line-based parallelization
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
                    batch, automaton, phrase_length, input_phrase, full_text, is_memory_search
                ): batch_idx
                for batch_idx, batch in enumerate(batches)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_batch):
                try:
                    batch_results = future.result(timeout=30)
                    
                    # Process batch results
                    batch_partial_results = []
                    
                    for variant, source, book, chapter, verse_num, marked_text in batch_results:
                        grouped_matches[(variant, source)].append({
                            'book': book,
                            'chapter': chapter,
                            'verse': verse_num,
                            'text': marked_text
                        })
                        
                        # Add to partial results
                        if variant not in [r['variant'] for r in batch_partial_results]:
                            batch_partial_results.append({
                                'variant': variant,
                                'sources': list(source)
                            })
                    
                    # Call the callback with partial results if provided
                    if partial_results_callback and batch_partial_results:
                        partial_results_callback(batch_partial_results)
                        
                except Exception as e:
                    batch_idx = future_to_batch[future]
                    logger.error("batch_search_error", batch=batch_idx, error=str(e))
        
        return grouped_matches
    
    def _search_parallel_by_books(self, automaton, lines, phrase_length, input_phrase, full_text, 
                                partial_results_callback=None, is_memory_search=False):
        """Perform parallel search across Torah text by dividing work by books."""
        grouped_matches = defaultdict(list)
        
        # Group lines by book
        book_lines = self._group_lines_by_book(lines)
        
        # Log the books found
        logger.info("parallel_search_by_books", books=list(book_lines.keys()))
        
        # Use maximum number of workers for better performance
        # Each book can use multiple workers if available
        num_workers = current_app.config['MAX_WORKERS']
        logger.info("using_workers_for_book_search", num_workers=num_workers)
        
        # Use context manager for thread pool
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            # Submit search for each book
            future_to_book = {
                executor.submit(
                    self._search_batch,
                    book_lines[book], automaton, phrase_length, input_phrase, full_text, is_memory_search
                ): book
                for book in book_lines
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_book):
                try:
                    book = future_to_book[future]
                    book_results = future.result(timeout=60)  # Longer timeout for book search
                    
                    # Process book results
                    book_partial_results = []
                    
                    for variant, source, book_name, chapter, verse_num, marked_text in book_results:
                        grouped_matches[(variant, source)].append({
                            'book': book_name,
                            'chapter': chapter,
                            'verse': verse_num,
                            'text': marked_text
                        })
                        
                        # Add to partial results
                        if variant not in [r['variant'] for r in book_partial_results]:
                            book_partial_results.append({
                                'variant': variant,
                                'sources': list(source)
                            })
                    
                    # Call the callback with partial results if provided
                    if partial_results_callback and book_partial_results:
                        partial_results_callback(book_partial_results)
                    
                    logger.info("book_search_completed", book=book, results_count=len(book_results))
                        
                except Exception as e:
                    book = future_to_book[future]
                    logger.error("book_search_error", book=book, error=str(e))
        
        return grouped_matches
    
    def _group_lines_by_book(self, lines):
        """Group Torah lines by book."""
        book_lines = {}
        current_book = None
        current_lines = []
        
        # Define all the books we're looking for
        all_books = [
            "בראשית", "שמות", "ויקרא", "במדבר", "דברים",
            "יהושע", "שופטים", "שמואל א", "שמואל ב", "מלכים א", "מלכים ב",
            "ישעיה", "ירמיה", "יחזקאל", "הושע", "יואל", "עמוס", "עובדיה", "יונה",
            "מיכה", "נחום", "חבקוק", "צפניה", "חגי", "זכריה", "מלאכי",
            "תהילים", "משלי", "איוב", "שיר השירים", "רות", "איכה", "קהלת",
            "אסתר", "דניאל", "עזרא", "נחמיה", "דברי הימים א", "דברי הימים ב"
        ]
        
        for line in lines:
            line = line.strip()
            
            # Check for book/chapter headers - more flexible pattern matching
            match = re.match(r'^(\S+)\s+\u05e4\u05e8\u05e7-([\u05d0-\u05ea]+)$', line)
            book_name = None
            
            # Also check for just the book name at the beginning of a line
            if match:
                book_name = match.group(1)
            else:
                for book in all_books:
                    if line.startswith(book):
                        book_name = book
                        break
            
            if book_name:
                # If we found a new book, save the previous book's lines
                if current_book and current_book != book_name and current_lines:
                    book_lines[current_book] = current_lines
                    current_lines = []
                
                current_book = book_name
            
            # Add the line to the current book
            if current_book:
                current_lines.append(line)
        
        # Add the last book
        if current_book and current_lines:
            book_lines[current_book] = current_lines
        
        # Log the books found and their line counts
        book_counts = {book: len(lines) for book, lines in book_lines.items()}
        logger.info("grouped_lines_by_book", books=book_counts)
        
        # If no books were found, try a simpler approach - divide the text into 5 equal parts
        if len(book_lines) == 0:
            logger.info("no_books_found_using_equal_division")
            total_lines = len(lines)
            chunk_size = total_lines // 5
            book_lines = {
                'בראשית': lines[0:chunk_size],
                'שמות': lines[chunk_size:chunk_size*2],
                'ויקרא': lines[chunk_size*2:chunk_size*3],
                'במדבר': lines[chunk_size*3:chunk_size*4],
                'דברים': lines[chunk_size*4:]
            }
        
        return book_lines
    
    def _search_batch(self, batch_lines, automaton, phrase_length, input_phrase, full_text, is_memory_search=False):
        """Search for patterns in a batch of lines."""
        results = []
        book = chapter = None
        
        # Get the length of the input phrase (without spaces)
        input_word_length = len(input_phrase.replace(' ', ''))
        special_prefixes = ['ל', 'ו', 'מ']
        
        # Log the search batch parameters
        logger.info("search_batch", 
                   input_phrase=input_phrase,
                   input_word_length=input_word_length,
                   is_memory_search=is_memory_search)
        
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
                    
                    # Apply the special rule for words in memory search
                    if matched_text == variant and variant != input_phrase:
                        # For memory search, we need to check if this is a complete word match
                        if is_memory_search:
                            # Check if the match is a complete word (not part of a larger word)
                            is_word_boundary_start = (start_index == 0 or clean_verse[start_index - 1] == ' ')
                            is_word_boundary_end = (end_index == len(clean_verse) - 1 or clean_verse[end_index + 1] == ' ')
                            
                            if is_word_boundary_start and is_word_boundary_end:
                                # This is a complete word match
                                # Log for debugging
                                logger.info("complete_word_match", 
                                           variant=variant, 
                                           variant_length=len(variant),
                                           input_phrase=input_phrase,
                                           input_word_length=input_word_length)
                                
                                # Check if the variant has exactly the same number of letters as the input phrase
                                if len(variant) == input_word_length:
                                    logger.info("match_exact_length", 
                                              variant=variant, 
                                              input_phrase=input_phrase,
                                              both_lengths=f"{len(variant)}=={input_word_length}")
                                    if variant in full_text:
                                        marked_text = clean_verse.replace(variant, f'[{variant}]', 1)
                                        results.append((variant, tuple(source), book, chapter, verse_num, marked_text))
                                        break
                                # If the variant starts with one of the special prefixes and has more letters than the input phrase
                                elif len(variant) > input_word_length and any(variant.startswith(prefix) for prefix in special_prefixes):
                                    prefix_match = next((p for p in special_prefixes if variant.startswith(p)), None)
                                    logger.info("match_prefix", variant=variant, prefix=prefix_match)
                                    if variant in full_text:
                                        marked_text = clean_verse.replace(variant, f'[{variant}]', 1)
                                        results.append((variant, tuple(source), book, chapter, verse_num, marked_text))
                                        break
                                else:
                                    logger.info("skip_variant", 
                                              variant=variant, 
                                              variant_length=len(variant),
                                              input_length=input_word_length,
                                              reason=f"length_mismatch: {len(variant)} != {input_word_length}")
                            else:
                                # This is a partial match within a larger word
                                logger.info("skip_partial_match", 
                                          variant=variant,
                                          containing_word_context=clean_verse[max(0, start_index-5):min(len(clean_verse), end_index+6)],
                                          reason="not_complete_word")
                        else:
                            # Original behavior for indexed search (allows partial matches)
                            logger.info("indexed_search_match", variant=variant)
                            if variant in full_text:
                                marked_text = clean_verse.replace(variant, f'[{variant}]', 1)
                                results.append((variant, tuple(source), book, chapter, verse_num, marked_text))
                                break
        
        return results
    
    def _search_parallel_multi_word(self, word_variants, lines, input_phrase, full_text, 
                                   partial_results_callback=None, is_memory_search=False):
        """
        Perform parallel search for multi-word phrases where words can appear anywhere in the verse.
        
        Args:
            word_variants: List of (word, automaton) tuples for each word in the search phrase
            lines: Torah text lines
            input_phrase: Original input phrase
            full_text: Full Torah text
            partial_results_callback: Callback for partial results
            is_memory_search: Whether this is a memory search
            
        Returns:
            Dictionary of grouped matches
        """
        grouped_matches = defaultdict(list)
        
        # Check if we should use book-based parallelization
        use_book_parallel = current_app.config.get('USE_BOOK_PARALLEL_SEARCH', False)
        
        # Log the parallelization method being used
        logger.info("multi_word_search_parallelization", 
                   use_book_parallel=use_book_parallel, 
                   max_workers=current_app.config.get('MAX_WORKERS', 4),
                   input_phrase=input_phrase,
                   word_count=len(word_variants))
        
        if use_book_parallel:
            # Group lines by book
            book_lines = self._group_lines_by_book(lines)
            
            # Use maximum number of workers for better performance
            num_workers = current_app.config['MAX_WORKERS']
            
            # Use context manager for thread pool
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                # Submit search for each book
                future_to_book = {
                    executor.submit(
                        self._search_batch_multi_word,
                        book_lines[book], word_variants, input_phrase, full_text, is_memory_search
                    ): book
                    for book in book_lines
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_book):
                    try:
                        book = future_to_book[future]
                        book_results = future.result(timeout=60)  # Longer timeout for book search
                        
                        # Process book results
                        book_partial_results = []
                        
                        for variant_combo, source_combo, book_name, chapter, verse_num, marked_text in book_results:
                            # Create a combined variant string and sources
                            combined_variant = " + ".join(variant_combo)
                            combined_sources = tuple(source for source in source_combo)
                            
                            grouped_matches[(combined_variant, combined_sources)].append({
                                'book': book_name,
                                'chapter': chapter,
                                'verse': verse_num,
                                'text': marked_text
                            })
                            
                            # Add to partial results
                            if combined_variant not in [r['variant'] for r in book_partial_results]:
                                book_partial_results.append({
                                    'variant': combined_variant,
                                    'sources': list(combined_sources)
                                })
                        
                        # Call the callback with partial results if provided
                        if partial_results_callback and book_partial_results:
                            partial_results_callback(book_partial_results)
                        
                        logger.info("multi_word_book_search_completed", 
                                   book=book, 
                                   results_count=len(book_results))
                            
                    except Exception as e:
                        book = future_to_book[future]
                        logger.error("multi_word_book_search_error", book=book, error=str(e), exc_info=True)
        else:
            # Original line-based parallelization
            num_workers = current_app.config['MAX_WORKERS']
            batch_multiplier = current_app.config.get('BATCH_SIZE_MULTIPLIER', 150)
            batch_size = max(batch_multiplier, len(lines) // num_workers)
            batches = [lines[i:i+batch_size] for i in range(0, len(lines), batch_size)]
            
            # Use context manager for thread pool
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                # Submit all batch searches
                future_to_batch = {
                    executor.submit(
                        self._search_batch_multi_word,
                        batch, word_variants, input_phrase, full_text, is_memory_search
                    ): batch_idx
                    for batch_idx, batch in enumerate(batches)
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_batch):
                    try:
                        batch_results = future.result(timeout=30)
                        
                        # Process batch results
                        batch_partial_results = []
                        
                        for variant_combo, source_combo, book, chapter, verse_num, marked_text in batch_results:
                            # Create a combined variant string and sources
                            combined_variant = " + ".join(variant_combo)
                            combined_sources = tuple(source for source in source_combo)
                            
                            grouped_matches[(combined_variant, combined_sources)].append({
                                'book': book,
                                'chapter': chapter,
                                'verse': verse_num,
                                'text': marked_text
                            })
                            
                            # Add to partial results
                            if combined_variant not in [r['variant'] for r in batch_partial_results]:
                                batch_partial_results.append({
                                    'variant': combined_variant,
                                    'sources': list(combined_sources)
                                })
                        
                        # Call the callback with partial results if provided
                        if partial_results_callback and batch_partial_results:
                            partial_results_callback(batch_partial_results)
                            
                    except Exception as e:
                        batch_idx = future_to_batch[future]
                        logger.error("multi_word_batch_search_error", batch=batch_idx, error=str(e), exc_info=True)
        
        return grouped_matches
    
    def _apply_filters(self, results, filters):
        """
        Apply filters to search results.
        
        Args:
            results: Dictionary with 'results' and 'total_variants' keys
            filters: Dictionary with optional 'book', 'chapter', and 'verse' keys
            
        Returns:
            Dictionary with filtered results
        """
        filtered_results = []
        
        # Log the filters being applied
        logger.info("applying_filters", filters=filters)
        
        # Extract filters
        filter_book = filters.get('book')
        filter_chapter = filters.get('chapter')
        filter_verse = filters.get('verse')
        
        # Apply filters to each result
        for result in results['results']:
            # Filter locations
            filtered_locations = []
            
            for location in result['locations']:
                # Check if location matches all provided filters
                matches = True
                
                if filter_book and location['book'] != filter_book:
                    matches = False
                
                if filter_chapter and location['chapter'] != filter_chapter:
                    matches = False
                
                if filter_verse and location['verse'] != filter_verse:
                    matches = False
                
                if matches:
                    filtered_locations.append(location)
            
            # If there are any matching locations, include this result
            if filtered_locations:
                filtered_result = {
                    'variant': result['variant'],
                    'sources': result['sources'],
                    'locations': filtered_locations
                }
                filtered_results.append(filtered_result)
        
        # Log the filtering results
        logger.info("filter_results", 
                   original_count=len(results['results']),
                   filtered_count=len(filtered_results))
        
        return {
            'results': filtered_results,
            'total_variants': len(filtered_results)
        }
    
    def _search_batch_multi_word(self, batch_lines, word_variants, input_phrase, full_text, is_memory_search=False):
        """
        Search for multiple words in a batch of lines, where words can appear anywhere in the verse.
        
        Args:
            batch_lines: Lines of Torah text to search
            word_variants: List of (word, automaton) tuples for each word in the search phrase
            input_phrase: Original input phrase
            full_text: Full Torah text
            is_memory_search: Whether this is a memory search
            
        Returns:
            List of matches with variant combinations
        """
        results = []
        book = chapter = None
        
        # Get the original words
        original_words = [word for word, _ in word_variants]
        
        # Log the search batch parameters
        logger.info("multi_word_search_batch", 
                   input_phrase=input_phrase,
                   words=original_words,
                   is_memory_search=is_memory_search)
        
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
                
                # Skip very short verses
                if len(clean_verse) < 5:
                    continue
                
                # Find matches for each word
                word_matches = []
                
                for i, (word, automaton) in enumerate(word_variants):
                    # Find all matches for this word in the verse
                    word_match_list = []
                    
                    for end_index, (variant, source) in automaton.iter(clean_verse):
                        start_index = end_index - len(variant) + 1
                        matched_text = clean_verse[start_index:end_index + 1]
                        
                        # Check if this is a valid match based on search type
                        is_valid_match = False
                        
                        if is_memory_search:
                            # For memory search, check word boundaries and length rules
                            is_word_boundary_start = (start_index == 0 or clean_verse[start_index - 1] == ' ')
                            is_word_boundary_end = (end_index == len(clean_verse) - 1 or clean_verse[end_index + 1] == ' ')
                            
                            if is_word_boundary_start and is_word_boundary_end:
                                # Check length rules for memory search
                                word_length = len(word.replace(' ', ''))
                                variant_length = len(variant)
                                
                                if variant_length == word_length:
                                    # Exact length match
                                    is_valid_match = True
                                elif variant_length > word_length and any(variant.startswith(prefix) for prefix in ['ל', 'ו', 'מ']):
                                    # Special prefix exception
                                    is_valid_match = True
                        else:
                            # For indexed search, accept all matches
                            is_valid_match = True
                        
                        if is_valid_match:
                            word_match_list.append((variant, tuple(source), start_index, end_index))
                    
                    # If we found matches for this word, add them to the list
                    if word_match_list:
                        word_matches.append(word_match_list)
                    else:
                        # If any word has no matches, skip this verse
                        break
                
                # If we have matches for all words, create combinations
                if len(word_matches) == len(word_variants):
                    # Generate all possible combinations of matches
                    for combo in itertools.product(*word_matches):
                        # Check for overlaps
                        has_overlap = False
                        for i in range(len(combo)):
                            for j in range(i + 1, len(combo)):
                                # Check if the matches overlap
                                start1, end1 = combo[i][2], combo[i][3]
                                start2, end2 = combo[j][2], combo[j][3]
                                
                                if (start1 <= start2 <= end1) or (start1 <= end2 <= end1) or \
                                   (start2 <= start1 <= end2) or (start2 <= end1 <= end2):
                                    has_overlap = True
                                    break
                            
                            if has_overlap:
                                break
                        
                        if not has_overlap:
                            # Extract variants and sources
                            variants = [match[0] for match in combo]
                            sources = [match[1] for match in combo]
                            
                            # Create marked text with all matches highlighted
                            marked_text = clean_verse
                            
                            # Sort matches by position (right to left for Hebrew)
                            sorted_matches = sorted(combo, key=lambda x: -x[2])
                            
                            # Apply highlights from right to left
                            for variant, _, start_index, end_index in sorted_matches:
                                prefix = marked_text[:start_index]
                                match_text = marked_text[start_index:end_index + 1]
                                suffix = marked_text[end_index + 1:]
                                marked_text = prefix + f'[{match_text}]' + suffix
                            
                            # Add to results
                            results.append((variants, sources, book, chapter, verse_num, marked_text))
        
        return results
