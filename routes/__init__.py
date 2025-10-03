"""
Routes package initialization
All route blueprints are imported and registered in app.py
"""

from .main import main_bp
from .downtime import downtime_bp
from .erp_routes import erp_bp
from .scheduling import scheduling_bp
from .reports import reports_bp
from . import admin

__all__ = [
    'main_bp',
    'downtime_bp',
    'erp_bp',
    'scheduling_bp',
    'reports_bp',
    'admin'
]