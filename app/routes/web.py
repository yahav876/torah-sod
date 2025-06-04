"""
Web routes for Torah Search
"""
from flask import Blueprint, render_template_string, current_app
from app.app_factory import cache
import structlog

logger = structlog.get_logger()

bp = Blueprint('web', __name__)


@bp.route('/')
@cache.cached(timeout=300)
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
