"""
Database Module for Downtime Tracker with Audit Logging
Handles all database operations and tracks changes
"""

import pyodbc
from config import Config
from datetime import datetime
import json

class Database:
    """Database connection and operations with audit logging"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.audit_enabled = True  # Can be toggled off for bulk operations
        
    def connect(self):
        """Establish database connection"""
        try:
            if Config.DB_USE_WINDOWS_AUTH:
                connection_string = (
                    f"DRIVER={{SQL Server}};"
                    f"SERVER={Config.DB_SERVER};"
                    f"DATABASE={Config.DB_NAME};"
                    f"Trusted_Connection=yes;"
                )
            else:
                connection_string = (
                    f"DRIVER={{SQL Server}};"
                    f"SERVER={Config.DB_SERVER};"
                    f"DATABASE={Config.DB_NAME};"
                    f"UID={Config.DB_USERNAME};"
                    f"PWD={Config.DB_PASSWORD};"
                )
            
            self.connection = pyodbc.connect(connection_string)
            self.cursor = self.connection.cursor()
            return True
            
        except pyodbc.Error as e:
            print(f"Database connection failed: {str(e)}")
            # Try with ODBC Driver 17 if SQL Server driver fails
            if "SQL Server" in str(e):
                try:
                    if Config.DB_USE_WINDOWS_AUTH:
                        connection_string = (
                            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                            f"SERVER={Config.DB_SERVER};"
                            f"DATABASE={Config.DB_NAME};"
                            f"Trusted_Connection=yes;"
                        )
                    else:
                        connection_string = (
                            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                            f"SERVER={Config.DB_SERVER};"
                            f"DATABASE={Config.DB_NAME};"
                            f"UID={Config.DB_USERNAME};"
                            f"PWD={Config.DB_PASSWORD};"
                        )
                    
                    self.connection = pyodbc.connect(connection_string)
                    self.cursor = self.connection.cursor()
                    return True
                except:
                    pass
            
            return False
    
    def disconnect(self):
        """Close database connection"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            return True
        except Exception as e:
            print(f"Error disconnecting: {str(e)}")
            return False
    
    def test_connection(self):
        """Test database connection"""
        try:
            if self.connect():
                self.cursor.execute("SELECT 1")
                result = self.cursor.fetchone()
                self.disconnect()
                return result is not None
        except:
            return False
        return False
    
    def ensure_audit_table(self):
        """Ensure the AuditLog table exists"""
        try:
            # Check if table exists
            if not self.check_table_exists('AuditLog'):
                print("Creating AuditLog table...")
                create_query = """
                    CREATE TABLE AuditLog (
                        audit_id INT IDENTITY(1,1) PRIMARY KEY,
                        table_name NVARCHAR(100) NOT NULL,
                        record_id INT,
                        action_type NVARCHAR(50) NOT NULL,
                        field_name NVARCHAR(100),
                        old_value NVARCHAR(MAX),
                        new_value NVARCHAR(MAX),
                        changed_by NVARCHAR(100) NOT NULL,
                        changed_date DATETIME NOT NULL DEFAULT GETDATE(),
                        user_ip NVARCHAR(50),
                        user_agent NVARCHAR(500),
                        additional_notes NVARCHAR(MAX)
                    );
                    
                    CREATE INDEX IX_AuditLog_Table ON AuditLog(table_name, record_id);
                    CREATE INDEX IX_AuditLog_Date ON AuditLog(changed_date DESC);
                    CREATE INDEX IX_AuditLog_User ON AuditLog(changed_by);
                """
                self.cursor.execute(create_query)
                self.connection.commit()
                print("✅ AuditLog table created successfully")
                return True
        except Exception as e:
            print(f"Error ensuring audit table: {str(e)}")
            return False
    
    def log_audit(self, table_name, record_id, action_type, changes=None, username=None, ip=None, user_agent=None, notes=None):
        """
        Log an audit entry
        
        Args:
            table_name: Name of the table being modified
            record_id: ID of the record being modified
            action_type: INSERT, UPDATE, DELETE, DEACTIVATE
            changes: Dict of {field_name: {'old': old_value, 'new': new_value}}
            username: User making the change
            ip: User's IP address
            user_agent: User's browser info
            notes: Additional notes
        """
        if not self.audit_enabled:
            return True
            
        try:
            # First ensure the audit table exists
            self.ensure_audit_table()
            
            if changes:
                # Log each field change separately for better tracking
                for field_name, values in changes.items():
                    old_value = str(values.get('old', '')) if values.get('old') is not None else None
                    new_value = str(values.get('new', '')) if values.get('new') is not None else None
                    
                    query = """
                        INSERT INTO AuditLog (
                            table_name, record_id, action_type, field_name,
                            old_value, new_value, changed_by, changed_date,
                            user_ip, user_agent, additional_notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, ?, ?)
                    """
                    
                    self.cursor.execute(query, (
                        table_name, record_id, action_type, field_name,
                        old_value, new_value, username or 'system',
                        ip, user_agent, notes
                    ))
            else:
                # For actions without field changes (like INSERT of new record)
                query = """
                    INSERT INTO AuditLog (
                        table_name, record_id, action_type, changed_by, 
                        changed_date, user_ip, user_agent, additional_notes
                    ) VALUES (?, ?, ?, ?, GETDATE(), ?, ?, ?)
                """
                
                self.cursor.execute(query, (
                    table_name, record_id, action_type, 
                    username or 'system', ip, user_agent, notes
                ))
            
            # IMPORTANT: Commit the audit log entry!
            self.connection.commit()
            print(f"✅ Audit logged: {action_type} on {table_name} ID {record_id} by {username}")
            return True
            
        except Exception as e:
            print(f"❌ Audit logging failed: {str(e)}")
            # Try to rollback if commit failed
            try:
                self.connection.rollback()
            except:
                pass
            # Don't fail the main operation if audit fails
            return False
    
    def get_record_before_update(self, table_name, id_column, record_id):
        """Get current values before update for audit comparison"""
        try:
            query = f"SELECT * FROM {table_name} WHERE {id_column} = ?"
            self.cursor.execute(query, (record_id,))
            
            columns = [column[0] for column in self.cursor.description]
            row = self.cursor.fetchone()
            
            if row:
                return dict(zip(columns, row))
            return None
            
        except Exception as e:
            print(f"Error getting record before update: {str(e)}")
            return None
    
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            # If it's a SELECT query, return results
            if query.strip().upper().startswith('SELECT'):
                columns = [column[0] for column in self.cursor.description]
                results = []
                for row in self.cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                return results
            else:
                # For INSERT, UPDATE, DELETE
                self.connection.commit()
                return True
                
        except pyodbc.Error as e:
            print(f"Query execution failed: {str(e)}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            self.connection.rollback()
            # Return empty list for SELECT queries, False for others
            if query.strip().upper().startswith('SELECT'):
                return []
            return False
    
    def execute_scalar(self, query, params=None):
        """Execute a query and return a single value"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            result = self.cursor.fetchone()
            return result[0] if result else None
            
        except Exception as e:
            print(f"Scalar query failed: {str(e)}")
            return None
    
    def check_table_exists(self, table_name):
        """Check if a table exists in the database"""
        try:
            query = """
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = ? AND TABLE_CATALOG = ?
            """
            result = self.execute_scalar(query, (table_name, Config.DB_NAME))
            return result > 0 if result is not None else False
        except Exception as e:
            print(f"Table check failed: {str(e)}")
            return False
    
    def get_facilities(self, active_only=True):
        """Get all facilities"""
        try:
            # Check which columns exist
            columns_query = """
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'Facilities'
            """
            columns_result = self.execute_query(columns_query)
            existing_columns = [col['COLUMN_NAME'] for col in columns_result] if columns_result else []
            
            # Build query based on available columns
            select_fields = ['facility_id', 'facility_name', 'location', 'is_active']
            if 'created_date' in existing_columns:
                select_fields.append('created_date')
            if 'created_by' in existing_columns:
                select_fields.append('created_by')
            if 'modified_date' in existing_columns:
                select_fields.append('modified_date')
            if 'modified_by' in existing_columns:
                select_fields.append('modified_by')
            
            fields_str = ', '.join(select_fields)
            
            if active_only:
                query = f"""
                    SELECT {fields_str}
                    FROM Facilities
                    WHERE is_active = 1
                    ORDER BY facility_name
                """
            else:
                query = f"""
                    SELECT {fields_str}
                    FROM Facilities
                    ORDER BY is_active DESC, facility_name
                """
            
            return self.execute_query(query)
        except Exception as e:
            print(f"Error getting facilities: {str(e)}")
            return []
    
    def get_production_lines(self, facility_id=None, active_only=True):
        """Get production lines, optionally filtered by facility"""
        try:
            # Check which columns exist
            columns_query = """
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'ProductionLines'
            """
            columns_result = self.execute_query(columns_query)
            existing_columns = [col['COLUMN_NAME'] for col in columns_result] if columns_result else []
            
            # Build select fields based on available columns
            select_fields = ['pl.line_id', 'pl.facility_id', 'pl.line_name', 'pl.is_active', 'f.facility_name']
            if 'line_code' in existing_columns:
                select_fields.insert(3, 'pl.line_code')
            if 'created_date' in existing_columns:
                select_fields.append('pl.created_date')
            if 'created_by' in existing_columns:
                select_fields.append('pl.created_by')
            if 'modified_date' in existing_columns:
                select_fields.append('pl.modified_date')
            if 'modified_by' in existing_columns:
                select_fields.append('pl.modified_by')
            
            fields_str = ', '.join(select_fields)
            
            if facility_id:
                if active_only:
                    query = f"""
                        SELECT {fields_str}
                        FROM ProductionLines pl
                        JOIN Facilities f ON pl.facility_id = f.facility_id
                        WHERE pl.facility_id = ? AND pl.is_active = 1
                        ORDER BY pl.line_name
                    """
                    params = (facility_id,)
                else:
                    query = f"""
                        SELECT {fields_str}
                        FROM ProductionLines pl
                        JOIN Facilities f ON pl.facility_id = f.facility_id
                        WHERE pl.facility_id = ?
                        ORDER BY pl.is_active DESC, pl.line_name
                    """
                    params = (facility_id,)
            else:
                if active_only:
                    query = f"""
                        SELECT {fields_str}
                        FROM ProductionLines pl
                        JOIN Facilities f ON pl.facility_id = f.facility_id
                        WHERE pl.is_active = 1
                        ORDER BY f.facility_name, pl.line_name
                    """
                    params = None
                else:
                    query = f"""
                        SELECT {fields_str}
                        FROM ProductionLines pl
                        JOIN Facilities f ON pl.facility_id = f.facility_id
                        ORDER BY pl.is_active DESC, f.facility_name, pl.line_name
                    """
                    params = None
            
            return self.execute_query(query, params)
        except Exception as e:
            print(f"Error getting production lines: {str(e)}")
            return []
    
    def get_audit_history(self, table_name=None, record_id=None, username=None, days=30):
        """Get audit history with filters"""
        try:
            # First ensure the audit table exists
            if not self.check_table_exists('AuditLog'):
                print("AuditLog table doesn't exist yet. Creating it...")
                self.ensure_audit_table()
                return []  # Return empty since no history exists yet
            
            query = """
                SELECT 
                    audit_id,
                    table_name,
                    record_id,
                    action_type,
                    field_name,
                    old_value,
                    new_value,
                    changed_by,
                    changed_date,
                    user_ip,
                    additional_notes
                FROM AuditLog
                WHERE changed_date >= DATEADD(day, ?, GETDATE())
            """
            
            params = [-days]
            
            if table_name:
                query += " AND table_name = ?"
                params.append(table_name)
            
            if record_id:
                query += " AND record_id = ?"
                params.append(record_id)
            
            if username:
                query += " AND changed_by = ?"
                params.append(username)
            
            query += " ORDER BY changed_date DESC"
            
            return self.execute_query(query, params)
            
        except Exception as e:
            print(f"Error getting audit history: {str(e)}")
            return []
    
    def get_facility_history(self, facility_id):
        """Get detailed audit history for a specific facility"""
        try:
            # First ensure the audit table exists
            if not self.check_table_exists('AuditLog'):
                self.ensure_audit_table()
                return []
            
            query = """
                SELECT 
                    audit_id,
                    action_type,
                    field_name,
                    old_value,
                    new_value,
                    changed_by,
                    changed_date,
                    CASE 
                        WHEN field_name = 'is_active' AND new_value = '0' THEN 'Deactivated'
                        WHEN field_name = 'is_active' AND new_value = '1' THEN 'Reactivated'
                        WHEN action_type = 'INSERT' THEN 'Created'
                        WHEN action_type = 'UPDATE' THEN 'Modified'
                        ELSE action_type
                    END as action_description
                FROM AuditLog
                WHERE table_name = 'Facilities' AND record_id = ?
                ORDER BY changed_date DESC
            """
            
            return self.execute_query(query, (facility_id,))
            
        except Exception as e:
            print(f"Error getting facility history: {str(e)}")
            return []
    
    def get_line_history(self, line_id):
        """Get detailed audit history for a specific production line"""
        try:
            # First ensure the audit table exists
            if not self.check_table_exists('AuditLog'):
                self.ensure_audit_table()
                return []
            
            query = """
                SELECT 
                    audit_id,
                    action_type,
                    field_name,
                    old_value,
                    new_value,
                    changed_by,
                    changed_date,
                    CASE 
                        WHEN field_name = 'is_active' AND new_value = '0' THEN 'Deactivated'
                        WHEN field_name = 'is_active' AND new_value = '1' THEN 'Reactivated'
                        WHEN action_type = 'INSERT' THEN 'Created'
                        WHEN action_type = 'UPDATE' THEN 'Modified'
                        ELSE action_type
                    END as action_description
                FROM AuditLog
                WHERE table_name = 'ProductionLines' AND record_id = ?
                ORDER BY changed_date DESC
            """
            
            return self.execute_query(query, (line_id,))
            
        except Exception as e:
            print(f"Error getting line history: {str(e)}")
            return []
    
    def get_downtime_categories(self, active_only=True):
        """Get all downtime categories"""
        try:
            if active_only:
                query = """
                    SELECT category_id, category_name, description, is_active
                    FROM DowntimeCategories
                    WHERE is_active = 1
                    ORDER BY category_name
                """
            else:
                query = """
                    SELECT category_id, category_name, description, is_active
                    FROM DowntimeCategories
                    ORDER BY is_active DESC, category_name
                """
            
            return self.execute_query(query)
        except Exception as e:
            print(f"Error getting categories: {str(e)}")
            return []
    
    def get_shifts(self):
        """Get all shifts"""
        try:
            query = """
                SELECT shift_id, shift_name, start_time, end_time, is_active
                FROM Shifts
                WHERE is_active = 1
                ORDER BY start_time
            """
            return self.execute_query(query)
        except Exception as e:
            print(f"Error getting shifts: {str(e)}")
            return []
    
    def add_downtime(self, data):
        """Add a new downtime record"""
        try:
            query = """
                INSERT INTO Downtimes (
                    facility_id, line_id, category_id, shift_id,
                    start_time, end_time, duration_minutes,
                    notes, created_by, created_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """
            
            # Calculate duration
            start = datetime.fromisoformat(data['start_time'])
            end = datetime.fromisoformat(data['end_time'])
            duration_minutes = int((end - start).total_seconds() / 60)
            
            params = (
                data['facility_id'],
                data['line_id'],
                data['category_id'],
                data['shift_id'],
                data['start_time'],
                data['end_time'],
                duration_minutes,
                data.get('notes', ''),
                data['created_by']
            )
            
            return self.execute_query(query, params)
        except Exception as e:
            print(f"Error adding downtime: {str(e)}")
            return False
    
    def get_recent_downtimes(self, days=7, facility_id=None):
        """Get recent downtime entries"""
        try:
            base_query = """
                SELECT d.*, 
                       f.facility_name, 
                       pl.line_name,
                       dc.category_name,
                       s.shift_name
                FROM Downtimes d
                JOIN Facilities f ON d.facility_id = f.facility_id
                JOIN ProductionLines pl ON d.line_id = pl.line_id
                JOIN DowntimeCategories dc ON d.category_id = dc.category_id
                JOIN Shifts s ON d.shift_id = s.shift_id
                WHERE d.start_time >= DATEADD(day, ?, GETDATE())
                  AND d.is_deleted = 0
            """
            
            if facility_id:
                query = base_query + " AND d.facility_id = ? ORDER BY d.start_time DESC"
                params = (-days, facility_id)
            else:
                query = base_query + " ORDER BY d.start_time DESC"
                params = (-days,)
            
            return self.execute_query(query, params)
        except Exception as e:
            print(f"Error getting recent downtimes: {str(e)}")
            return []
    
    def get_downtime_summary(self, start_date, end_date, group_by='category'):
        """Get downtime summary statistics"""
        try:
            if group_by == 'category':
                query = """
                    SELECT dc.category_name as grouping,
                           COUNT(*) as event_count,
                           SUM(d.duration_minutes) as total_minutes
                    FROM Downtimes d
                    JOIN DowntimeCategories dc ON d.category_id = dc.category_id
                    WHERE d.start_time >= ? AND d.end_time <= ?
                      AND d.is_deleted = 0
                    GROUP BY dc.category_name
                    ORDER BY total_minutes DESC
                """
            elif group_by == 'facility':
                query = """
                    SELECT f.facility_name as grouping,
                           COUNT(*) as event_count,
                           SUM(d.duration_minutes) as total_minutes
                    FROM Downtimes d
                    JOIN Facilities f ON d.facility_id = f.facility_id
                    WHERE d.start_time >= ? AND d.end_time <= ?
                      AND d.is_deleted = 0
                    GROUP BY f.facility_name
                    ORDER BY total_minutes DESC
                """
            else:  # group by line
                query = """
                    SELECT pl.line_name as grouping,
                           COUNT(*) as event_count,
                           SUM(d.duration_minutes) as total_minutes
                    FROM Downtimes d
                    JOIN ProductionLines pl ON d.line_id = pl.line_id
                    WHERE d.start_time >= ? AND d.end_time <= ?
                      AND d.is_deleted = 0
                    GROUP BY pl.line_name
                    ORDER BY total_minutes DESC
                """
            
            params = (start_date, end_date)
            return self.execute_query(query, params)
        except Exception as e:
            print(f"Error getting downtime summary: {str(e)}")
            return []

# Create global instance
db = Database()