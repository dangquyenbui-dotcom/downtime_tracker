# app.py - UPDATED with enhanced debugging

"""
Downtime Tracker - Main Application
Production-ready configuration with network access and i18n support
"""

from flask import Flask, session
import os
from datetime import timedelta
from config import Config
import socket

# Import i18n configuration
from i18n_config import I18nConfig, _, format_datetime_i18n, format_date_i18n

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = Config.SECRET_KEY
    app.permanent_session_lifetime = timedelta(hours=Config.SESSION_HOURS)
    
    # Configure static files path
    app.static_folder = 'static'
    app.static_url_path = '/static'
    
    # Initialize internationalization
    I18nConfig.init_app(app)
    
    # Register template filters for i18n
    app.jinja_env.filters['datetime_i18n'] = format_datetime_i18n
    app.jinja_env.filters['date_i18n'] = format_date_i18n
    
    # Make translation function available in templates
    app.jinja_env.globals['_'] = _
    app.jinja_env.globals['get_locale'] = lambda: session.get('language', 'en')
    app.jinja_env.globals['get_languages'] = I18nConfig.get_available_languages
    
    # Register blueprints
    register_blueprints(app)
    
    # Initialize database
    initialize_database()
    
    return app

def register_blueprints(app):
    """Register all application blueprints"""
    from routes.main import main_bp
    from routes.downtime import downtime_bp
    from routes.erp_routes import erp_bp
    from routes.scheduling import scheduling_bp 
    from routes.reports import reports_bp
    from routes.admin.panel import admin_panel_bp
    from routes.admin.facilities import admin_facilities_bp
    from routes.admin.production_lines import admin_lines_bp
    from routes.admin.categories import admin_categories_bp
    from routes.admin.audit import admin_audit_bp
    from routes.admin.shifts import admin_shifts_bp
    from routes.admin.users import admin_users_bp
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(downtime_bp)
    app.register_blueprint(erp_bp)
    app.register_blueprint(scheduling_bp)
    app.register_blueprint(reports_bp)
    
    # Register all admin blueprints under the /admin prefix
    app.register_blueprint(admin_panel_bp, url_prefix='/admin')
    app.register_blueprint(admin_facilities_bp, url_prefix='/admin')
    app.register_blueprint(admin_lines_bp, url_prefix='/admin')
    app.register_blueprint(admin_categories_bp, url_prefix='/admin')
    app.register_blueprint(admin_audit_bp, url_prefix='/admin')
    app.register_blueprint(admin_shifts_bp, url_prefix='/admin')
    app.register_blueprint(admin_users_bp, url_prefix='/admin')

def initialize_database():
    """Initialize database connection and verify tables"""
    from database.connection import DatabaseConnection
    
    db = DatabaseConnection()
    if db.test_connection():
        print("✅ Database: Connected and ready!")
    else:
        print("❌ Database: Connection failed!")
        print("   Run database initialization script")

def get_local_ip():
    """Get the local IP address of the machine"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"
    
def test_services():
    """Test all service connections on startup"""
    print("\n" + "="*60)
    print("DOWNTIME TRACKER v1.8.0 - STARTUP DIAGNOSTICS")
    print("="*60)
    
    from database.connection import DatabaseConnection
    db = DatabaseConnection()
    if db.test_connection():
        print("✅ Database: Connected")
    else:
        print("❌ Database: Not connected")
    
    if not Config.TEST_MODE:
        from auth.ad_auth import test_ad_connection
        if test_ad_connection():
            print("✅ Active Directory: Connected")
        else:
            print("❌ Active Directory: Not connected")
    else:
        print("🧪 Test Mode: Using fake authentication")
    
    print("="*60 + "\n")

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    local_ip = get_local_ip()
    
    print("\n" + "="*50)
    print("DOWNTIME TRACKER v1.8.0 - CONFIGURATION")
    print("="*50)
    print(f"Mode: {'TEST' if Config.TEST_MODE else 'PRODUCTION'}")
    print(f"Database: {Config.DB_SERVER}/{Config.DB_NAME}")
    print(f"AD Domain: {Config.AD_DOMAIN}")
    print(f"Languages: English, Spanish")
    print("="*50 + "\n")
    
    test_services()
    
    app = create_app()
    
    print("\n" + "="*60)
    print("🚀 SERVER STARTING - ACCESS URLS:")
    print("="*60)
    print(f"Local:        http://localhost:5000")
    print(f"Network:      http://{local_ip}:5000")
    print("="*60)
    print("\n📝 Make sure:")
    print("  1. Windows Firewall allows port 5000")
    print("  2. No antivirus blocking the connection")
    print("  3. Network allows peer-to-peer connections")
    print("\nPress CTRL+C to stop the server\n")
    
    # Use Flask's built-in server for debugging
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True # Enables detailed error messages and auto-reloading
    )