from __future__ import annotations

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAG ESG - Test Interface</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header p {
            opacity: 0.9;
        }
        .content {
            padding: 30px;
        }
        .input-section {
            margin-bottom: 30px;
        }
        .input-section label {
            display: block;
            margin-bottom: 10px;
            font-weight: 600;
            color: #333;
        }
        .input-group {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
        }
        .input-group input {
            flex: 1;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 1em;
            transition: border-color 0.3s;
        }
        .input-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        .input-group input[type="number"] {
            flex: 0 0 100px;
        }
        .btn {
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .btn:active {
            transform: translateY(0);
        }
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            color: #667eea;
        }
        .spinner {
            border: 3px solid #e0e0e0;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .results {
            display: none;
        }
        .result-section {
            margin-bottom: 25px;
        }
        .result-title {
            font-size: 1.3em;
            font-weight: 700;
            margin-bottom: 15px;
            color: #333;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }
        .answer-box {
            background: #f5f7fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            line-height: 1.6;
            color: #555;
        }
        .sources {
            display: grid;
            gap: 15px;
        }
        .source-item {
            background: #f9f9f9;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            transition: all 0.3s;
        }
        .source-item:hover {
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }
        .source-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .source-name {
            font-weight: 600;
            color: #333;
        }
        .source-type {
            display: inline-block;
            padding: 3px 10px;
            background: #667eea;
            color: white;
            border-radius: 20px;
            font-size: 0.85em;
            margin-left: 10px;
        }
        .source-rank {
            background: #764ba2;
            color: white;
            padding: 3px 10px;
            border-radius: 3px;
            font-size: 0.85em;
        }
        .source-text {
            color: #666;
            font-size: 0.95em;
            line-height: 1.5;
            margin-bottom: 10px;
        }
        .source-distance {
            font-size: 0.85em;
            color: #999;
        }
        .error {
            background: #fee;
            color: #c00;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #c00;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌍 RAG ESG System</h1>
            <p>Retrieval-Augmented Generation for Environmental, Social & Governance insights</p>
        </div>
        
        <div class="content">
            <div class="input-section">
                <label for="question">Ask your ESG question:</label>
                <div class="input-group">
                    <input 
                        type="text" 
                        id="question" 
                        placeholder="e.g., What are the main environmental risks mentioned?"
                        onkeypress="if(event.key==='Enter') askQuestion()"
                    >
                    <input type="number" id="top_k" value="3" min="1" max="10">
                    <button class="btn" onclick="askQuestion()">Ask</button>
                </div>
                <small style="color: #999;">Top-K results: (1-10)</small>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Searching and generating answer...</p>
            </div>
            
            <div class="error" id="error" style="display: none;"></div>
            
            <div class="results" id="results">
                <div class="result-section">
                    <div class="result-title">📝 Generated Answer</div>
                    <div class="answer-box" id="answer"></div>
                </div>
                
                <div class="result-section">
                    <div class="result-title">📚 Retrieved Sources</div>
                    <div class="sources" id="sources"></div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        async function askQuestion() {
            const question = document.getElementById('question').value.trim();
            const top_k = parseInt(document.getElementById('top_k').value);
            
            if (!question) {
                showError('Please enter a question');
                return;
            }
            
            const loading = document.getElementById('loading');
            const results = document.getElementById('results');
            const error = document.getElementById('error');
            
            loading.style.display = 'block';
            results.style.display = 'none';
            error.style.display = 'none';
            
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ question, top_k }),
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const data = await response.json();
                displayResults(data);
            } catch (err) {
                showError(`Error: ${err.message}`);
            } finally {
                loading.style.display = 'none';
            }
        }
        
        function displayResults(data) {
            if (data.error) {
                showError(data.error);
                return;
            }
            
            document.getElementById('answer').textContent = data.answer;
            
            const sourcesHtml = data.sources.map((source, idx) => `
                <div class="source-item">
                    <div class="source-header">
                        <div>
                            <span class="source-name">${escapeHtml(source.source_name)}</span>
                            <span class="source-type">${source.source_type}</span>
                            <span class="source-rank">Rank #${source.rank}</span>
                        </div>
                    </div>
                    <div class="source-text">${escapeHtml(source.text.substring(0, 300))}...</div>
                    <div class="source-distance">Similarity: ${(1 - source.distance).toFixed(3)}</div>
                </div>
            `).join('');
            
            document.getElementById('sources').innerHTML = sourcesHtml;
            document.getElementById('results').style.display = 'block';
        }
        
        function showError(msg) {
            const error = document.getElementById('error');
            error.textContent = msg;
            error.style.display = 'block';
        }
        
        function escapeHtml(text) {
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            };
            return text.replace(/[&<>"']/g, m => map[m]);
        }
    </script>
</body>
</html>
"""


def get_html_ui() -> str:
    """Return the HTML UI template."""
    return HTML_TEMPLATE
