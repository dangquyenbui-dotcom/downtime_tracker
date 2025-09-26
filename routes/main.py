"""
Main routes for Downtime Tracker
Handles login, logout, and dashboard
"""

import sys
from pathlib import Path
# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from flask import Blueprint, render_template, redirect, url_for, session, request, flash

# Now these imports will work properly
import auth  # type: ignore
import config  # type: ignore
import database  # type: ignore

# Create blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Redirect root to login or dashboard"""
    if 'user' in session:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with proper template rendering"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if username and password:
            print(f"Login attempt for user: {username}")
            user_info = auth.authenticate_user(username, password)
            
            if user_info:
                # Set session
                session.permanent = True
                session['user'] = user_info
                
                print(f"✅ User {username} logged in successfully. Admin: {user_info.get('is_admin', False)}")
                return redirect(url_for('main.dashboard'))
            else:
                flash('Invalid credentials or access denied. You must be a member of DowntimeTracker_User or DowntimeTracker_Admin group.', 'error')
                print(f"❌ Login failed for user: {username}")
        else:
            flash('Please enter both username and password', 'error')
    
    # Pass config to template for dynamic display
    return render_template('login.html', config=config.Config)

@main_bp.route('/dashboard')
def dashboard():
    """Main dashboard after login"""
    if not auth.require_login(session):
        return redirect(url_for('main.login'))
    
    # Get database statistics with safe defaults
    stats = {
        'facilities': 0,
        'production_lines': 0,
        'recent_downtime_count': 0,
        'categories': 0
    }
    
    db = database.db
    try:
        if db.connect():
            try:
                # Count facilities
                if db.check_table_exists('Facilities'):
                    result = db.execute_query("SELECT COUNT(*) as count FROM Facilities WHERE is_active = 1")
                    if result and len(result) > 0:
                        stats['facilities'] = result[0].get('count', 0)
                
                # Count production lines
                if db.check_table_exists('ProductionLines'):
                    result = db.execute_query("SELECT COUNT(*) as count FROM ProductionLines WHERE is_active = 1")
                    if result and len(result) > 0:
                        stats['production_lines'] = result[0].get('count', 0)
                
                # Count recent downtime events (last 7 days)
                if db.check_table_exists('Downtimes'):
                    result = db.execute_query("""
                        SELECT COUNT(*) as count 
                        FROM Downtimes 
                        WHERE start_time >= DATEADD(day, -7, GETDATE())
                          AND is_deleted = 0
                    """)
                    if result and len(result) > 0:
                        stats['recent_downtime_count'] = result[0].get('count', 0)
                
                # Count downtime categories
                if db.check_table_exists('DowntimeCategories'):
                    result = db.execute_query("SELECT COUNT(*) as count FROM DowntimeCategories WHERE is_active = 1")
                    if result and len(result) > 0:
                        stats['categories'] = result[0].get('count', 0)
            finally:
                db.disconnect()
    except Exception as e:
        print(f"Error getting dashboard stats: {str(e)}")
        # Use default zeros if database isn't ready
    
    return render_template('dashboard.html', 
                         user=session['user'], 
                         stats=stats, 
                         config=config.Config)

@main_bp.route('/logout')
def logout():
    """Logout and clear session"""
    username = session.get('user', {}).get('username', 'Unknown')
    session.clear()
    print(f"User {username} logged out")
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('main.login'))

@main_bp.route('/status')
def status():
    """System status page (admin only)"""
    if not auth.require_login(session):
        return redirect(url_for('main.login'))
    
    if not session.get('user', {}).get('is_admin', False):
        flash('Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # System status info with safe defaults
    status_info = {
        'ad_connected': False,
        'db_connected': False,
        'test_mode': config.Config.TEST_MODE,
        'facilities_count': 0,
        'lines_count': 0,
        'users_today': 0
    }
    
    # Test AD connection
    try:
        if not config.Config.TEST_MODE:
            result = auth.get_user_groups('nonexistent_test_user')  # Test query
            status_info['ad_connected'] = True
        else:
            status_info['ad_connected'] = True  # In test mode, consider it "connected"
    except Exception:
        status_info['ad_connected'] = config.Config.TEST_MODE  # In test mode, consider it "connected"
    
    # Test DB connection and get counts
    db = database.db
    try:
        if db.connect():
            try:
                status_info['db_connected'] = True
                
                # Get counts with safe table checks
                if db.check_table_exists('Facilities'):
                    result = db.execute_query("SELECT COUNT(*) as count FROM Facilities")
                    if result and len(result) > 0:
                        status_info['facilities_count'] = result[0].get('count', 0)
                
                if db.check_table_exists('ProductionLines'):
                    result = db.execute_query("SELECT COUNT(*) as count FROM ProductionLines")
                    if result and len(result) > 0:
                        status_info['lines_count'] = result[0].get('count', 0)
                
                # Count unique users today
                if db.check_table_exists('Downtimes'):
                    result = db.execute_query("""
                        SELECT COUNT(DISTINCT created_by) as count 
                        FROM Downtimes 
                        WHERE CAST(created_date as DATE) = CAST(GETDATE() as DATE)
                    """)
                    if result and len(result) > 0:
                        status_info['users_today'] = result[0].get('count', 0)
            finally:
                db.disconnect()
    except Exception as e:
        print(f"Error in status check: {str(e)}")
    
    # Check if status.html template exists, otherwise return simple status page
    try:
        return render_template('status.html', 
                             user=session['user'], 
                             status=status_info, 
                             config=config.Config)
    except Exception:
        # Fallback if template doesn't exist
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>System Status</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
                .status {{ margin: 10px 0; padding: 10px; background: #f0f0f0; border-radius: 5px; }}
                .status.ok {{ background: #c6f6d5; }}
                .status.error {{ background: #fed7d7; }}
                a {{ color: #667eea; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>System Status</h1>
                <div class="status {'ok' if status_info['db_connected'] else 'error'}">
                    Database: {'✅ Connected' if status_info['db_connected'] else '❌ Disconnected'}
                </div>
                <div class="status {'ok' if status_info['ad_connected'] else 'error'}">
                    Active Directory: {'✅ Connected' if status_info['ad_connected'] else '❌ Disconnected'}
                </div>
                <div class="status ok">
                    Test Mode: {'Yes' if status_info['test_mode'] else 'No'}
                </div>
                <hr>
                <p>Facilities: {status_info['facilities_count']}</p>
                <p>Production Lines: {status_info['lines_count']}</p>
                <p>Users Today: {status_info['users_today']}</p>
                <p><a href="/dashboard">← Back to Dashboard</a></p>
            </div>
        </body>
        </html>
        """