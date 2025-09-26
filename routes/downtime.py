"""
Downtime entry and reporting routes
"""

from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify
from auth import require_login

# Create blueprint
downtime_bp = Blueprint('downtime', __name__)

@downtime_bp.route('/downtime')
def entry_form():
    """Downtime entry form"""
    if not require_login(session):
        return redirect(url_for('main.login'))
    
    # Placeholder for now - we'll build this next
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Report Downtime - Downtime Tracker</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f5f5;
                padding: 20px;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2d3748;
                border-bottom: 3px solid #48bb78;
                padding-bottom: 10px;
            }
            .form-preview {
                background: #f7fafc;
                border: 2px dashed #cbd5e0;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }
            .form-field {
                margin: 15px 0;
                padding: 10px;
                background: white;
                border-radius: 5px;
            }
            .back-link {
                display: inline-block;
                margin-top: 20px;
                color: #667eea;
                text-decoration: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📝 Report Downtime</h1>
            <p>Record production downtime events</p>
            
            <div class="form-preview">
                <h3>Form fields coming next:</h3>
                <div class="form-field">📍 <strong>Facility:</strong> Dropdown list</div>
                <div class="form-field">⚙️ <strong>Production Line:</strong> Dropdown (filtered by facility)</div>
                <div class="form-field">📅 <strong>Date:</strong> Date picker</div>
                <div class="form-field">⏰ <strong>Start Time:</strong> Time picker</div>
                <div class="form-field">⏱️ <strong>End Time:</strong> Time picker</div>
                <div class="form-field">📊 <strong>Category:</strong> Dropdown (Mechanical, Electrical, etc.)</div>
                <div class="form-field">🕐 <strong>Shift:</strong> Auto-select based on time</div>
                <div class="form-field">📝 <strong>Notes:</strong> Text area</div>
            </div>
            
            <p><strong>Features:</strong></p>
            <ul>
                <li>Auto-calculate duration</li>
                <li>Email notifications based on category</li>
                <li>Save to SQL database</li>
                <li>Validation to prevent overlaps</li>
            </ul>
            
            <a href="/dashboard" class="back-link">← Back to Dashboard</a>
        </div>
    </body>
    </html>
    """

@downtime_bp.route('/downtime/add', methods=['POST'])
def add_downtime():
    """Add new downtime entry"""
    if not require_login(session):
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    # This will handle the form submission when we build it
    return jsonify({'success': True, 'message': 'Downtime entry added'})

@downtime_bp.route('/reports')
def reports():
    """View reports"""
    if not require_login(session):
        return redirect(url_for('main.login'))
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Reports - Downtime Tracker</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f5f5;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2d3748;
                border-bottom: 3px solid #4ecdc4;
                padding-bottom: 10px;
            }
            .reports-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            .report-card {
                background: #f7fafc;
                border: 1px solid #e2e8f0;
                padding: 20px;
                border-radius: 8px;
            }
            .report-title {
                font-size: 18px;
                font-weight: 600;
                color: #2d3748;
                margin-bottom: 10px;
            }
            .back-link {
                display: inline-block;
                margin-top: 20px;
                color: #667eea;
                text-decoration: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Downtime Reports</h1>
            <p>View and analyze downtime data</p>
            
            <div class="reports-grid">
                <div class="report-card">
                    <div class="report-title">📈 Daily Summary</div>
                    <p>Downtime by day, shift, and category</p>
                </div>
                
                <div class="report-card">
                    <div class="report-title">📊 Weekly Trends</div>
                    <p>Week-over-week comparison</p>
                </div>
                
                <div class="report-card">
                    <div class="report-title">🏭 By Facility</div>
                    <p>Compare facilities performance</p>
                </div>
                
                <div class="report-card">
                    <div class="report-title">⚙️ By Production Line</div>
                    <p>Line-specific downtime analysis</p>
                </div>
                
                <div class="report-card">
                    <div class="report-title">📋 By Category</div>
                    <p>Pareto chart of downtime causes</p>
                </div>
                
                <div class="report-card">
                    <div class="report-title">📥 Export Data</div>
                    <p>Download to Excel/CSV</p>
                </div>
            </div>
            
            <a href="/dashboard" class="back-link">← Back to Dashboard</a>
        </div>
    </body>
    </html>
    """