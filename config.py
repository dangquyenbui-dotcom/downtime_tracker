"""
Configuration settings for Downtime Tracker
Reads sensitive information from environment variables
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    SESSION_HOURS = int(os.getenv('SESSION_HOURS', '8'))
    
    # Active Directory settings
    AD_SERVER = os.getenv('AD_SERVER')
    AD_DOMAIN = os.getenv('AD_DOMAIN')
    AD_PORT = int(os.getenv('AD_PORT', '389'))
    
    # Service account for AD queries
    AD_SERVICE_ACCOUNT = os.getenv('AD_SERVICE_ACCOUNT')
    AD_SERVICE_PASSWORD = os.getenv('AD_SERVICE_PASSWORD')
    
    # Security Groups
    AD_ADMIN_GROUP = os.getenv('AD_ADMIN_GROUP', 'DowntimeTracker_Admin')
    AD_USER_GROUP = os.getenv('AD_USER_GROUP', 'DowntimeTracker_User')
    
    # Base DN for searches
    AD_BASE_DN = os.getenv('AD_BASE_DN')
    
    # Test mode - set to True to bypass AD and use test accounts
    TEST_MODE = os.getenv('TEST_MODE', 'False').lower() == 'true'
    
    # Database settings
    DB_SERVER = os.getenv('DB_SERVER')
    DB_NAME = os.getenv('DB_NAME', 'ProductionDB')
    DB_USE_WINDOWS_AUTH = os.getenv('DB_USE_WINDOWS_AUTH', 'False').lower() == 'true'
    DB_USERNAME = os.getenv('DB_USERNAME')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    
    # Email settings (for notifications)
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'mail.local')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'True').lower() == 'true'
    EMAIL_FROM = os.getenv('EMAIL_FROM', 'downtime@local')
    
    # Email notification mappings (category -> AD groups)
    EMAIL_NOTIFICATIONS = {
        'Mechanical': ['Maintenance Team', 'Facility Manager'],
        'Electrical': ['Maintenance Team', 'Facility Manager'],
        'Material Shortage': ['Supply Chain', 'Production Manager'],
        'Quality Hold': ['Quality Team', 'Production Manager'],
        'No Operator': ['HR Team', 'Production Manager'],
        'Changeover': ['Production Manager'],
        'Break Time': [],  # No notification
        'Cleaning': ['Production Manager'],
        'Planned Maintenance': ['Maintenance Team'],
        'Other': ['Production Manager', 'Facility Manager']
    }