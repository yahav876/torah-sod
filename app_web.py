#!/usr/bin/env python3
"""
Torah Search Web Application
A production-ready Flask web service for searching Hebrew text in the Torah
using various letter mapping techniques.
"""

import os
import re
import itertools
import ahocorasick
import json
import time
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_cors import CORS
import logging
from functools import lru_cache
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    TORAH_FILE = os.path.join(os.path.dirname(__file__), 'torah.txt')
    MAX_RESULTS = int(os.environ.get('MAX_RESULTS', '1000'))
    CACHE_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT', '3600'))
    MAX_WORKERS = int(os.environ.get('MAX_WORKERS', '8'))

app.config.from_object(Config)

# === Letter Mapping Data ===
abgd_map_1 = { 'א': 'ב', 'ב': 'א', 'ג': 'ד', 'ד': 'ג', 'ה': 'ו', 'ו': 'ה',
               'ז': 'ח', 'ח': 'ז', 'ט': 'י', 'י': 'ט', 'כ': 'ל', 'ל': 'כ',
               'מ': 'נ', 'נ': 'מ', 'ס': 'ע', 'ע': 'ס', 'פ': 'צ', 'צ': 'פ',
               'ק': 'ר', 'ר': 'ק', 'ש': 'ת', 'ת': 'ש' }

abgd_map_2 = { 'א': 'ת', 'ת': 'א', 'ב': 'ש', 'ש': 'ב', 'ג': 'ר', 'ר': 'ג',
               'ד': 'ק', 'ק': 'ד', 'ה': 'צ', 'צ': 'ה', 'ו': 'פ', 'פ': 'ו',
               'ז': 'ע', 'ע': 'ז', 'ח': 'ס', 'ס': 'ח', 'ט': 'נ', 'נ': 'ט',
               'י': 'מ', 'מ': 'י', 'כ': 'ל', 'ל': 'כ' }

abgd_map_3 = { 'א': 'ל', 'ל': 'א', 'ב': 'מ', 'מ': 'ב', 'ג': 'נ', 'נ': 'ג',
               'ד': 'ס', 'ס': 'ד', 'ה': 'ע', 'ע': 'ה', 'ו': 'פ', 'פ': 'ו',
               'ז': 'צ', 'צ': 'ז', 'ח': 'ק', 'ק': 'ח', 'ט': 'ר', 'ר': 'ט',
               'י': 'ש', 'ש': 'י', 'כ': 'ת', 'ת': 'כ' }

abgd_map_4 = { 'א': 'ט', 'ט': 'א', 'ב': 'ח', 'ח': 'ב', 'ג': 'ז', 'ז': 'ג',
               'ד': 'ו', 'ו': 'ד', 'צ': 'י', 'ה': 'ה', 'פ': 'כ', 'י': 'צ',
               'ל': 'ע', 'כ': 'פ', 'ס': 'מ', 'ע': 'ל', 'נ': 'נ', 'מ': 'ס',
               'ן': 'ש', 'ץ': 'ק', 'ם': 'ת', 'ף': 'ר',
               'ן': 'ן', 'ם': 'ם', 'ך': 'ך', 'ף': 'ף' }

abgd_map_5 = [['א','י','ק'], ['ב','כ','ר'], ['ג','ל','ש'],
              ['ד','מ','ת'], ['ה','נ','ך'], ['ו','ס','ם'],
              ['ז','ע','ן'], ['ח','פ','ף'], ['ת','צ','ץ']]

abgd_map_6 = [['א','ח','ס'], ['ב','ט','ע'], ['ג','י','פ'],
              ['ד','כ','צ'], ['ה','ל','ק'], ['ו','מ','ר'],
              ['ז','נ','ש'], ['ז','נ','ת']]

abgd_map_7 = [['א','ה','ח','ע'],
              ['ב','ו','מ','פ'],
              ['ג','י','כ','ק'],
              ['ד','ט','ל','נ','ת'],
              ['ז','ס','ש','ר','צ']]

abgd_map_8 = [['א','ה','ו','י']]

final_to_regular = { 'ך':'כ', 'ם':'מ', 'ן':'נ', 'ף':'פ', 'ץ':'צ' }

maps = [
    ("Map 1", abgd_map_1),
    ("Map 2", abgd_map_2),
    ("Map 3", abgd_map_3),
    ("Map 4", abgd_map_4)
]

ignored_prefixes = {'ל', 'מ', 'ו', 'ה', 'כ'}

# Global variables for caching
_torah_lines = None
_torah_text = None
_torah_lock = threading.RLock()

# === Core Search Logic ===

def get_grouped_mapped(ch, map_group, label, apply_normalization=False):
    """Get mapped characters from group-based maps."""
    results = []
    ch_norm = final_to_regular.get(ch, ch) if apply_normalization else ch
    for group in map_group:
        if ch_norm in group:
            results.extend([(other, label) for other in group if other != ch_norm])
    return results

def get_possible_conversions(ch):
    """Get all possible character conversions for a given Hebrew character."""
    results = []
    norm = final_to_regular.get(ch, ch)
    
    # Maps 1-3
    for map_name, mapping in maps[:3]:
        if norm in mapping:
            results.append((mapping[norm], map_name))
    
    # Map 4
    if ch in abgd_map_4:
        results.append((abgd_map_4[ch], "Map 4"))
    
    # Maps 5-8
    results.extend(get_grouped_mapped(ch, abgd_map_5, "Map 5"))
    results.extend(get_grouped_mapped(ch, abgd_map_6, "Map 6"))
    results.extend(get_grouped_mapped(ch, abgd_map_7, "Map 7", apply_normalization=True))
    results.extend(get_grouped_mapped(ch, abgd_map_8, "Map 8"))
    
    # Original character
    results.append((ch, "Original"))
    
    return list(set(results))

def generate_all_variants(phrase):
    """Generate all possible variants of a phrase using letter mappings."""
    letter_options = []
    for ch in phrase:
        if ch == ' ':
            letter_options.append([(' ', 'Original')])
        else:
            letter_options.append(get_possible_conversions(ch))
    
    return [
        ("".join([ltr for ltr, _ in combo]), [src for _, src in combo])
        for combo in itertools.product(*letter_options)
    ]

@lru_cache(maxsize=128)
def load_torah_lines():
    """Load Torah lines with caching."""
    global _torah_lines, _torah_text
    
    with _torah_lock:
        if _torah_lines is None:
            try:
                with open(app.config['TORAH_FILE'], encoding="utf-8") as f:
                    _torah_lines = f.readlines()
                    _torah_text = ''.join(_torah_lines)
                logger.info(f"Loaded Torah file with {len(_torah_lines)} lines")
            except FileNotFoundError:
                logger.error(f"Torah file not found: {app.config['TORAH_FILE']}")
                return [], ""
        
        return _torah_lines, _torah_text

def build_automaton(variant_tuples):
    """Build Aho-Corasick automaton for efficient pattern matching."""
    automaton = ahocorasick.Automaton()
    for variant, source in variant_tuples:
        automaton.add_word(variant, (variant, source))
    automaton.make_automaton()
    return automaton

def search_in_batch(batch_lines, automaton, phrase_length, input_phrase, full_text):
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

def search_with_reference_parallel(automaton, lines, phrase_length, input_phrase, full_text):
    """Perform parallel search across Torah text."""
    grouped_matches = defaultdict(list)

    num_workers = min(app.config['MAX_WORKERS'], os.cpu_count() or 4)
    batch_size = len(lines) // num_workers + 1
    batches = [lines[i:i+batch_size] for i in range(0, len(lines), batch_size)]

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [
            executor.submit(search_in_batch, batch, automaton, phrase_length, input_phrase, full_text) 
            for batch in batches
        ]
        
        for future in futures:
            try:
                for variant, source, book, chapter, verse_num, marked_text in future.result():
                    grouped_matches[(variant, source)].append({
                        'book': book,
                        'chapter': chapter, 
                        'verse': verse_num,
                        'text': marked_text
                    })
            except Exception as e:
                logger.error(f"Error in search batch: {e}")

    return grouped_matches

def perform_search(input_phrase):
    """Main search function."""
    try:
        start_time = time.time()
        
        # Load Torah text
        lines, full_text = load_torah_lines()
        if not lines:
            return {'error': 'Torah file not found or empty', 'results': []}
        
        # Generate variants and build automaton
        variant_tuples = generate_all_variants(input_phrase)
        automaton = build_automaton(variant_tuples)
        
        # Perform search
        grouped_matches = search_with_reference_parallel(
            automaton, lines, len(input_phrase.replace(' ', '')), input_phrase, full_text
        )
        
        # Format results
        results = []
        for (variant, sources), locations in grouped_matches.items():
            if len(results) >= app.config['MAX_RESULTS']:
                break
                
            results.append({
                'variant': variant,
                'sources': list(sources),
                'locations': locations[:100]  # Limit locations per variant
            })
        
        search_time = time.time() - start_time
        
        return {
            'input_phrase': input_phrase,
            'results': results,
            'total_variants': len(grouped_matches),
            'search_time': round(search_time, 3),
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {
            'error': str(e),
            'success': False,
            'results': []
        }

# === Web Routes ===

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Torah Search - חיפוש בתורה</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            direction: rtl;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(45deg, #2c3e50, #3498db);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .search-section {
            padding: 30px;
            text-align: center;
        }
        
        .search-box {
            display: flex;
            gap: 15px;
            justify-content: center;
            align-items: center;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        
        #searchInput {
            padding: 15px 20px;
            font-size: 18px;
            border: 2px solid #ddd;
            border-radius: 25px;
            min-width: 300px;
            text-align: right;
            direction: rtl;
        }
        
        #searchInput:focus {
            outline: none;
            border-color: #3498db;
            box-shadow: 0 0 10px rgba(52, 152, 219, 0.3);
        }
        
        #searchBtn {
            padding: 15px 30px;
            background: linear-gradient(45deg, #e74c3c, #c0392b);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 18px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        #searchBtn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(231, 76, 60, 0.4);
        }
        
        #loading {
            display: none;
            color: #3498db;
            font-size: 18px;
            margin: 20px 0;
        }
        
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-left: 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        #results {
            margin-top: 30px;
            text-align: right;
        }
        
        .result-item {
            background: #f8f9fa;
            margin: 15px 0;
            padding: 20px;
            border-radius: 10px;
            border-right: 5px solid #3498db;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .variant {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        
        .sources {
            color: #7f8c8d;
            margin-bottom: 15px;
            font-style: italic;
        }
        
        .location {
            background: white;
            margin: 10px 0;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #ecf0f1;
        }
        
        .location-header {
            font-weight: bold;
            color: #e74c3c;
            margin-bottom: 8px;
        }
        
        .verse-text {
            line-height: 1.6;
            font-size: 16px;
        }
        
        .highlight {
            background: #f1c40f;
            padding: 2px 4px;
            border-radius: 3px;
            font-weight: bold;
        }
        
        .stats {
            background: #ecf0f1;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
        }
        
        .error {
            background: #e74c3c;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        @media (max-width: 768px) {
            .search-box {
                flex-direction: column;
            }
            
            #searchInput {
                min-width: 250px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 חיפוש בתורה</h1>
            <p>חיפוש מילים בתורה בעזרת שיטות החלפת אותיות שונות</p>
        </div>
        
        <div class="search-section">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="הכנס מילה או ביטוי בעברית..." />
                <button id="searchBtn" onclick="search()">חפש</button>
            </div>
            
            <div id="loading">
                מחפש...
                <div class="spinner"></div>
            </div>
            
            <div id="results"></div>
        </div>
    </div>

    <script>
        let isSearching = false;
        
        document.getElementById('searchInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                search();
            }
        });
        
        async function search() {
            if (isSearching) return;
            
            const query = document.getElementById('searchInput').value.trim();
            if (!query) {
                alert('אנא הכנס מילה או ביטוי לחיפוש');
                return;
            }
            
            isSearching = true;
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').innerHTML = '';
            document.getElementById('searchBtn').disabled = true;
            
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ phrase: query })
                });
                
                const data = await response.json();
                displayResults(data);
                
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('results').innerHTML = 
                    '<div class="error">שגיאה בחיפוש: ' + error.message + '</div>';
            } finally {
                isSearching = false;
                document.getElementById('loading').style.display = 'none';
                document.getElementById('searchBtn').disabled = false;
            }
        }
        
        function displayResults(data) {
            const resultsDiv = document.getElementById('results');
            
            if (!data.success) {
                resultsDiv.innerHTML = '<div class="error">שגיאה: ' + (data.error || 'שגיאה לא ידועה') + '</div>';
                return;
            }
            
            if (data.results.length === 0) {
                resultsDiv.innerHTML = '<div class="error">לא נמצאו תוצאות עבור: ' + data.input_phrase + '</div>';
                return;
            }
            
            let html = '<div class="stats">';
            html += '<strong>נמצאו ' + data.total_variants + ' וריאציות</strong><br>';
            html += 'זמן חיפוש: ' + data.search_time + ' שניות';
            html += '</div>';
            
            data.results.forEach(result => {
                html += '<div class="result-item">';
                html += '<div class="variant">' + result.variant + '</div>';
                html += '<div class="sources">מקורות: ' + result.sources.join(', ') + '</div>';
                
                result.locations.forEach(location => {
                    html += '<div class="location">';
                    html += '<div class="location-header">' + location.book + ' פרק ' + location.chapter + ', פסוק ' + location.verse + '</div>';
                    html += '<div class="verse-text">' + location.text.replace(/\[([^\]]+)\]/g, '<span class="highlight">$1</span>') + '</div>';
                    html += '</div>';
                });
                
                html += '</div>';
            });
            
            resultsDiv.innerHTML = html;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the main search interface."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for performing search."""
    try:
        data = request.get_json()
        if not data or 'phrase' not in data:
            return jsonify({'error': 'Missing phrase parameter', 'success': False}), 400
        
        phrase = data['phrase'].strip()
        if not phrase:
            return jsonify({'error': 'Empty phrase provided', 'success': False}), 400
        
        if len(phrase) > 100:
            return jsonify({'error': 'Phrase too long (max 100 characters)', 'success': False}), 400
        
        logger.info(f"Search request for phrase: {phrase}")
        result = perform_search(phrase)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({'error': 'Internal server error', 'success': False}), 500

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'timestamp': time.time()})

@app.route('/stats')
def stats():
    """Get application statistics."""
    lines, _ = load_torah_lines()
    return jsonify({
        'torah_lines': len(lines),
        'max_results': app.config['MAX_RESULTS'],
        'max_workers': app.config['MAX_WORKERS']
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Development server
    logger.info("Starting Torah Search Web Application...")
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
