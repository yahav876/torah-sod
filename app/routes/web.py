"""
Web routes for Torah Search
"""
from flask import Blueprint, render_template_string, current_app
from app.app_factory import cache
import structlog

logger = structlog.get_logger()

bp = Blueprint('web', __name__)


@bp.route('/')
# Temporarily disable caching to ensure latest changes are visible
# @cache.cached(timeout=300)
def index():
    """Serve the main search interface."""
    return render_template_string(get_main_template())


@bp.route('/about')
@cache.cached(timeout=3600)
def about():
    """About page."""
    return render_template_string(get_about_template())


def get_main_template():
    """Return the main search interface template."""
    return """
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
            margin-bottom: 15px;
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
        
        .search-options {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin-bottom: 20px;
            width: 100%;
            text-align: center;
        }
        
        .admin-options {
            margin-top: 50px;
            margin-bottom: 30px;
            text-align: center;
            padding: 20px;
            border-top: 1px dashed #ccc;
        }
        
        .admin-btn {
            padding: 12px 25px;
            background: #e67e22;
            color: white;
            border: 2px solid #d35400;
            border-radius: 15px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 3px 6px rgba(0,0,0,0.1);
        }
        
        .admin-btn:hover {
            background: #d35400;
            transform: translateY(-2px);
            box-shadow: 0 5px 10px rgba(0,0,0,0.2);
        }
        
        .toggle-container {
            display: flex;
            background: #f1f1f1;
            border-radius: 30px;
            padding: 5px;
            margin: 10px auto;
            width: 400px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .toggle-option {
            flex: 1;
            padding: 10px;
            text-align: center;
            cursor: pointer;
            border-radius: 25px;
            font-weight: bold;
            transition: all 0.3s ease;
            margin: 0 2px;
        }
        
        .toggle-option.active {
            background-color: #3498db;
            color: white;
            box-shadow: 0 2px 8px rgba(52, 152, 219, 0.5);
        }
        
        .toggle-help {
            text-align: center;
            color: #7f8c8d;
            font-size: 14px;
            margin-top: 5px;
            font-style: italic;
            width: 100%;
            max-width: 500px;
            margin-left: auto;
            margin-right: auto;
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
        
        #cancelBtn {
            display: none;
            padding: 8px 15px;
            background: #95a5a6;
            color: white;
            border: none;
            border-radius: 15px;
            font-size: 14px;
            cursor: pointer;
            margin-top: 10px;
            transition: all 0.2s;
        }
        
        #cancelBtn:hover {
            background: #7f8c8d;
        }
        
        .progress-container {
            width: 100%;
            background-color: #f3f3f3;
            border-radius: 10px;
            margin: 10px 0;
            display: none;
        }
        
        .progress-bar {
            height: 10px;
            background-color: #4CAF50;
            border-radius: 10px;
            width: 0%;
            transition: width 0.3s;
        }
        
        .partial-results {
            font-style: italic;
            color: #7f8c8d;
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 5px solid #3498db;
        }
        
        .partial-result-item {
            background: #fff;
            margin: 10px 0;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
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
        
        .variant-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            padding: 5px;
            border-radius: 5px;
            transition: background-color 0.2s;
        }
        
        .variant-header:hover {
            background-color: #f0f0f0;
        }
        
        .variant-toggle {
            font-size: 20px;
            color: #7f8c8d;
            transition: transform 0.3s;
        }
        
        .variant-toggle.collapsed {
            transform: rotate(-90deg);
        }
        
        .sources {
            color: #7f8c8d;
            margin-bottom: 15px;
            font-style: italic;
        }
        
        .locations-container {
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }
        
        .locations-container.collapsed {
            max-height: 0;
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
        
        .results-controls {
            margin: 20px 0;
            text-align: center;
        }
        
        .control-btn {
            padding: 10px 20px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            margin: 0 5px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.2s;
        }
        
        .control-btn:hover {
            background: #2980b9;
            transform: translateY(-2px);
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
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
                <button id="searchBtn">חפש</button>
            </div>
            
            <div class="search-options">
                <div class="toggle-container">
                    <div id="indexedOption" class="toggle-option active">חיפוש מאגר נתונים</div>
                    <div id="memoryOption" class="toggle-option">חיפוש בזיכרון</div>
                </div>
                <div class="toggle-help">
                    לחץ על אחת האפשרויות כדי לבחור שיטת חיפוש - האפשרות הכחולה היא הנבחרת
                </div>
                
                <div class="admin-options">
                    <div style="margin-bottom: 10px; font-weight: bold;">ניהול מערכת</div>
                    <button id="clearCacheBtn" class="admin-btn">נקה את המטמון</button>
                </div>
            </div>
            
            <div id="loading">
                מחפש...
                <div class="spinner"></div>
                <div>
                    <button id="cancelBtn">ביטול חיפוש</button>
                </div>
            </div>
            
            <div class="progress-container" id="progressContainer">
                <div class="progress-bar" id="progressBar"></div>
            </div>
            
            <div id="partialResults" class="partial-results" style="display: none;"></div>
            
            <div class="results-controls" id="resultsControls" style="display: none;">
                <button id="expandAllBtn" class="control-btn">הרחב הכל</button>
                <button id="collapseAllBtn" class="control-btn">כווץ הכל</button>
            </div>
            
            <div id="results"></div>
        </div>
    </div>

    <script>
        let isSearching = false;
        let searchType = 'indexed'; // Default search type
        let searchJobId = null;
        let progressInterval = null;
        let partialResults = [];
        let abortController = null;
        
        // Initialize all event handlers when the DOM is fully loaded
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM fully loaded, initializing event handlers');
            
            // Set up search button click handler
            document.getElementById('searchBtn').addEventListener('click', function() {
                search();
            });
            
            // Set up search type toggle handlers
            document.getElementById('indexedOption').addEventListener('click', function() {
                setSearchType('indexed');
            });
            
            document.getElementById('memoryOption').addEventListener('click', function() {
                setSearchType('memory');
            });
            
            // Set up clear cache button handler
            document.getElementById('clearCacheBtn').addEventListener('click', function() {
                clearCache();
            });
            
            // Set up cancel button handler
            document.getElementById('cancelBtn').addEventListener('click', function() {
                cancelSearch();
            });
            
            // Set up search input enter key handler
            document.getElementById('searchInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    search();
                }
            });
            
            // Set up expand/collapse all buttons
            document.getElementById('expandAllBtn').addEventListener('click', function() {
                expandAllVariants();
            });
            
            document.getElementById('collapseAllBtn').addEventListener('click', function() {
                collapseAllVariants();
            });
        });
        
        // Set up search type toggle
        function setSearchType(type) {
            searchType = type;
            
            // Update UI
            if (type === 'indexed') {
                document.getElementById('indexedOption').classList.add('active');
                document.getElementById('memoryOption').classList.remove('active');
            } else {
                document.getElementById('indexedOption').classList.remove('active');
                document.getElementById('memoryOption').classList.add('active');
            }
        }
        
        
        async function search() {
            if (isSearching) return;
            
            const query = document.getElementById('searchInput').value.trim();
            if (!query) {
                alert('אנא הכנס מילה או ביטוי לחיפוש');
                return;
            }
            
            isSearching = true;
            document.getElementById('loading').style.display = 'block';
            document.getElementById('cancelBtn').style.display = 'inline-block';
            document.getElementById('results').innerHTML = '';
            document.getElementById('partialResults').innerHTML = `
                <div style="text-align: center; padding: 20px;">
                    מחפש תוצאות... אנא המתן
                </div>`;
            document.getElementById('partialResults').style.display = 'block';
            document.getElementById('searchBtn').disabled = true;
            document.getElementById('progressContainer').style.display = 'block';
            document.getElementById('progressBar').style.width = '0%';
            
            // Reset partial results
            partialResults = [];
            
            try {
                // Create a new AbortController for this search
                abortController = new AbortController();
                const signal = abortController.signal;
                
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        phrase: query,
                        search_type: searchType
                    }),
                    signal: signal
                });
                
                const data = await response.json();
                
                // Check if this is a background job
                if (data.job_id) {
                    searchJobId = data.job_id;
                    startProgressPolling(searchJobId);
                } else {
                    // Regular search result
                    displayResults(data);
                    document.getElementById('progressContainer').style.display = 'none';
                }
                
            } catch (error) {
                if (error.name === 'AbortError') {
                    document.getElementById('results').innerHTML = 
                        '<div class="error">החיפוש בוטל על ידי המשתמש</div>';
                    document.getElementById('progressContainer').style.display = 'none';
                } else {
                    console.error('Error:', error);
                    document.getElementById('results').innerHTML = 
                        '<div class="error">שגיאה בחיפוש: ' + error.message + '</div>';
                    document.getElementById('progressContainer').style.display = 'none';
                }
            } finally {
                if (!searchJobId) {
                    isSearching = false;
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('cancelBtn').style.display = 'none';
                    document.getElementById('searchBtn').disabled = false;
                }
            }
        }
        
        // Poll for progress updates and partial results
        async function startProgressPolling(jobId) {
            let progress = 0;
            let completed = false;
            
            // Update progress bar immediately
            updateProgressBar(10);
            
            // Start polling for partial results
            progressInterval = setInterval(async () => {
                try {
                    const response = await fetch(`/api/search/status/${jobId}`);
                    const data = await response.json();
                    
                    if (data.progress) {
                        progress = data.progress;
                    } else {
                        // Increment progress slightly to show activity
                        progress = Math.min(progress + 5, 90);
                    }
                    
                    updateProgressBar(progress);
                    
                    // Check for partial results
                    if (data.partial_results && data.partial_results.length > 0) {
                        updatePartialResults(data.partial_results);
                    }
                    
                    // Check if search is complete
                    if (data.status === 'completed') {
                        clearInterval(progressInterval);
                        completed = true;
                        
                        // Display final results
                        if (data.results) {
                            displayResults(data.results);
                        }
                        
                        // Clean up
                        searchJobId = null;
                        isSearching = false;
                        document.getElementById('loading').style.display = 'none';
                        document.getElementById('cancelBtn').style.display = 'none';
                        document.getElementById('searchBtn').disabled = false;
                        document.getElementById('progressContainer').style.display = 'none';
                        document.getElementById('partialResults').innerHTML = '';
                    }
                    
                    // Check for failure
                    if (data.status === 'failed') {
                        clearInterval(progressInterval);
                        document.getElementById('results').innerHTML = 
                            '<div class="error">שגיאה בחיפוש: ' + (data.error_message || 'שגיאה לא ידועה') + '</div>';
                        
                        // Clean up
                        searchJobId = null;
                        isSearching = false;
                        document.getElementById('loading').style.display = 'none';
                        document.getElementById('cancelBtn').style.display = 'none';
                        document.getElementById('searchBtn').disabled = false;
                        document.getElementById('progressContainer').style.display = 'none';
                        document.getElementById('partialResults').innerHTML = '';
                    }
                    
                } catch (error) {
                    console.error('Error checking progress:', error);
                }
            }, 1000);
        }
        
        function updateProgressBar(progress) {
            document.getElementById('progressBar').style.width = `${progress}%`;
        }
        
        // Function to cancel an ongoing search
        function cancelSearch() {
            if (!isSearching) return;
            
            // If using AbortController for fetch
            if (abortController) {
                abortController.abort();
                abortController = null;
            }
            
            // If using a background job
            if (searchJobId) {
                // Clear the polling interval
                if (progressInterval) {
                    clearInterval(progressInterval);
                    progressInterval = null;
                }
                
                // Update UI
                searchJobId = null;
                isSearching = false;
                document.getElementById('loading').style.display = 'none';
                document.getElementById('cancelBtn').style.display = 'none';
                document.getElementById('searchBtn').disabled = false;
                document.getElementById('progressContainer').style.display = 'none';
                document.getElementById('partialResults').innerHTML = '';
                document.getElementById('results').innerHTML = 
                    '<div class="error">החיפוש בוטל על ידי המשתמש</div>';
            }
        }
        
        function updatePartialResults(newResults) {
            console.log("Received partial results:", newResults.length);
            
            // Add new results that aren't already in the partial results
            for (const result of newResults) {
                if (!partialResults.some(r => r.variant === result.variant)) {
                    partialResults.push(result);
                }
            }
            
            // Always show the partial results container, even if empty
            document.getElementById('partialResults').style.display = 'block';
            
            // Display partial results
            if (partialResults.length > 0) {
                let html = `<div style="font-weight: bold; color: #2c3e50; margin-bottom: 10px;">
                    נמצאו ${partialResults.length} תוצאות חלקיות עד כה... (החיפוש עדיין מתבצע)
                </div>`;
                
                // Display all partial results with real-time updates
                partialResults.forEach((result, index) => {
                    html += `<div class="partial-result-item">`;
                    html += `<div class="variant">${result.variant}</div>`;
                    html += `<div class="sources">מקורות: ${result.sources.join(', ')}</div>`;
                    
                    // Add a sample location if available
                    if (result.locations && result.locations.length > 0) {
                        const location = result.locations[0];
                        html += `<div class="location">`;
                        html += `<div class="location-header">${location.book} פרק ${location.chapter}, פסוק ${location.verse}</div>`;
                        html += `<div class="verse-text">${location.text.replace(/\[([^\]]+)\]/g, '<span class="highlight">$1</span>')}</div>`;
                        html += `</div>`;
                        
                        if (result.locations.length > 1) {
                            html += `<div style="text-align: center; font-style: italic; margin-top: 5px;">
                                ועוד ${result.locations.length - 1} מקומות נוספים...
                            </div>`;
                        }
                    }
                    
                    html += `</div>`;
                });
                
                document.getElementById('partialResults').innerHTML = html;
            } else {
                document.getElementById('partialResults').innerHTML = `
                    <div style="text-align: center; padding: 20px;">
                        מחפש תוצאות... אנא המתן
                    </div>`;
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
            
            data.results.forEach((result, index) => {
                const resultId = 'result-' + index;
                html += '<div class="result-item">';
                
                // Collapsible variant header
                html += '<div class="variant-header" data-result-id="' + resultId + '">';
                html += '<div class="variant">' + result.variant + '</div>';
                html += '<div class="variant-toggle">▼</div>';
                html += '</div>';
                
                html += '<div class="sources">מקורות: ' + result.sources.join(', ') + '</div>';
                
                // Collapsible locations container
                html += '<div id="' + resultId + '" class="locations-container">';
                
                result.locations.forEach(location => {
                    html += '<div class="location">';
                    html += '<div class="location-header">' + location.book + ' פרק ' + location.chapter + ', פסוק ' + location.verse + '</div>';
                    html += '<div class="verse-text">' + location.text.replace(/\[([^\]]+)\]/g, '<span class="highlight">$1</span>') + '</div>';
                    html += '</div>';
                });
                
                html += '</div>'; // End locations-container
                html += '</div>'; // End result-item
            });
            
            resultsDiv.innerHTML = html;
            
            // Initialize all location containers with proper height
            data.results.forEach((result, index) => {
                const container = document.getElementById('result-' + index);
                if (container) {
                    container.style.maxHeight = container.scrollHeight + 'px';
                }
            });
            
            // Add click event listeners to all variant headers
            document.querySelectorAll('.variant-header').forEach(header => {
                header.addEventListener('click', function() {
                    const resultId = this.getAttribute('data-result-id');
                    toggleVariant(resultId);
                });
            });
            
            // Show the expand/collapse all buttons
            document.getElementById('resultsControls').style.display = 'block';
        }
        
        // Function to toggle variant expansion/collapse
        function toggleVariant(resultId) {
            const container = document.getElementById(resultId);
            if (!container) {
                console.error('Container not found:', resultId);
                return;
            }
            
            // Find the header by traversing up from the container
            const resultItem = container.parentElement;
            if (!resultItem) {
                console.error('Result item not found for:', resultId);
                return;
            }
            
            // Find the variant header (first child of result item)
            const header = resultItem.querySelector('.variant-header');
            if (!header) {
                console.error('Header not found for:', resultId);
                return;
            }
            
            // Find the toggle element
            const toggle = header.querySelector('.variant-toggle');
            if (!toggle) {
                console.error('Toggle not found for:', resultId);
                return;
            }
            
            if (container.classList.contains('collapsed')) {
                // Expand
                container.classList.remove('collapsed');
                container.style.maxHeight = container.scrollHeight + 'px';
                toggle.classList.remove('collapsed');
                toggle.textContent = '▼';
            } else {
                // Collapse
                container.classList.add('collapsed');
                container.style.maxHeight = '0';
                toggle.classList.add('collapsed');
                toggle.textContent = '◀';
            }
        }
        
        // Function to expand all variants
        function expandAllVariants() {
            document.querySelectorAll('.locations-container').forEach(container => {
                if (container.classList.contains('collapsed')) {
                    const resultId = container.id;
                    toggleVariant(resultId);
                }
            });
        }
        
        // Function to collapse all variants
        function collapseAllVariants() {
            document.querySelectorAll('.locations-container').forEach(container => {
                if (!container.classList.contains('collapsed')) {
                    const resultId = container.id;
                    toggleVariant(resultId);
                }
            });
        }
        
        // Function to clear all search caches
        async function clearCache() {
            if (!confirm('האם אתה בטוח שברצונך לנקות את כל המטמון? פעולה זו תמחק את כל תוצאות החיפוש השמורות.')) {
                return;
            }
            
            try {
                const response = await fetch('/api/admin/clear-cache', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('המטמון נוקה בהצלחה!');
                } else {
                    alert('שגיאה בניקוי המטמון: ' + (data.error || 'שגיאה לא ידועה'));
                }
                
            } catch (error) {
                console.error('Error clearing cache:', error);
                alert('שגיאה בניקוי המטמון: ' + error.message);
            }
        }
    </script>
</body>
</html>
"""


def get_about_template():
    """Return the about page template."""
    return """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>אודות - Torah Search</title>
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
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
            padding: 40px;
        }
        
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        
        p {
            line-height: 1.8;
            color: #34495e;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>אודות המערכת</h1>
        <p>מערכת חיפוש בתורה המאפשרת לחפש מילים וביטויים בעזרת שיטות החלפת אותיות שונות.</p>
        <p>המערכת משתמשת בטכנולוגיות מתקדמות לחיפוש מהיר ויעיל בטקסט התורה.</p>
        <a href="/">חזרה לעמוד הראשי</a>
    </div>
</body>
</html>
"""
