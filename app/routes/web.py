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
            font-size: 18px; /* Reduced by 25% from 24px */
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
        
        .variant-table {
            flex: 1;
            margin-right: 15px;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            overflow: hidden;
        }
        
        .variant-row {
            display: flex;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .variant-row:last-child {
            border-bottom: none;
        }
        
        .variant-cell {
            padding: 8px 12px;
        }
        
        .variant-cell:first-child {
            width: 120px;
            background-color: #f5f5f5;
            font-weight: bold;
            border-left: 1px solid #e0e0e0;
        }
        
        .variant-cell:last-child {
            flex: 1;
        }
        
        .sources {
            color: #7f8c8d;
            margin-bottom: 15px;
            font-style: italic;
        }
        
        .clickable-variant {
            cursor: pointer;
            text-decoration: underline;
            color: #3498db;
        }
        
        .clickable-variant:hover {
            color: #2980b9;
            text-decoration: underline;
        }
        
        .search-context-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        
        .search-context-content {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            width: 90%;
            max-width: 500px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            text-align: center;
        }
        
        .search-context-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #2c3e50;
        }
        
        .search-context-options {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 20px 0;
        }
        
        .search-context-option {
            padding: 10px 15px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.2s;
        }
        
        .search-context-option:hover {
            background-color: #2980b9;
            transform: translateY(-2px);
        }
        
        .search-context-close {
            padding: 8px 15px;
            background-color: #95a5a6;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 10px;
        }
        
        .search-context-close:hover {
            background-color: #7f8c8d;
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
        
        .clickable-location {
            cursor: pointer;
            text-decoration: underline;
            transition: all 0.2s;
        }
        
        .clickable-location:hover {
            color: #c0392b;
            transform: translateY(-1px);
        }
        
        .verse-text {
            line-height: 1.6;
            font-size: 12px; /* Reduced by 25% from 16px */
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
                <!-- Search options removed - using only in-memory search -->
                
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
            
            <!-- Filters Section -->
            <div id="filtersSection" style="display: none; margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 10px;">
                <div style="font-weight: bold; margin-bottom: 10px; font-size: 18px;">סינון תוצאות:</div>
                
                <div style="display: flex; flex-wrap: wrap; gap: 20px; justify-content: center;">
                    <!-- Book Filter -->
                    <div style="min-width: 200px;">
                        <div style="font-weight: bold; margin-bottom: 5px;">סינון לפי ספר:</div>
                        <select id="bookFilter" style="width: 100%; padding: 8px; border-radius: 5px; border: 1px solid #ddd;">
                            <option value="all">כל הספרים</option>
                            <option value="בראשית">בראשית</option>
                            <option value="שמות">שמות</option>
                            <option value="ויקרא">ויקרא</option>
                            <option value="במדבר">במדבר</option>
                            <option value="דברים">דברים</option>
                        </select>
                    </div>
                    
                    <!-- Source Filter -->
                    <div style="min-width: 200px;">
                        <div style="font-weight: bold; margin-bottom: 5px;">סינון לפי מקור:</div>
                        <select id="sourceFilter" style="width: 100%; padding: 8px; border-radius: 5px; border: 1px solid #ddd;">
                            <option value="all">כל המקורות</option>
                            <!-- Will be populated dynamically -->
                        </select>
                    </div>
                </div>
                
                <div style="margin-top: 15px; text-align: center;">
                    <button id="applyFiltersBtn" class="control-btn">החל סינון</button>
                    <button id="resetFiltersBtn" class="control-btn" style="background-color: #95a5a6;">איפוס סינון</button>
                </div>
            </div>
            
            <div id="results"></div>
        </div>
    </div>
    
    <!-- Search Context Modal -->
    <div id="searchContextModal" class="search-context-modal">
        <div class="search-context-content">
            <div class="search-context-title">חיפוש נוסף עבור: <span id="contextVariantText"></span></div>
            <div>בחר את ההקשר לחיפוש:</div>
            <div class="search-context-options">
                <button id="searchInVerse" class="search-context-option">חפש בפסוק</button>
                <button id="searchInChapter" class="search-context-option">חפש בפרק</button>
            </div>
            <button id="closeContextModal" class="search-context-close">סגור</button>
        </div>
    </div>
    
    <!-- Location Search Modal -->
    <div id="locationSearchModal" class="search-context-modal">
        <div class="search-context-content">
            <div class="search-context-title">חיפוש חדש ב<span id="locationContextText"></span></div>
            <div>הכנס מילה לחיפוש:</div>
            <div style="margin: 20px 0;">
                <input type="text" id="locationSearchInput" placeholder="הכנס מילה או ביטוי..." style="padding: 10px; width: 80%; text-align: right; direction: rtl;" />
            </div>
            <div class="search-context-options">
                <button id="searchLocationVerse" class="search-context-option">חפש בפסוק</button>
                <button id="searchLocationChapter" class="search-context-option">חפש בפרק</button>
            </div>
            <button id="closeLocationModal" class="search-context-close">סגור</button>
        </div>
    </div>

    <script>
        let isSearching = false;
        let searchType = 'memory'; // Always use memory search
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
            
            // Search type toggle handlers removed - using only in-memory search
            
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
        
        // Search type toggle function removed - using only in-memory search
        
        
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
            
            // Check if we should use streaming for small searches
            const wordCount = query.split(' ').length;
            const useStreaming = wordCount <= 10; // Use streaming for searches with 10 or fewer words
            
            if (useStreaming) {
                // Use Server-Sent Events for streaming results
                try {
                    const eventSource = new EventSource('/api/search/stream?' + new URLSearchParams({
                        phrase: query,
                        search_type: searchType
                    }));
                    
                    // Store EventSource for cancellation
                    window.currentEventSource = eventSource;
                    
                    let progressPercent = 10;
                    
                    eventSource.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        
                        if (data.type === 'start') {
                            console.log('Search started for:', data.phrase);
                            updateProgressBar(10);
                        } else if (data.type === 'partial') {
                            // Add partial result
                            if (!partialResults.some(r => r.variant === data.result.variant)) {
                                partialResults.push(data.result);
                                updatePartialResults(partialResults);
                                
                                // Update progress
                                progressPercent = Math.min(progressPercent + 5, 80);
                                updateProgressBar(progressPercent);
                            }
                        } else if (data.type === 'complete') {
                            // Display final results
                            eventSource.close();
                            window.currentEventSource = null;
                            
                            updateProgressBar(100);
                            displayResults(data.results);
                            
                            // Clean up
                            isSearching = false;
                            document.getElementById('loading').style.display = 'none';
                            document.getElementById('cancelBtn').style.display = 'none';
                            document.getElementById('searchBtn').disabled = false;
                            document.getElementById('progressContainer').style.display = 'none';
                            document.getElementById('partialResults').style.display = 'none';
                        }
                    };
                    
                    eventSource.onerror = function(error) {
                        console.error('EventSource error:', error);
                        eventSource.close();
                        window.currentEventSource = null;
                        
                        // Fallback to polling-based approach
                        console.log('Falling back to polling-based live search');
                        useLivePolling(query, searchType);
                    };
                    
                } catch (error) {
                    console.error('Error:', error);
                    document.getElementById('results').innerHTML = 
                        '<div class="error">שגיאה בחיפוש: ' + error.message + '</div>';
                    document.getElementById('progressContainer').style.display = 'none';
                    
                    // Clean up
                    isSearching = false;
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('cancelBtn').style.display = 'none';
                    document.getElementById('searchBtn').disabled = false;
                }
            } else {
                // Use regular search for complex queries (background job)
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
        }
        
        // Poll for progress updates and partial results
        async function startProgressPolling(jobId) {
            let progress = 0;
            let completed = false;
            
            // Update progress bar immediately
            updateProgressBar(10);
            
            // Make sure partial results container is visible
            document.getElementById('partialResults').style.display = 'block';
            
            // Do an immediate check for partial results
            try {
                const initialResponse = await fetch(`/api/search/status/${jobId}`);
                const initialData = await initialResponse.json();
                console.log("Initial status check:", initialData);
                
                if (initialData.partial_results && initialData.partial_results.length > 0) {
                    console.log("Initial partial results:", initialData.partial_results.length);
                    updatePartialResults(initialData.partial_results);
                }
            } catch (error) {
                console.error("Error in initial status check:", error);
            }
            
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
                        console.log("Received partial results from server:", data.partial_results.length);
                        updatePartialResults(data.partial_results);
                    } else {
                        console.log("No partial results in this update");
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
                        document.getElementById('partialResults').style.display = 'none';
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
                        document.getElementById('partialResults').style.display = 'none';
                    }
                    
                } catch (error) {
                    console.error('Error checking progress:', error);
                }
            }, 1000);
        }
        
        function updateProgressBar(progress) {
            document.getElementById('progressBar').style.width = `${progress}%`;
        }
        
        // Polling-based live search (fallback for when SSE doesn't work with ALB)
        async function useLivePolling(query, searchType) {
            try {
                // Start the search
                const startResponse = await fetch('/api/search/live', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        phrase: query,
                        search_type: searchType
                    })
                });
                
                const startData = await startResponse.json();
                if (!startData.success) {
                    throw new Error(startData.error || 'Failed to start search');
                }
                
                const sessionId = startData.session_id;
                let pollCount = 0;
                const maxPolls = 300; // 5 minutes max
                
                // Store the polling interval for cancellation
                window.currentPollInterval = setInterval(async () => {
                    try {
                        const pollResponse = await fetch(`/api/search/live/poll/${sessionId}`);
                        const pollData = await pollResponse.json();
                        
                        if (pollData.status === 'error') {
                            clearInterval(window.currentPollInterval);
                            document.getElementById('results').innerHTML = 
                                '<div class="error">שגיאה בחיפוש: ' + (pollData.error || 'Unknown error') + '</div>';
                            cleanupSearch();
                            return;
                        }
                        
                        // Update partial results
                        if (pollData.partial_results && pollData.partial_results.length > 0) {
                            updatePartialResults(pollData.partial_results);
                            updateProgressBar(Math.min(10 + (pollData.partial_results.length * 5), 80));
                        }
                        
                        // Check if completed
                        if (pollData.status === 'completed' && pollData.final_result) {
                            clearInterval(window.currentPollInterval);
                            updateProgressBar(100);
                            displayResults(pollData.final_result);
                            cleanupSearch();
                            return;
                        }
                        
                        // Timeout check
                        pollCount++;
                        if (pollCount > maxPolls) {
                            clearInterval(window.currentPollInterval);
                            document.getElementById('results').innerHTML = 
                                '<div class="error">החיפוש נכשל - חריגת זמן</div>';
                            cleanupSearch();
                        }
                        
                    } catch (error) {
                        console.error('Polling error:', error);
                        clearInterval(window.currentPollInterval);
                        document.getElementById('results').innerHTML = 
                            '<div class="error">שגיאה בחיפוש</div>';
                        cleanupSearch();
                    }
                }, 1000); // Poll every second
                
            } catch (error) {
                console.error('Live polling error:', error);
                document.getElementById('results').innerHTML = 
                    '<div class="error">שגיאה בחיפוש: ' + error.message + '</div>';
                cleanupSearch();
            }
        }
        
        function cleanupSearch() {
            isSearching = false;
            document.getElementById('loading').style.display = 'none';
            document.getElementById('cancelBtn').style.display = 'none';
            document.getElementById('searchBtn').disabled = false;
            document.getElementById('progressContainer').style.display = 'none';
            document.getElementById('partialResults').style.display = 'none';
        }
        
        // Function to cancel an ongoing search
        function cancelSearch() {
            if (!isSearching) return;
            
            // If using EventSource for streaming
            if (window.currentEventSource) {
                window.currentEventSource.close();
                window.currentEventSource = null;
            }
            
            // If using polling
            if (window.currentPollInterval) {
                clearInterval(window.currentPollInterval);
                window.currentPollInterval = null;
            }
            
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
                
                searchJobId = null;
            }
            
            // Update UI
            isSearching = false;
            document.getElementById('loading').style.display = 'none';
            document.getElementById('cancelBtn').style.display = 'none';
            document.getElementById('searchBtn').disabled = false;
            document.getElementById('progressContainer').style.display = 'none';
            document.getElementById('partialResults').innerHTML = '';
            document.getElementById('results').innerHTML = 
                '<div class="error">החיפוש בוטל על ידי המשתמש</div>';
        }
        
        function updatePartialResults(newResults) {
            console.log("Received partial results:", newResults.length);
            
            // Add new results that aren't already in the partial results
            for (const result of newResults) {
                if (!partialResults.some(r => r.variant === result.variant)) {
                    console.log("Adding new partial result:", result.variant);
                    partialResults.push(result);
                }
            }
            
            // Always show the partial results container, even if empty
            document.getElementById('partialResults').style.display = 'block';
            
            // Display partial results
            if (partialResults.length > 0) {
                let html = `<div style="font-weight: bold; color: #2c3e50; margin-bottom: 10px; font-size: 18px;">
                    תוצאות חלקיות שנמצאו עד כה: ${partialResults.length} (החיפוש עדיין מתבצע)
                </div>`;
                
                // Get the original search term from the input field
                const searchTerm = document.getElementById('searchInput').value.trim();
                
                // Display all partial results with real-time updates
                partialResults.forEach((result, index) => {
                    html += `<div class="partial-result-item">`;
                    
                    // Create a table-like structure with 3 rows
                    html += `<div class="variant-table">`;
                    // Row 1: Original search term
                    html += `<div class="variant-row"><div class="variant-cell">מילה מקורית:</div><div class="variant-cell">${searchTerm}</div></div>`;
                    // Row 2: Sources
                    html += `<div class="variant-row"><div class="variant-cell">מקורות:</div><div class="variant-cell">${result.sources.join(', ')}</div></div>`;
                    // Row 3: Variant
                    html += `<div class="variant-row"><div class="variant-cell">וריאציה:</div><div class="variant-cell">${result.variant}</div></div>`;
                    html += `</div>`; // End variant-table
                    
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
        
        // Store the original search results for filtering
        let originalSearchResults = null;
        
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
            
            // Store the original results for filtering
            originalSearchResults = data;
            
            // Collect all unique sources and books for filters
            const allSources = new Set();
            data.results.forEach(result => {
                result.sources.forEach(source => allSources.add(source));
            });
            
            // Populate the source filter dropdown
            const sourceFilter = document.getElementById('sourceFilter');
            sourceFilter.innerHTML = '<option value="all">כל המקורות</option>';
            Array.from(allSources).sort().forEach(source => {
                sourceFilter.innerHTML += `<option value="${source}">${source}</option>`;
            });
            
            // Show the filters section
            document.getElementById('filtersSection').style.display = 'block';
            
            let html = '<div class="stats">';
            html += '<strong>נמצאו ' + data.total_variants + ' וריאציות</strong><br>';
            html += 'זמן חיפוש: ' + data.search_time + ' שניות';
            html += '</div>';
            
            // Get the original search term
            const searchTerm = data.input_phrase;
            
            data.results.forEach((result, index) => {
                const resultId = 'result-' + index;
                html += '<div class="result-item">';
                
                // Collapsible variant header
                html += '<div class="variant-header" data-result-id="' + resultId + '">';
                html += '<div class="variant-toggle">▼</div>';
                
                // Create a table-like structure with 3 rows
                html += '<div class="variant-table">';
                // Row 1: Original search term
                html += '<div class="variant-row"><div class="variant-cell">מילה מקורית:</div><div class="variant-cell">' + searchTerm + '</div></div>';
                // Row 2: Sources
                html += '<div class="variant-row"><div class="variant-cell">מקורות:</div><div class="variant-cell">' + result.sources.join(', ') + '</div></div>';
                // Row 3: Variant - make it clickable
                html += '<div class="variant-row"><div class="variant-cell">וריאציה:</div><div class="variant-cell"><span class="clickable-variant" data-variant="' + result.variant + '" data-sources="' + result.sources.join(',') + '">' + result.variant + '</span></div></div>';
                html += '</div>'; // End variant-table
                
                html += '</div>'; // End variant-header
                
                // Collapsible locations container
                html += '<div id="' + resultId + '" class="locations-container">';
                
                result.locations.forEach((location, locIndex) => {
                    const locationId = `${resultId}-loc-${locIndex}`;
                    html += '<div class="location" id="' + locationId + '">';
                    
                    // Make location header clickable for context search
                    const locationData = `data-book="${location.book}" data-chapter="${location.chapter}" data-verse="${location.verse}"`;
                    html += `<div class="location-header clickable-location" ${locationData}>
                        ${location.book} פרק ${location.chapter}, פסוק ${location.verse}
                    </div>`;
                    
                    // Make highlighted words NOT clickable as requested
                    const highlightedText = location.text.replace(/\[([^\]]+)\]/g, 
                        `<span class="highlight">$1</span>`);
                    
                    html += '<div class="verse-text">' + highlightedText + '</div>';
                    html += '</div>';
                });
                
                html += '</div>'; // End locations-container
                html += '</div>'; // End result-item
            });
            
            resultsDiv.innerHTML = html;
            
            // Initialize all location containers as collapsed by default
            data.results.forEach((result, index) => {
                const container = document.getElementById('result-' + index);
                if (container) {
                    // Add collapsed class
                    container.classList.add('collapsed');
                    container.style.maxHeight = '0';
                    
                    // Update toggle icon
                    const toggle = document.querySelector(`[data-result-id="result-${index}"] .variant-toggle`);
                    if (toggle) {
                        toggle.classList.add('collapsed');
                        toggle.textContent = '◀';
                    }
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
            
            // Add click event listeners to all clickable variants
            console.log("Setting up clickable variants:", document.querySelectorAll('.clickable-variant').length);
            document.querySelectorAll('.clickable-variant').forEach(variant => {
                console.log("Adding click listener to variant:", variant.textContent);
                variant.addEventListener('click', function(e) {
                    console.log("Variant clicked:", this.textContent);
                    e.stopPropagation(); // Prevent triggering the variant header click
                    
                    // Get variant data
                    const variantText = this.getAttribute('data-variant');
                    const sources = this.getAttribute('data-sources');
                    
                    // Get location data if available
                    const book = this.getAttribute('data-book');
                    const chapter = this.getAttribute('data-chapter');
                    const verse = this.getAttribute('data-verse');
                    
                    // Show context search modal
                    showSearchContextModal(variantText, sources, book, chapter, verse);
                });
            });
            
            // Add click event listeners to all clickable location headers
            console.log("Setting up clickable locations:", document.querySelectorAll('.clickable-location').length);
            document.querySelectorAll('.clickable-location').forEach(location => {
                console.log("Adding click listener to location:", location.textContent.trim());
                location.addEventListener('click', function(e) {
                    console.log("Location clicked:", this.textContent.trim());
                    e.stopPropagation(); // Prevent triggering the variant header click
                    
                    // Get location data
                    const book = this.getAttribute('data-book');
                    const chapter = this.getAttribute('data-chapter');
                    const verse = this.getAttribute('data-verse');
                    
                    console.log("Location data:", book, chapter, verse);
                    
                    // Show context search modal with empty variant text
                    // This will allow the user to enter a new search term
                    showLocationSearchModal(book, chapter, verse);
                });
            });
            
            // Set up filter buttons
            document.getElementById('applyFiltersBtn').addEventListener('click', applyFilters);
            document.getElementById('resetFiltersBtn').addEventListener('click', resetFilters);
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
        
        // Function to show the search context modal
        function showSearchContextModal(variantText, sources, book, chapter, verse) {
            // Set the variant text in the modal
            document.getElementById('contextVariantText').textContent = variantText;
            
            // Create modal if it doesn't exist
            let modal = document.getElementById('searchContextModal');
            if (!modal) {
                modal = document.createElement('div');
                modal.id = 'searchContextModal';
                modal.className = 'search-context-modal';
                
                const content = `
                    <div class="search-context-content">
                        <div class="search-context-title">חיפוש נוסף עבור: <span id="contextVariantText">${variantText}</span></div>
                        <div>בחר את ההקשר לחיפוש:</div>
                        <div class="search-context-options">
                            <button id="searchInVerse" class="search-context-option">חפש בפסוק</button>
                            <button id="searchInChapter" class="search-context-option">חפש בפרק</button>
                        </div>
                        <button id="closeContextModal" class="search-context-close">סגור</button>
                    </div>
                `;
                
                modal.innerHTML = content;
                document.body.appendChild(modal);
            }
            
            // Display the modal
            modal.style.display = 'flex';
            
            // Set up event listeners for the modal buttons
            document.getElementById('searchInVerse').onclick = function() {
                performContextSearch(variantText, 'verse', book, chapter, verse);
                modal.style.display = 'none';
            };
            
            document.getElementById('searchInChapter').onclick = function() {
                performContextSearch(variantText, 'chapter', book, chapter, verse);
                modal.style.display = 'none';
            };
            
            document.getElementById('closeContextModal').onclick = function() {
                modal.style.display = 'none';
            };
            
            // Close modal when clicking outside
            modal.onclick = function(event) {
                if (event.target === modal) {
                    modal.style.display = 'none';
                }
            };
        }
        
        // Function to perform context search
        function performContextSearch(variantText, contextType, book, chapter, verse) {
            // Log the search parameters
            console.log("Context search parameters:", {
                variantText,
                contextType,
                book,
                chapter,
                verse
            });
            
            // Construct the search query based on context type
            if (contextType === 'verse' && verse) {
                // Search in specific verse
                document.getElementById('searchInput').value = `${variantText} book:${book} chapter:${chapter} verse:${verse}`;
            } else if (contextType === 'chapter') {
                // Search in specific chapter
                document.getElementById('searchInput').value = `${variantText} book:${book} chapter:${chapter}`;
            } else {
                // Just search for the variant text
                document.getElementById('searchInput').value = variantText;
            }
            
            // Execute the search
            search();
        }
        
        // Function to apply filters to search results
        function applyFilters() {
            if (!originalSearchResults) return;
            
            const bookFilter = document.getElementById('bookFilter').value;
            const sourceFilter = document.getElementById('sourceFilter').value;
            
            console.log("Applying filters:", { bookFilter, sourceFilter });
            
            // Clone the original results
            const filteredData = JSON.parse(JSON.stringify(originalSearchResults));
            const filteredResults = [];
            
            // Apply filters to each result
            for (const result of filteredData.results) {
                // Filter by source
                if (sourceFilter !== 'all' && !result.sources.includes(sourceFilter)) {
                    continue;
                }
                
                // Filter locations by book
                if (bookFilter !== 'all') {
                    const filteredLocations = result.locations.filter(location => 
                        location.book === bookFilter
                    );
                    
                    if (filteredLocations.length > 0) {
                        // Update the result with filtered locations
                        result.locations = filteredLocations;
                        filteredResults.push(result);
                    }
                } else {
                    // No book filter, include all locations
                    filteredResults.push(result);
                }
            }
            
            // Update the filtered data
            filteredData.results = filteredResults;
            filteredData.total_variants = filteredResults.length;
            
            // Display the filtered results
            renderResults(filteredData);
            
            // Update stats
            const statsDiv = document.querySelector('.stats');
            if (statsDiv) {
                statsDiv.innerHTML = `<strong>נמצאו ${filteredResults.length} וריאציות</strong> (מתוך ${originalSearchResults.total_variants} סך הכל)<br>`;
                statsDiv.innerHTML += `סינון: ${bookFilter === 'all' ? 'כל הספרים' : bookFilter}, ${sourceFilter === 'all' ? 'כל המקורות' : sourceFilter}`;
            }
        }
        
        // Function to reset filters
        function resetFilters() {
            document.getElementById('bookFilter').value = 'all';
            document.getElementById('sourceFilter').value = 'all';
            
            if (originalSearchResults) {
                renderResults(originalSearchResults);
                
                // Update stats
                const statsDiv = document.querySelector('.stats');
                if (statsDiv) {
                    statsDiv.innerHTML = `<strong>נמצאו ${originalSearchResults.total_variants} וריאציות</strong><br>`;
                    statsDiv.innerHTML += `זמן חיפוש: ${originalSearchResults.search_time} שניות`;
                }
            }
        }
        
        // Function to render results (separated from displayResults for reuse)
        function renderResults(data) {
            const resultsDiv = document.getElementById('results');
            
            // Clear existing results except stats
            const statsDiv = document.querySelector('.stats');
            resultsDiv.innerHTML = '';
            if (statsDiv) {
                resultsDiv.appendChild(statsDiv);
            }
            
            // Get the original search term
            const searchTerm = data.input_phrase;
            
            data.results.forEach((result, index) => {
                const resultId = 'result-' + index;
                const resultItem = document.createElement('div');
                resultItem.className = 'result-item';
                
                // Collapsible variant header
                let html = '<div class="variant-header" data-result-id="' + resultId + '">';
                html += '<div class="variant-toggle">▼</div>';
                
                // Create a table-like structure with 3 rows
                html += '<div class="variant-table">';
                // Row 1: Original search term
                html += '<div class="variant-row"><div class="variant-cell">מילה מקורית:</div><div class="variant-cell">' + searchTerm + '</div></div>';
                // Row 2: Sources
                html += '<div class="variant-row"><div class="variant-cell">מקורות:</div><div class="variant-cell">' + result.sources.join(', ') + '</div></div>';
                // Row 3: Variant - make it clickable
                html += '<div class="variant-row"><div class="variant-cell">וריאציה:</div><div class="variant-cell"><span class="clickable-variant" data-variant="' + result.variant + '" data-sources="' + result.sources.join(',') + '">' + result.variant + '</span></div></div>';
                html += '</div>'; // End variant-table
                
                html += '</div>'; // End variant-header
                
                // Collapsible locations container
                html += '<div id="' + resultId + '" class="locations-container">';
                
                result.locations.forEach((location, locIndex) => {
                    const locationId = `${resultId}-loc-${locIndex}`;
                    html += '<div class="location" id="' + locationId + '">';
                    
                    // Make location header clickable for context search
                    const locationData = `data-book="${location.book}" data-chapter="${location.chapter}" data-verse="${location.verse}"`;
                    html += `<div class="location-header clickable-location" ${locationData}>
                        ${location.book} פרק ${location.chapter}, פסוק ${location.verse}
                    </div>`;
                    
                    // Make highlighted words NOT clickable as requested
                    const highlightedText = location.text.replace(/\[([^\]]+)\]/g, 
                        `<span class="highlight">$1</span>`);
                    
                    html += '<div class="verse-text">' + highlightedText + '</div>';
                    html += '</div>';
                });
                
                html += '</div>'; // End locations-container
                
                resultItem.innerHTML = html;
                resultsDiv.appendChild(resultItem);
            });
            
            // Initialize all location containers as collapsed by default
            data.results.forEach((result, index) => {
                const container = document.getElementById('result-' + index);
                if (container) {
                    // Add collapsed class
                    container.classList.add('collapsed');
                    container.style.maxHeight = '0';
                    
                    // Update toggle icon
                    const toggle = document.querySelector(`[data-result-id="result-${index}"] .variant-toggle`);
                    if (toggle) {
                        toggle.classList.add('collapsed');
                        toggle.textContent = '◀';
                    }
                }
            });
            
            // Add click event listeners to all variant headers
            document.querySelectorAll('.variant-header').forEach(header => {
                header.addEventListener('click', function() {
                    const resultId = this.getAttribute('data-result-id');
                    toggleVariant(resultId);
                });
            });
            
            // Add click event listeners to all clickable variants
            document.querySelectorAll('.clickable-variant').forEach(variant => {
                variant.addEventListener('click', function(e) {
                    e.stopPropagation(); // Prevent triggering the variant header click
                    
                    // Get variant data
                    const variantText = this.getAttribute('data-variant');
                    const sources = this.getAttribute('data-sources');
                    
                    // Get location data if available
                    const book = this.getAttribute('data-book');
                    const chapter = this.getAttribute('data-chapter');
                    const verse = this.getAttribute('data-verse');
                    
                    // Show context search modal
                    showSearchContextModal(variantText, sources, book, chapter, verse);
                });
            });
            
            // Add click event listeners to all clickable location headers
            document.querySelectorAll('.clickable-location').forEach(location => {
                location.addEventListener('click', function(e) {
                    e.stopPropagation(); // Prevent triggering the variant header click
                    
                    // Get location data
                    const book = this.getAttribute('data-book');
                    const chapter = this.getAttribute('data-chapter');
                    const verse = this.getAttribute('data-verse');
                    
                    // Show context search modal with empty variant text
                    showLocationSearchModal(book, chapter, verse);
                });
            });
        }
        
        // Function to show the location search modal
        function showLocationSearchModal(book, chapter, verse) {
            // Set the location text in the modal
            let locationText = '';
            if (verse) {
                locationText = `${book} פרק ${chapter}, פסוק ${verse}`;
            } else {
                locationText = `${book} פרק ${chapter}`;
            }
            
            // Create modal if it doesn't exist
            let modal = document.getElementById('locationSearchModal');
            if (!modal) {
                modal = document.createElement('div');
                modal.id = 'locationSearchModal';
                modal.className = 'search-context-modal';
                
                const content = `
                    <div class="search-context-content">
                        <div class="search-context-title">חיפוש חדש ב<span id="locationContextText"></span></div>
                        <div>הכנס מילה לחיפוש:</div>
                        <div style="margin: 20px 0;">
                            <input type="text" id="locationSearchInput" placeholder="הכנס מילה או ביטוי..." style="padding: 10px; width: 80%; text-align: right; direction: rtl;" />
                        </div>
                        <div class="search-context-options">
                            <button id="searchLocationVerse" class="search-context-option">חפש בפסוק</button>
                            <button id="searchLocationChapter" class="search-context-option">חפש בפרק</button>
                        </div>
                        <button id="closeLocationModal" class="search-context-close">סגור</button>
                    </div>
                `;
                
                modal.innerHTML = content;
                document.body.appendChild(modal);
            }
            
            // Set the location text
            document.getElementById('locationContextText').textContent = locationText;
            
            // Clear the input field
            const inputField = document.getElementById('locationSearchInput');
            if (inputField) {
                inputField.value = '';
            }
            
            // Display the modal
            modal.style.display = 'flex';
            
            // Focus the input field
            setTimeout(() => {
                document.getElementById('locationSearchInput').focus();
            }, 100);
            
            // Set up event listeners for the modal buttons
            document.getElementById('searchLocationVerse').onclick = function() {
                const searchTerm = document.getElementById('locationSearchInput').value.trim();
                if (searchTerm) {
                    performContextSearch(searchTerm, 'verse', book, chapter, verse);
                    modal.style.display = 'none';
                } else {
                    alert('אנא הכנס מילה או ביטוי לחיפוש');
                }
            };
            
            document.getElementById('searchLocationChapter').onclick = function() {
                const searchTerm = document.getElementById('locationSearchInput').value.trim();
                if (searchTerm) {
                    performContextSearch(searchTerm, 'chapter', book, chapter, verse);
                    modal.style.display = 'none';
                } else {
                    alert('אנא הכנס מילה או ביטוי לחיפוש');
                }
            };
            
            document.getElementById('closeLocationModal').onclick = function() {
                modal.style.display = 'none';
            };
            
            // Close modal when clicking outside
            modal.onclick = function(event) {
                if (event.target === modal) {
                    modal.style.display = 'none';
                }
            };
            
            // Add enter key handler for the input field
            document.getElementById('locationSearchInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    const searchTerm = this.value.trim();
                    if (searchTerm) {
                        performContextSearch(searchTerm, 'verse', book, chapter, verse);
                        modal.style.display = 'none';
                    } else {
                        alert('אנא הכנס מילה או ביטוי לחיפוש');
                    }
                }
            });
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
