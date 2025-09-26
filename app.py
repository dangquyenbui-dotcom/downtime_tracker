"""
Downtime Tracker - Main Application
Updated to use modular structure with database integration
Domain: wepackitall.local
"""

from flask import Flask
import os
from datetime import timedelta
from config import Config
from database import db

# Import blueprints
from routes.main import main_bp
from routes.admin import admin_bp
from routes.downtime import downtime_bp

def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = Config.SECRET_KEY
    app.permanent_session_lifetime = timedelta(hours=Config.SESSION_HOURS)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(downtime_bp)
    
    return app

def test_connections():
    """Test both AD and Database connections on startup"""
    print("\n" + "="*60)
    print("DOWNTIME TRACKER - STARTUP DIAGNOSTICS")
    print("="*60)
    
    # Test Database Connection
    print("\n🗄️  Testing Database Connection...")
    print("-" * 40)
    # test_connection() handles its own connect/disconnect
    if db.test_connection():
        print("✅ Database: Connected and ready!")
    else:
        print("❌ Database: Connection failed!")
        print("   Run: python test_db_connection.py")
    
    # Test AD Connection (if not in test mode)
    if not Config.TEST_MODE:
        print("\n🔐 Testing Active Directory Connection...")
        print("-" * 40)
        try:
            from auth import get_user_groups
            # Test with service account
            result = get_user_groups('test')  # This will fail gracefully if no test user
            if result is None:
                print("✅ AD: Service account connected (no test user found - normal)")
            else:
                print("✅ AD: Service account connected successfully!")
        except Exception as e:
            print("❌ AD: Connection failed!")
            print(f"   Error: {str(e)}")
            print("   Run: python test_ad_connection.py")
    else:
        print("\n🧪 Test Mode: Using fake authentication")
    
    print("\n" + "="*60)
    print("STARTUP COMPLETE")
    print("="*60)

if __name__ == '__main__':
    # Create templates folder if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Display configuration
    print("\n" + "="*50)
    print("DOWNTIME TRACKER - CONFIGURATION")
    print("="*50)
    print(f"\nActive Directory:")
    print(f"  Domain: {Config.AD_DOMAIN}")
    print(f"  Server: {Config.AD_SERVER}")
    print(f"  Admin Group: {Config.AD_ADMIN_GROUP}")
    print(f"  User Group: {Config.AD_USER_GROUP}")
    print(f"  Test Mode: {'ENABLED' if Config.TEST_MODE else 'DISABLED'}")
    
    print(f"\nDatabase:")
    print(f"  Server: {Config.DB_SERVER}")
    print(f"  Database: {Config.DB_NAME}")
    print(f"  Auth: {'Windows' if Config.DB_USE_WINDOWS_AUTH else 'SQL'}")
    if not Config.DB_USE_WINDOWS_AUTH:
        print(f"  Username: {Config.DB_USERNAME}")
    
    if Config.TEST_MODE:
        print("\n⚠️  TEST MODE ACTIVE")
        print("Test users: test (user), test1 (admin)")
        print("Passwords: same as username")
    else:
        print("\n✅ PRODUCTION MODE")
        print("Using real Active Directory authentication")
        print("Users must be in required AD groups")
    
    # Test connections
    test_connections()
    
    # Create and run app
    app = create_app()
    
    print(f"\n🚀 Starting server at: http://localhost:5000")
    print("Press CTRL+C to stop the server")
    print("="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)