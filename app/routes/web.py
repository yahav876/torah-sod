"""
Web routes for Torah Search
"""
from flask import Blueprint, render_template_string, current_app, request, redirect, url_for, session, flash
from app.app_factory import cache
import structlog
import os
from functools import wraps

logger = structlog.get_logger()

bp = Blueprint('web', __name__)

# Admin credentials - in a real app, these would be stored securely
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "torah123"  # This should be hashed in a real application

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('web.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

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


@bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page."""
    error = None
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('web.admin'))
        else:
            error = 'שם משתמש או סיסמה שגויים'
    
    return render_template_string(get_admin_login_template(), error=error)


@bp.route('/admin')
@login_required
def admin():
    """Admin dashboard."""
    return render_template_string(get_admin_template())


@bp.route('/admin/logout')
def admin_logout():
    """Admin logout."""
    session.pop('logged_in', None)
    return redirect(url_for('web.index'))


def get_main_template():
    """Return the main search interface template."""
    return """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Torah Search - חיפוש בתורה</title>
    <link rel="icon" href="/favicon.ico?v=2" type="image/x-icon">
    <link rel="shortcut icon" href="/favicon.ico?v=2" type="image/x-icon">
    <!-- Force favicon refresh with different approaches -->
    <link rel="apple-touch-icon" href="/favicon.ico?v=2">
    <meta name="msapplication-TileImage" content="/favicon.ico?v=2">
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
        <!-- בס״ד in top right corner -->
        <div style="position: absolute; top: 10px; right: 20px; font-size: 14px;">בס״ד</div>
        
        <!-- About button in top left corner -->
        <div style="position: absolute; top: 10px; left: 20px;">
            <a href="/about" class="about-btn" style="padding: 8px 15px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; box-shadow: 0 2px 5px rgba(0,0,0,0.2); transition: all 0.2s;">אודות</a>
        </div>
        
        <div class="header">
            <a href="/" style="text-decoration: none; color: inherit;">
                <h1>🔍 חיפוש בתורה</h1>
                <p>חיפוש מילים בתורה בעזרת שיטות החלפת אותיות שונות</p>
            </a>
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
                    <a href="/admin" class="admin-btn" style="display: inline-block; text-decoration: none;">כניסה למנהל</a>
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
                        <div id="bookFilterContainer" class="checkbox-group" style="max-height: 150px; overflow-y: auto; border: 1px solid #ddd; border-radius: 5px; padding: 8px;">
                            <!-- Will be populated dynamically -->
                        </div>
                    </div>
                    
                    <!-- Source Filter -->
                    <div style="min-width: 200px;">
                        <div style="font-weight: bold; margin-bottom: 5px;">סינון לפי מקור:</div>
                        <div id="sourceFilterContainer" class="checkbox-group" style="max-height: 150px; overflow-y: auto; border: 1px solid #ddd; border-radius: 5px; padding: 8px;">
                            <!-- Will be populated dynamically -->
                        </div>
                    </div>
                </div>
                
                <style>
                    .checkbox-group {
                        display: flex;
                        flex-direction: column;
                        gap: 5px;
                    }
                    .checkbox-group label {
                        display: flex;
                        align-items: center;
                        cursor: pointer;
                        padding: 3px;
                        border-radius: 3px;
                    }
                    .checkbox-group label:hover {
                        background-color: #f0f0f0;
                    }
                    .checkbox-group input[type="checkbox"] {
                        margin-left: 8px;
                    }
                </style>
                
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
                <button id="backToResults" class="search-context-option" style="background-color: #e67e22;">חזור לתוצאות</button>
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
                <button id="backToPreviousResultsBtn" class="search-context-option" style="background-color: #e67e22;">חזור לתוצאות הקודמות</button>
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
            
            // Check if we need to show the "Back to Previous Results" button
            checkAndShowBackButton();
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
            
            // Check if this is a context search (contains book: or chapter: or verse:)
            const isContextSearch = data.input_phrase && 
                (data.input_phrase.includes('book:') || 
                 data.input_phrase.includes('chapter:') || 
                 data.input_phrase.includes('verse:'));
            
            // If this is a context search, add a history entry to allow browser back button navigation
            if (isContextSearch && sessionStorage.getItem('previousSearchResults')) {
                // Add a history entry for the current search
                if (window.history && window.history.pushState) {
                    // Add a state object with the current search results
                    window.history.pushState(
                        { contextSearch: true },
                        document.title,
                        window.location.pathname + window.location.search
                    );
                }
            }
            
            // Collect all unique sources and books for filters
            const allSources = new Set();
            const allBooks = new Set();
            
            data.results.forEach(result => {
                // Add sources
                result.sources.forEach(source => allSources.add(source));
                
                // Add books
                result.locations.forEach(location => {
                    allBooks.add(location.book);
                });
            });
            
            // Populate the book filter checkboxes
            const bookFilterContainer = document.getElementById('bookFilterContainer');
            bookFilterContainer.innerHTML = '';
            
            // Add "Select All" checkbox for books
            const selectAllBooksLabel = document.createElement('label');
            selectAllBooksLabel.innerHTML = `<input type="checkbox" class="select-all-books" checked> בחר הכל`;
            selectAllBooksLabel.style.fontWeight = 'bold';
            selectAllBooksLabel.style.borderBottom = '1px solid #ddd';
            selectAllBooksLabel.style.paddingBottom = '5px';
            selectAllBooksLabel.style.marginBottom = '5px';
            bookFilterContainer.appendChild(selectAllBooksLabel);
            
            // Add individual book checkboxes
            Array.from(allBooks).sort().forEach(book => {
                const label = document.createElement('label');
                label.innerHTML = `<input type="checkbox" name="bookFilter" value="${book}" checked> ${book}`;
                bookFilterContainer.appendChild(label);
            });
            
            // Define the 9 standard map options
            const standardMaps = [
                "אב״גד",
                "את״בש",
                "אל״במ",
                "אט״בח",
                "איק-בכר",
                "אחס-בטע",
                "מוצאות-הפה",
                "אהוי",
                "מקור"
            ];
            
            // Populate the source filter checkboxes
            const sourceFilterContainer = document.getElementById('sourceFilterContainer');
            sourceFilterContainer.innerHTML = '';
            
            // Add "Select All" checkbox for sources
            const selectAllSourcesLabel = document.createElement('label');
            selectAllSourcesLabel.innerHTML = `<input type="checkbox" class="select-all-sources" checked> בחר הכל`;
            selectAllSourcesLabel.style.fontWeight = 'bold';
            selectAllSourcesLabel.style.borderBottom = '1px solid #ddd';
            selectAllSourcesLabel.style.paddingBottom = '5px';
            selectAllSourcesLabel.style.marginBottom = '5px';
            sourceFilterContainer.appendChild(selectAllSourcesLabel);
            
            // Always add all 9 standard maps, but highlight the ones that exist in the results
            standardMaps.forEach(map => {
                const label = document.createElement('label');
                const exists = allSources.has(map);
                label.innerHTML = `<input type="checkbox" name="sourceFilter" value="${map}" checked> ${map}`;
                
                // Highlight maps that exist in the results
                if (exists) {
                    label.style.fontWeight = 'bold';
                }
                
                sourceFilterContainer.appendChild(label);
            });
            
            // Add event listeners for "Select All" checkboxes
            document.querySelector('.select-all-books').addEventListener('change', function() {
                const isChecked = this.checked;
                document.querySelectorAll('input[name="bookFilter"]').forEach(checkbox => {
                    checkbox.checked = isChecked;
                });
            });
            
            document.querySelector('.select-all-sources').addEventListener('change', function() {
                const isChecked = this.checked;
                document.querySelectorAll('input[name="sourceFilter"]').forEach(checkbox => {
                    checkbox.checked = isChecked;
                });
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
                // Row 3: Variant - no longer clickable
                html += '<div class="variant-row"><div class="variant-cell">וריאציה:</div><div class="variant-cell">' + result.variant + '</div></div>';
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
            
            // Removed clickable variants event listeners as requested
            
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
        
        // Function to clear all search caches - moved to admin page
        
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
            
            document.getElementById('backToResults').onclick = function() {
                // Just close the modal without performing a new search
                // This will effectively return to the current search results
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
            
            // Store current search results for back button functionality
            if (originalSearchResults) {
                // Save the current search results to session storage
                sessionStorage.setItem('previousSearchResults', JSON.stringify(originalSearchResults));
                sessionStorage.setItem('isPreviousSearch', 'true');
            }
            
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
        
        // Function to check if we need to show the "Back to Previous Results" button
        function checkAndShowBackButton() {
            console.log("Checking for previous search results...");
            // Check if we have previous search results in session storage
            const hasPreviousResults = sessionStorage.getItem('isPreviousSearch') === 'true';
            console.log("Has previous results:", hasPreviousResults);
            
            if (hasPreviousResults) {
                console.log("Creating back button...");
                // Create the back button if it doesn't exist
                let backButton = document.getElementById('backToPreviousResults');
                if (!backButton) {
                    backButton = document.createElement('button');
                    backButton.id = 'backToPreviousResults';
                    backButton.className = 'control-btn';
                    backButton.style.backgroundColor = '#e67e22';
                    backButton.style.marginBottom = '20px';
                    backButton.style.fontSize = '18px';
                    backButton.style.padding = '15px 30px';
                    backButton.textContent = 'חזור לתוצאות הקודמות';
                    
                    // Add click event listener
                    backButton.addEventListener('click', function() {
                        console.log("Back button clicked");
                        // Get the previous search results from session storage
                        const previousResults = JSON.parse(sessionStorage.getItem('previousSearchResults'));
                        if (previousResults) {
                            console.log("Displaying previous results");
                            // Display the previous search results
                            displayResults(previousResults);
                            
                            // Clear the session storage
                            sessionStorage.removeItem('previousSearchResults');
                            sessionStorage.removeItem('isPreviousSearch');
                            
                            // Remove the back button
                            this.remove();
                        }
                    });
                    
                    // Insert the back button at the top of the results
                    const resultsDiv = document.getElementById('results');
                    if (resultsDiv.firstChild) {
                        resultsDiv.insertBefore(backButton, resultsDiv.firstChild);
                    } else {
                        resultsDiv.appendChild(backButton);
                    }
                    
                    console.log("Back button created and inserted");
                }
            }
        }
        
        // Function to apply filters to search results
        function applyFilters() {
            if (!originalSearchResults) {
                console.error("No original search results available");
                return;
            }
            
            // Get selected books
            const selectedBooks = [];
            document.querySelectorAll('input[name="bookFilter"]:checked').forEach(checkbox => {
                selectedBooks.push(checkbox.value);
            });
            
            // Get selected sources
            const selectedSources = [];
            document.querySelectorAll('input[name="sourceFilter"]:checked').forEach(checkbox => {
                selectedSources.push(checkbox.value);
            });
            
            console.log("Applying filters:", { 
                selectedBooks, 
                selectedSources,
                originalResultsCount: originalSearchResults.results.length
            });
            
            // Check if any filters are selected
            if (selectedBooks.length === 0 || selectedSources.length === 0) {
                // No filters selected, show a message
                document.getElementById('results').innerHTML = 
                    '<div class="error">אנא בחר לפחות ספר אחד ומקור אחד</div>';
                return;
            }
            
            try {
                // Create a completely new filtered data object
                const filteredData = {
                    success: true,
                    input_phrase: originalSearchResults.input_phrase,
                    search_time: originalSearchResults.search_time,
                    total_variants: 0,
                    results: []
                };
                
                // Apply filters to each result
                for (let i = 0; i < originalSearchResults.results.length; i++) {
                    const originalResult = originalSearchResults.results[i];
                    
                    // Debug
                    console.log(`Processing result ${i}:`, {
                        variant: originalResult.variant,
                        sources: originalResult.sources,
                        locationsCount: originalResult.locations.length
                    });
                    
                    // Check if any of the result's sources are in the selected sources
                    const hasSelectedSource = originalResult.sources.some(source => 
                        selectedSources.includes(source)
                    );
                    
                    // Skip if none of the result's sources are selected
                    if (!hasSelectedSource) {
                        console.log(`Result ${i} skipped: no matching sources`);
                        continue;
                    }
                    
                    // Filter locations by selected books
                    const filteredLocations = originalResult.locations.filter(location => 
                        selectedBooks.includes(location.book)
                    );
                    
                    console.log(`Result ${i} filtered locations:`, filteredLocations.length);
                    
                    // Only add the result if it has matching locations
                    if (filteredLocations.length > 0) {
                        // Create a new result object with filtered locations
                        const filteredResult = {
                            variant: originalResult.variant,
                            sources: [...originalResult.sources],
                            locations: filteredLocations
                        };
                        
                        filteredData.results.push(filteredResult);
                    }
                }
                
                // Update total variants count
                filteredData.total_variants = filteredData.results.length;
                
                console.log("Filtered results:", {
                    totalResults: filteredData.results.length,
                    firstResult: filteredData.results.length > 0 ? {
                        variant: filteredData.results[0].variant,
                        locationsCount: filteredData.results[0].locations.length
                    } : null
                });
                
            // Display the filtered results
            renderResults(filteredData);
            
            // Update stats
            const statsDiv = document.querySelector('.stats');
            if (statsDiv) {
                statsDiv.innerHTML = `<strong>נמצאו ${filteredData.results.length} וריאציות</strong> (מתוך ${originalSearchResults.total_variants} סך הכל)<br>`;
                statsDiv.innerHTML += `סינון: ${selectedBooks.length} ספרים, ${selectedSources.length} מקורות`;
            }
            
            // Check if we need to show the "Back to Previous Results" button
            checkAndShowBackButton();
                
                // Show the results controls
                document.getElementById('resultsControls').style.display = 'block';
            } catch (error) {
                console.error("Error applying filters:", error);
                document.getElementById('results').innerHTML = 
                    '<div class="error">שגיאה בסינון התוצאות: ' + error.message + '</div>';
            }
        }
        
        // Function to reset filters
        function resetFilters() {
            // Check all book checkboxes
            document.querySelectorAll('input[name="bookFilter"]').forEach(checkbox => {
                checkbox.checked = true;
            });
            
            // Check all source checkboxes
            document.querySelectorAll('input[name="sourceFilter"]').forEach(checkbox => {
                checkbox.checked = true;
            });
            
            // Check the "Select All" checkboxes
            document.querySelector('.select-all-books').checked = true;
            document.querySelector('.select-all-sources').checked = true;
            
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
                // Row 3: Variant - no longer clickable
                html += '<div class="variant-row"><div class="variant-cell">וריאציה:</div><div class="variant-cell">' + result.variant + '</div></div>';
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
            
            // Removed clickable variants event listeners as requested
            
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
            
            document.getElementById('backToPreviousResultsBtn').onclick = function() {
                // Get the previous search results from session storage
                const previousResults = JSON.parse(sessionStorage.getItem('previousSearchResults'));
                if (previousResults) {
                    console.log("Displaying previous results from modal");
                    // Display the previous search results
                    displayResults(previousResults);
                    
                    // Clear the session storage
                    sessionStorage.removeItem('previousSearchResults');
                    sessionStorage.removeItem('isPreviousSearch');
                    
                    // Close the modal
                    modal.style.display = 'none';
                } else {
                    // If no previous results, just close the modal
                    modal.style.display = 'none';
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
    <link rel="icon" href="/favicon.ico?v=2" type="image/x-icon">
    <link rel="shortcut icon" href="/favicon.ico?v=2" type="image/x-icon">
    <!-- Force favicon refresh with different approaches -->
    <link rel="apple-touch-icon" href="/favicon.ico?v=2">
    <meta name="msapplication-TileImage" content="/favicon.ico?v=2">
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
            position: relative;
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
        
        .about-btn {
            position: absolute;
            top: 10px;
            left: 20px;
            padding: 8px 15px;
            background-color: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
        }
        
        .about-btn:hover {
            background-color: #2980b9;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- בס״ד in top right corner -->
        <div style="position: absolute; top: 10px; right: 20px; font-size: 14px;">בס״ד</div>
        
        <!-- Home button in top left corner -->
        <div style="position: absolute; top: 10px; left: 20px;">
            <a href="/" class="about-btn">דף הבית</a>
        </div>
        
        <h1>אודות המערכת</h1>
        <p>מערכת חיפוש בתורה המאפשרת לחפש מילים וביטויים בעזרת שיטות החלפת אותיות שונות.</p>
        <p>המערכת משתמשת בטכנולוגיות מתקדמות לחיפוש מהיר ויעיל בטקסט התורה.</p>
    </div>
</body>
</html>
"""


def get_admin_login_template():
    """Return the admin login template."""
    return """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>כניסת מנהל - Torah Search</title>
    <link rel="icon" href="/favicon.ico?v=2" type="image/x-icon">
    <link rel="shortcut icon" href="/favicon.ico?v=2" type="image/x-icon">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            direction: rtl;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .login-container {
            width: 100%;
            max-width: 400px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            padding: 40px;
            text-align: center;
        }
        
        h1 {
            color: #2c3e50;
            margin-bottom: 30px;
        }
        
        .form-group {
            margin-bottom: 20px;
            text-align: right;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #34495e;
        }
        
        input[type="text"],
        input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        
        button {
            background: #3498db;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
            font-weight: bold;
        }
        
        button:hover {
            background: #2980b9;
        }
        
        .error {
            color: #e74c3c;
            margin-bottom: 20px;
            padding: 10px;
            background: #fadbd8;
            border-radius: 5px;
        }
        
        .home-link {
            margin-top: 20px;
            display: block;
            color: #3498db;
            text-decoration: none;
        }
        
        .home-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <!-- בס״ד in top right corner -->
        <div style="position: absolute; top: 10px; right: 20px; font-size: 14px;">בס״ד</div>
        
        <h1>כניסת מנהל</h1>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        <form method="post">
            <div class="form-group">
                <label for="username">שם משתמש:</label>
                <input type="text" id="username" name="username" required>
            </div>
            
            <div class="form-group">
                <label for="password">סיסמה:</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit">כניסה</button>
        </form>
        
        <a href="/" class="home-link">חזרה לדף הבית</a>
    </div>
</body>
</html>
"""


def get_admin_template():
    """Return the admin dashboard template."""
    return """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>לוח בקרה למנהל - Torah Search</title>
    <link rel="icon" href="/favicon.ico?v=2" type="image/x-icon">
    <link rel="shortcut icon" href="/favicon.ico?v=2" type="image/x-icon">
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
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
            padding: 40px;
            position: relative;
        }
        
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }
        
        .admin-section {
            margin-bottom: 40px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            border-right: 5px solid #3498db;
        }
        
        .admin-section h2 {
            color: #2c3e50;
            margin-top: 0;
        }
        
        .admin-btn {
            background: #e74c3c;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            font-weight: bold;
            margin-top: 10px;
        }
        
        .admin-btn:hover {
            background: #c0392b;
        }
        
        .nav-links {
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
        }
        
        .nav-link {
            padding: 10px 15px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
        }
        
        .nav-link:hover {
            background: #2980b9;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .stat-card {
            background: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #3498db;
            margin: 10px 0;
        }
        
        .stat-label {
            color: #7f8c8d;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- בס״ד in top right corner -->
        <div style="position: absolute; top: 10px; right: 20px; font-size: 14px;">בס״ד</div>
        
        <h1>לוח בקרה למנהל</h1>
        
        <div class="nav-links">
            <a href="/" class="nav-link">חזרה לדף הבית</a>
            <a href="/admin/logout" class="nav-link">התנתקות</a>
        </div>
        
        <div class="admin-section">
            <h2>ניהול מטמון</h2>
            <p>ניקוי המטמון ימחק את כל תוצאות החיפוש השמורות ויאלץ את המערכת לחשב אותן מחדש.</p>
            <button id="clearCacheBtn" class="admin-btn">נקה את המטמון</button>
            <button id="addTestStatsBtn" class="admin-btn" style="background: #27ae60; margin-right: 10px;">הוסף נתוני בדיקה</button>
            <div id="cacheStatus" style="margin-top: 10px;"></div>
        </div>
        
        <div class="admin-section">
            <h2>סטטיסטיקות מערכת</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">חיפושים היום</div>
                    <div class="stat-value" id="todaySearches">--</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">סך הכל חיפושים</div>
                    <div class="stat-value" id="totalSearches">--</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">תוצאות במטמון</div>
                    <div class="stat-value" id="cachedResults">--</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">זמן חיפוש ממוצע</div>
                    <div class="stat-value" id="avgSearchTime">--</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Set up clear cache button handler
            document.getElementById('clearCacheBtn').addEventListener('click', function() {
                clearCache();
            });
            
            // Set up add test stats button handler
            document.getElementById('addTestStatsBtn').addEventListener('click', function() {
                addTestStats();
            });
            
            // Load statistics
            loadStats();
        });
        
        // Function to clear all search caches
        async function clearCache() {
            if (!confirm('האם אתה בטוח שברצונך לנקות את כל המטמון? פעולה זו תמחק את כל תוצאות החיפוש השמורות.')) {
                return;
            }
            
            const statusDiv = document.getElementById('cacheStatus');
            statusDiv.innerHTML = '<div style="color: #3498db;">מנקה את המטמון...</div>';
            
            try {
                const response = await fetch('/api/admin/clear-cache', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    statusDiv.innerHTML = '<div style="color: #2ecc71;">המטמון נוקה בהצלחה!</div>';
                    // Reload stats after clearing cache
                    loadStats();
                } else {
                    statusDiv.innerHTML = '<div style="color: #e74c3c;">שגיאה בניקוי המטמון: ' + (data.error || 'שגיאה לא ידועה') + '</div>';
                }
                
            } catch (error) {
                console.error('Error clearing cache:', error);
                statusDiv.innerHTML = '<div style="color: #e74c3c;">שגיאה בניקוי המטמון: ' + error.message + '</div>';
            }
        }
        
        // Function to add test statistics data
        async function addTestStats() {
            if (!confirm('האם אתה בטוח שברצונך להוסיף נתוני בדיקה? פעולה זו תיצור נתוני סטטיסטיקה לצורך בדיקה.')) {
                return;
            }
            
            const statusDiv = document.getElementById('cacheStatus');
            statusDiv.innerHTML = '<div style="color: #3498db;">מוסיף נתוני בדיקה...</div>';
            
            try {
                const response = await fetch('/api/admin/add-test-stats', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    statusDiv.innerHTML = '<div style="color: #2ecc71;">נתוני בדיקה נוספו בהצלחה!</div>';
                    // Reload stats after adding test data
                    loadStats();
                } else {
                    statusDiv.innerHTML = '<div style="color: #e74c3c;">שגיאה בהוספת נתוני בדיקה: ' + (data.error || 'שגיאה לא ידועה') + '</div>';
                }
                
            } catch (error) {
                console.error('Error adding test stats:', error);
                statusDiv.innerHTML = '<div style="color: #e74c3c;">שגיאה בהוספת נתוני בדיקה: ' + error.message + '</div>';
            }
        }
        
        // Function to load statistics
        async function loadStats() {
            try {
                // Add a cache-busting parameter to prevent caching
                const timestamp = new Date().getTime();
                
                // Show loading state
                document.getElementById('totalSearches').textContent = 'Loading...';
                document.getElementById('cachedResults').textContent = 'Loading...';
                document.getElementById('todaySearches').textContent = 'Loading...';
                document.getElementById('avgSearchTime').textContent = 'Loading...';
                
                // Log to console only for debugging
                console.log(`Fetching stats at ${new Date().toISOString()}...`);
                
                const response = await fetch(`/api/stats?_=${timestamp}`);
                const data = await response.json();
                
                // Log to console only
                console.log("Loaded statistics:", data);
                
                if (data) {
                    // Update the UI with the statistics
                    document.getElementById('totalSearches').textContent = data.total_searches || 0;
                    document.getElementById('cachedResults').textContent = data.cached_searches || 0;
                    
                    // Calculate today's searches
                    const todaySearches = data.recent_searches ? 
                        data.recent_searches.filter(s => {
                            const searchDate = new Date(s.timestamp);
                            const today = new Date();
                            return searchDate.toDateString() === today.toDateString();
                        }).length : 0;
                    
                    document.getElementById('todaySearches').textContent = todaySearches;
                    
                    // Calculate average search time
                    if (data.recent_searches && data.recent_searches.length > 0) {
                        const avgTime = data.recent_searches.reduce((sum, s) => sum + s.time, 0) / data.recent_searches.length;
                        document.getElementById('avgSearchTime').textContent = avgTime.toFixed(2) + 's';
                    } else {
                        document.getElementById('avgSearchTime').textContent = '0s';
                    }
                }
                
                // Set up auto-refresh for statistics every 30 seconds
                setTimeout(loadStats, 30000);
                
            } catch (error) {
                console.error('Error loading stats:', error);
                
                // Update UI to show error state
                document.getElementById('totalSearches').textContent = '0';
                document.getElementById('cachedResults').textContent = '0';
                document.getElementById('todaySearches').textContent = '0';
                document.getElementById('avgSearchTime').textContent = '0s';
                
                // Try again after 30 seconds
                setTimeout(loadStats, 30000);
            }
        }
    </script>
</body>
</html>
"""
