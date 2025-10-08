# dangquyenbui-dotcom/downtime_tracker/downtime_tracker-953d9e6915ad7fa465db9a8f87b8a56d713b0537/database/__init__.py
"""
Database package initialization
Provides centralized access to all database modules
"""

from .connection import DatabaseConnection, get_db
from .facilities import FacilitiesDB
from .production_lines import ProductionLinesDB
from .categories import CategoriesDB
from .downtimes import DowntimesDB
from .audit import AuditDB
from .shifts import ShiftsDB
from .users import UsersDB
from .sessions import SessionsDB
from .reports import reports_db
from .scheduling import scheduling_db
from .capacity import ProductionCapacityDB # Add this import

# Create singleton instances
facilities_db = FacilitiesDB()
lines_db = ProductionLinesDB()
categories_db = CategoriesDB()
downtimes_db = DowntimesDB()
audit_db = AuditDB()
shifts_db = ShiftsDB()
users_db = UsersDB()
sessions_db = SessionsDB()
capacity_db = ProductionCapacityDB() # Add this instance

# Export main database functions
__all__ = [
    'DatabaseConnection',
    'get_db',
    'facilities_db',
    'lines_db',
    'categories_db',
    'downtimes_db',
    'audit_db',
    'shifts_db',
    'users_db',
    'sessions_db',
    'reports_db',
    'scheduling_db',
    'capacity_db' # Add this export
]