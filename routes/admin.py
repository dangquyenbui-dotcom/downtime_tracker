"""
Admin routes for Downtime Tracker with comprehensive audit logging
Handles facilities, production lines, and tracks all changes
"""

from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify, flash
from auth import require_login, require_admin
from database import db

# Create blueprint
admin_bp = Blueprint('admin', __name__)

def get_client_info():
    """Get client IP and user agent for audit logging"""
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    user_agent = request.environ.get('HTTP_USER_AGENT', '')[:500]  # Limit to 500 chars
    return ip, user_agent

@admin_bp.route('/admin')
def panel():
    """Admin panel main page"""
    if not require_login(session):
        return redirect(url_for('main.login'))
    
    if not require_admin(session):
        flash('Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    return render_template('admin/panel.html', user=session['user'])

@admin_bp.route('/admin/facilities')
def facilities():
    """Manage facilities"""
    if not require_login(session):
        return redirect(url_for('main.login'))
    
    if not require_admin(session):
        flash('Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get all facilities from database
    facilities = []
    error_message = None
    
    try:
        if db.connect():
            # First check if the table exists
            if not db.check_table_exists('Facilities'):
                error_message = "Facilities table does not exist. Please run init_database.py to create tables."
                print(f"Error: {error_message}")
            else:
                facilities = db.get_facilities(active_only=False)  # Show all including inactive
                if facilities is None:
                    facilities = []
                    error_message = "Failed to retrieve facilities from database."
                else:
                    # Add safe defaults for missing fields
                    for facility in facilities:
                        if 'created_date' not in facility:
                            facility['created_date'] = None
                        if 'created_by' not in facility:
                            facility['created_by'] = None
                        if 'modified_date' not in facility:
                            facility['modified_date'] = None
                        if 'modified_by' not in facility:
                            facility['modified_by'] = None
                print(f"Retrieved {len(facilities)} facilities")
            db.disconnect()
        else:
            error_message = "Failed to connect to database. Check your database configuration."
            print("Error: Database connection failed")
    except Exception as e:
        error_message = f'Error loading facilities: {str(e)}'
        print(f"Exception in facilities route: {str(e)}")
        facilities = []
    
    if error_message:
        flash(error_message, 'error')
    
    return render_template('admin/facilities.html', 
                         facilities=facilities, 
                         user=session['user'])

@admin_bp.route('/admin/facilities/add', methods=['POST'])
def add_facility():
    """Add new facility with audit logging"""
    if not require_login(session) or not require_admin(session):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        
        if not name:
            return jsonify({'success': False, 'message': 'Facility name is required'})
        
        ip, user_agent = get_client_info()
        
        if db.connect():
            # Check if facility already exists
            existing = db.execute_query(
                "SELECT facility_id FROM Facilities WHERE facility_name = ?",
                (name,)
            )
            
            if existing:
                db.disconnect()
                return jsonify({'success': False, 'message': 'Facility name already exists'})
            
            # Check which columns exist in the Facilities table
            columns_query = """
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'Facilities'
            """
            columns_result = db.execute_query(columns_query)
            existing_columns = [col['COLUMN_NAME'] for col in columns_result] if columns_result else []
            
            # Build INSERT query based on available columns
            if 'created_by' in existing_columns:
                # Use audit columns if they exist
                success = db.execute_query(
                    """INSERT INTO Facilities (facility_name, location, is_active, created_by, created_date)
                       VALUES (?, ?, 1, ?, GETDATE())""",
                    (name, location or None, session['user']['username'])
                )
            else:
                # Simple insert without audit columns
                success = db.execute_query(
                    """INSERT INTO Facilities (facility_name, location, is_active)
                       VALUES (?, ?, 1)""",
                    (name, location or None)
                )
            
            # Get the ID of the newly inserted facility
            if success:
                new_facility = db.execute_query(
                    "SELECT TOP 1 facility_id FROM Facilities WHERE facility_name = ? ORDER BY facility_id DESC",
                    (name,)
                )
                
                if new_facility:
                    facility_id = new_facility[0]['facility_id']
                    
                    # Log the creation in audit log
                    db.log_audit(
                        table_name='Facilities',
                        record_id=facility_id,
                        action_type='INSERT',
                        username=session['user']['username'],
                        ip=ip,
                        user_agent=user_agent,
                        notes=f"Created new facility: {name}"
                    )
                    
                    # Also log the initial values
                    initial_values = {
                        'facility_name': {'old': None, 'new': name},
                        'location': {'old': None, 'new': location or None},
                        'is_active': {'old': None, 'new': '1'}
                    }
                    
                    db.log_audit(
                        table_name='Facilities',
                        record_id=facility_id,
                        action_type='INSERT',
                        changes=initial_values,
                        username=session['user']['username'],
                        ip=ip,
                        user_agent=user_agent
                    )
            
            db.disconnect()
            
            if success:
                return jsonify({'success': True, 'message': 'Facility added successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to add facility'})
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'})
            
    except Exception as e:
        print(f"Error adding facility: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred'})

@admin_bp.route('/admin/facilities/edit/<int:facility_id>', methods=['POST'])
def edit_facility(facility_id):
    """Edit existing facility with detailed change tracking"""
    if not require_login(session) or not require_admin(session):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        
        if not name:
            return jsonify({'success': False, 'message': 'Facility name is required'})
        
        ip, user_agent = get_client_info()
        
        if db.connect():
            # Get current values for audit comparison
            old_record = db.get_record_before_update('Facilities', 'facility_id', facility_id)
            
            if not old_record:
                db.disconnect()
                return jsonify({'success': False, 'message': 'Facility not found'})
            
            # Check if new name conflicts with another facility
            existing = db.execute_query(
                "SELECT facility_id FROM Facilities WHERE facility_name = ? AND facility_id != ?",
                (name, facility_id)
            )
            
            if existing:
                db.disconnect()
                return jsonify({'success': False, 'message': 'Facility name already exists'})
            
            # Track changes
            changes = {}
            if old_record.get('facility_name') != name:
                changes['facility_name'] = {
                    'old': old_record.get('facility_name'),
                    'new': name
                }
            
            old_location = old_record.get('location', '')
            new_location = location or None
            if old_location != new_location:
                changes['location'] = {
                    'old': old_location,
                    'new': new_location
                }
            
            # Only update if there are changes
            if not changes:
                db.disconnect()
                return jsonify({'success': True, 'message': 'No changes detected'})
            
            # Check which columns exist
            columns_query = """
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'Facilities'
            """
            columns_result = db.execute_query(columns_query)
            existing_columns = [col['COLUMN_NAME'] for col in columns_result] if columns_result else []
            
            # Update facility based on available columns
            if 'modified_by' in existing_columns:
                success = db.execute_query(
                    """UPDATE Facilities 
                       SET facility_name = ?, location = ?, modified_by = ?, modified_date = GETDATE()
                       WHERE facility_id = ?""",
                    (name, location or None, session['user']['username'], facility_id)
                )
            else:
                success = db.execute_query(
                    """UPDATE Facilities 
                       SET facility_name = ?, location = ?
                       WHERE facility_id = ?""",
                    (name, location or None, facility_id)
                )
            
            # Log the changes in audit log
            if success and changes:
                db.log_audit(
                    table_name='Facilities',
                    record_id=facility_id,
                    action_type='UPDATE',
                    changes=changes,
                    username=session['user']['username'],
                    ip=ip,
                    user_agent=user_agent,
                    notes=f"Updated facility: {old_record.get('facility_name')} -> {name}"
                )
            
            db.disconnect()
            
            if success:
                change_summary = ', '.join([f"{k}: '{v['old']}' → '{v['new']}'" for k, v in changes.items()])
                return jsonify({'success': True, 'message': f'Facility updated. Changes: {change_summary}'})
            else:
                return jsonify({'success': False, 'message': 'Failed to update facility'})
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'})
            
    except Exception as e:
        print(f"Error editing facility: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred'})

@admin_bp.route('/admin/facilities/delete/<int:facility_id>', methods=['POST'])
def delete_facility(facility_id):
    """Soft delete (deactivate) facility with audit logging"""
    if not require_login(session) or not require_admin(session):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        ip, user_agent = get_client_info()
        
        if db.connect():
            # Get current facility details
            old_record = db.get_record_before_update('Facilities', 'facility_id', facility_id)
            
            if not old_record:
                db.disconnect()
                return jsonify({'success': False, 'message': 'Facility not found'})
            
            # Check if already inactive
            if not old_record.get('is_active'):
                db.disconnect()
                return jsonify({'success': False, 'message': 'Facility is already deactivated'})
            
            # Check if facility has active production lines
            lines = db.execute_query(
                "SELECT COUNT(*) as count FROM ProductionLines WHERE facility_id = ? AND is_active = 1",
                (facility_id,)
            )
            
            if lines and lines[0]['count'] > 0:
                db.disconnect()
                return jsonify({'success': False, 'message': 'Cannot deactivate facility with active production lines'})
            
            # Check which columns exist
            columns_query = """
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'Facilities'
            """
            columns_result = db.execute_query(columns_query)
            existing_columns = [col['COLUMN_NAME'] for col in columns_result] if columns_result else []
            
            # Deactivate facility based on available columns
            if 'modified_by' in existing_columns:
                success = db.execute_query(
                    """UPDATE Facilities 
                       SET is_active = 0, modified_by = ?, modified_date = GETDATE()
                       WHERE facility_id = ?""",
                    (session['user']['username'], facility_id)
                )
            else:
                success = db.execute_query(
                    """UPDATE Facilities 
                       SET is_active = 0
                       WHERE facility_id = ?""",
                    (facility_id,)
                )
            
            # Log the deactivation
            if success:
                changes = {
                    'is_active': {'old': '1', 'new': '0'}
                }
                
                db.log_audit(
                    table_name='Facilities',
                    record_id=facility_id,
                    action_type='DEACTIVATE',
                    changes=changes,
                    username=session['user']['username'],
                    ip=ip,
                    user_agent=user_agent,
                    notes=f"Deactivated facility: {old_record.get('facility_name')}"
                )
            
            db.disconnect()
            
            if success:
                return jsonify({'success': True, 'message': f"Facility '{old_record.get('facility_name')}' deactivated successfully"})
            else:
                return jsonify({'success': False, 'message': 'Failed to deactivate facility'})
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'})
            
    except Exception as e:
        print(f"Error deleting facility: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred'})

@admin_bp.route('/admin/facilities/history/<int:facility_id>')
def facility_history(facility_id):
    """View audit history for a specific facility"""
    if not require_login(session) or not require_admin(session):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        if db.connect():
            history = db.get_facility_history(facility_id)
            
            # Get facility details
            facility = db.execute_query(
                "SELECT * FROM Facilities WHERE facility_id = ?",
                (facility_id,)
            )
            
            db.disconnect()
            
            if facility:
                return jsonify({
                    'success': True,
                    'facility': facility[0],
                    'history': history
                })
            else:
                return jsonify({'success': False, 'message': 'Facility not found'})
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'})
            
    except Exception as e:
        print(f"Error getting facility history: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred'})

@admin_bp.route('/admin/lines')
def production_lines():
    """Manage production lines"""
    if not require_login(session):
        return redirect(url_for('main.login'))
    
    if not require_admin(session):
        flash('Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get all production lines and facilities
    lines = []
    facilities = []
    error_message = None
    
    try:
        if db.connect():
            # Check if tables exist
            if not db.check_table_exists('ProductionLines'):
                error_message = "ProductionLines table does not exist. Please run init_database.py to create tables."
                print(f"Error: {error_message}")
            elif not db.check_table_exists('Facilities'):
                error_message = "Facilities table does not exist. Please run init_database.py to create tables."
                print(f"Error: {error_message}")
            else:
                lines = db.get_production_lines(active_only=False)  # Show all including inactive
                facilities = db.get_facilities(active_only=True)    # Only active facilities for dropdown
                
                if lines is None:
                    lines = []
                else:
                    # Add safe defaults for missing fields
                    for line in lines:
                        if 'line_code' not in line:
                            line['line_code'] = None
                        if 'created_date' not in line:
                            line['created_date'] = None
                        if 'created_by' not in line:
                            line['created_by'] = None
                        if 'modified_date' not in line:
                            line['modified_date'] = None
                        if 'modified_by' not in line:
                            line['modified_by'] = None
                            
                if facilities is None:
                    facilities = []
                    
                print(f"Retrieved {len(lines)} production lines and {len(facilities)} facilities")
            db.disconnect()
        else:
            error_message = "Failed to connect to database. Check your database configuration."
            print("Error: Database connection failed")
    except Exception as e:
        error_message = f'Error loading production lines: {str(e)}'
        print(f"Exception in production_lines route: {str(e)}")
        lines = []
        facilities = []
    
    if error_message:
        flash(error_message, 'error')
    
    return render_template('admin/production_lines.html', 
                         lines=lines, 
                         facilities=facilities,
                         user=session['user'])

@admin_bp.route('/admin/lines/add', methods=['POST'])
def add_line():
    """Add new production line with audit logging"""
    if not require_login(session) or not require_admin(session):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        facility_id = request.form.get('facility_id')
        line_name = request.form.get('line_name', '').strip()
        line_code = request.form.get('line_code', '').strip()
        
        if not facility_id or not line_name:
            return jsonify({'success': False, 'message': 'Facility and line name are required'})
        
        ip, user_agent = get_client_info()
        
        if db.connect():
            # Check if line name already exists in this facility
            existing = db.execute_query(
                "SELECT line_id FROM ProductionLines WHERE facility_id = ? AND line_name = ?",
                (facility_id, line_name)
            )
            
            if existing:
                db.disconnect()
                return jsonify({'success': False, 'message': 'Line name already exists in this facility'})
            
            # Get facility name for logging
            facility_info = db.execute_query(
                "SELECT facility_name FROM Facilities WHERE facility_id = ?",
                (facility_id,)
            )
            facility_name = facility_info[0]['facility_name'] if facility_info else 'Unknown'
            
            # Check which columns exist
            columns_query = """
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'ProductionLines'
            """
            columns_result = db.execute_query(columns_query)
            existing_columns = [col['COLUMN_NAME'] for col in columns_result] if columns_result else []
            
            # Build INSERT query based on available columns
            if 'created_by' in existing_columns:
                if 'line_code' in existing_columns:
                    success = db.execute_query(
                        """INSERT INTO ProductionLines (facility_id, line_name, line_code, is_active, created_by, created_date)
                           VALUES (?, ?, ?, 1, ?, GETDATE())""",
                        (facility_id, line_name, line_code or None, session['user']['username'])
                    )
                else:
                    success = db.execute_query(
                        """INSERT INTO ProductionLines (facility_id, line_name, is_active, created_by, created_date)
                           VALUES (?, ?, 1, ?, GETDATE())""",
                        (facility_id, line_name, session['user']['username'])
                    )
            else:
                if 'line_code' in existing_columns:
                    success = db.execute_query(
                        """INSERT INTO ProductionLines (facility_id, line_name, line_code, is_active)
                           VALUES (?, ?, ?, 1)""",
                        (facility_id, line_name, line_code or None)
                    )
                else:
                    success = db.execute_query(
                        """INSERT INTO ProductionLines (facility_id, line_name, is_active)
                           VALUES (?, ?, 1)""",
                        (facility_id, line_name)
                    )
            
            # Get the ID of the newly inserted line
            if success:
                new_line = db.execute_query(
                    "SELECT TOP 1 line_id FROM ProductionLines WHERE facility_id = ? AND line_name = ? ORDER BY line_id DESC",
                    (facility_id, line_name)
                )
                
                if new_line:
                    line_id = new_line[0]['line_id']
                    
                    # Log the creation
                    initial_values = {
                        'facility_id': {'old': None, 'new': str(facility_id)},
                        'line_name': {'old': None, 'new': line_name},
                        'is_active': {'old': None, 'new': '1'}
                    }
                    
                    if 'line_code' in existing_columns and line_code:
                        initial_values['line_code'] = {'old': None, 'new': line_code}
                    
                    db.log_audit(
                        table_name='ProductionLines',
                        record_id=line_id,
                        action_type='INSERT',
                        changes=initial_values,
                        username=session['user']['username'],
                        ip=ip,
                        user_agent=user_agent,
                        notes=f"Created new line '{line_name}' in facility '{facility_name}'"
                    )
            
            db.disconnect()
            
            if success:
                return jsonify({'success': True, 'message': 'Production line added successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to add production line'})
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'})
            
    except Exception as e:
        print(f"Error adding line: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred'})

@admin_bp.route('/admin/lines/edit/<int:line_id>', methods=['POST'])
def edit_line(line_id):
    """Edit existing production line with detailed change tracking"""
    if not require_login(session) or not require_admin(session):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        line_name = request.form.get('line_name', '').strip()
        line_code = request.form.get('line_code', '').strip()
        
        if not line_name:
            return jsonify({'success': False, 'message': 'Line name is required'})
        
        ip, user_agent = get_client_info()
        
        if db.connect():
            # Get current values for audit comparison
            old_record = db.get_record_before_update('ProductionLines', 'line_id', line_id)
            
            if not old_record:
                db.disconnect()
                return jsonify({'success': False, 'message': 'Production line not found'})
            
            facility_id = old_record['facility_id']
            
            # Check if new name conflicts
            existing = db.execute_query(
                "SELECT line_id FROM ProductionLines WHERE facility_id = ? AND line_name = ? AND line_id != ?",
                (facility_id, line_name, line_id)
            )
            
            if existing:
                db.disconnect()
                return jsonify({'success': False, 'message': 'Line name already exists in this facility'})
            
            # Track changes
            changes = {}
            if old_record.get('line_name') != line_name:
                changes['line_name'] = {
                    'old': old_record.get('line_name'),
                    'new': line_name
                }
            
            # Check if line_code exists in the record
            if 'line_code' in old_record:
                old_code = old_record.get('line_code', '')
                new_code = line_code or None
                if old_code != new_code:
                    changes['line_code'] = {
                        'old': old_code,
                        'new': new_code
                    }
            
            # Only update if there are changes
            if not changes:
                db.disconnect()
                return jsonify({'success': True, 'message': 'No changes detected'})
            
            # Check which columns exist
            columns_query = """
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'ProductionLines'
            """
            columns_result = db.execute_query(columns_query)
            existing_columns = [col['COLUMN_NAME'] for col in columns_result] if columns_result else []
            
            # Build UPDATE query based on available columns
            if 'modified_by' in existing_columns:
                if 'line_code' in existing_columns:
                    success = db.execute_query(
                        """UPDATE ProductionLines 
                           SET line_name = ?, line_code = ?, modified_by = ?, modified_date = GETDATE()
                           WHERE line_id = ?""",
                        (line_name, line_code or None, session['user']['username'], line_id)
                    )
                else:
                    success = db.execute_query(
                        """UPDATE ProductionLines 
                           SET line_name = ?, modified_by = ?, modified_date = GETDATE()
                           WHERE line_id = ?""",
                        (line_name, session['user']['username'], line_id)
                    )
            else:
                if 'line_code' in existing_columns:
                    success = db.execute_query(
                        """UPDATE ProductionLines 
                           SET line_name = ?, line_code = ?
                           WHERE line_id = ?""",
                        (line_name, line_code or None, line_id)
                    )
                else:
                    success = db.execute_query(
                        """UPDATE ProductionLines 
                           SET line_name = ?
                           WHERE line_id = ?""",
                        (line_name, line_id)
                    )
            
            # Log the changes
            if success and changes:
                db.log_audit(
                    table_name='ProductionLines',
                    record_id=line_id,
                    action_type='UPDATE',
                    changes=changes,
                    username=session['user']['username'],
                    ip=ip,
                    user_agent=user_agent,
                    notes=f"Updated production line: {old_record.get('line_name')}"
                )
            
            db.disconnect()
            
            if success:
                change_summary = ', '.join([f"{k}: '{v['old']}' → '{v['new']}'" for k, v in changes.items()])
                return jsonify({'success': True, 'message': f'Production line updated. Changes: {change_summary}'})
            else:
                return jsonify({'success': False, 'message': 'Failed to update production line'})
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'})
            
    except Exception as e:
        print(f"Error editing line: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred'})

@admin_bp.route('/admin/lines/delete/<int:line_id>', methods=['POST'])
def delete_line(line_id):
    """Soft delete (deactivate) production line with audit logging"""
    if not require_login(session) or not require_admin(session):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        ip, user_agent = get_client_info()
        
        if db.connect():
            # Get current line details
            old_record = db.get_record_before_update('ProductionLines', 'line_id', line_id)
            
            if not old_record:
                db.disconnect()
                return jsonify({'success': False, 'message': 'Production line not found'})
            
            # Check if already inactive
            if not old_record.get('is_active'):
                db.disconnect()
                return jsonify({'success': False, 'message': 'Production line is already deactivated'})
            
            # Check if line has downtime records
            downtimes = db.execute_query(
                "SELECT COUNT(*) as count FROM Downtimes WHERE line_id = ?",
                (line_id,)
            )
            
            # Check which columns exist
            columns_query = """
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'ProductionLines'
            """
            columns_result = db.execute_query(columns_query)
            existing_columns = [col['COLUMN_NAME'] for col in columns_result] if columns_result else []
            
            # Deactivate based on available columns
            if 'modified_by' in existing_columns:
                success = db.execute_query(
                    """UPDATE ProductionLines 
                       SET is_active = 0, modified_by = ?, modified_date = GETDATE()
                       WHERE line_id = ?""",
                    (session['user']['username'], line_id)
                )
            else:
                success = db.execute_query(
                    """UPDATE ProductionLines 
                       SET is_active = 0
                       WHERE line_id = ?""",
                    (line_id,)
                )
            
            # Log the deactivation
            if success:
                changes = {
                    'is_active': {'old': '1', 'new': '0'}
                }
                
                db.log_audit(
                    table_name='ProductionLines',
                    record_id=line_id,
                    action_type='DEACTIVATE',
                    changes=changes,
                    username=session['user']['username'],
                    ip=ip,
                    user_agent=user_agent,
                    notes=f"Deactivated production line: {old_record.get('line_name')}"
                )
            
            if downtimes and downtimes[0]['count'] > 0:
                message = f"Production line '{old_record.get('line_name')}' deactivated (has {downtimes[0]['count']} historical records)"
            else:
                message = f"Production line '{old_record.get('line_name')}' deactivated successfully"
            
            db.disconnect()
            
            if success:
                return jsonify({'success': True, 'message': message})
            else:
                return jsonify({'success': False, 'message': 'Failed to deactivate production line'})
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'})
            
    except Exception as e:
        print(f"Error deleting line: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred'})

@admin_bp.route('/admin/lines/history/<int:line_id>')
def line_history(line_id):
    """View audit history for a specific production line"""
    if not require_login(session) or not require_admin(session):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        if db.connect():
            history = db.get_line_history(line_id)
            
            # Get line details
            line = db.execute_query(
                """SELECT pl.*, f.facility_name 
                   FROM ProductionLines pl
                   JOIN Facilities f ON pl.facility_id = f.facility_id
                   WHERE pl.line_id = ?""",
                (line_id,)
            )
            
            db.disconnect()
            
            if line:
                return jsonify({
                    'success': True,
                    'line': line[0],
                    'history': history
                })
            else:
                return jsonify({'success': False, 'message': 'Production line not found'})
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'})
            
    except Exception as e:
        print(f"Error getting line history: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred'})

@admin_bp.route('/admin/audit-log')
def audit_log():
    """View complete audit log"""
    if not require_login(session):
        return redirect(url_for('main.login'))
    
    if not require_admin(session):
        flash('Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get audit history
    history = []
    
    try:
        if db.connect():
            # Get last 30 days of audit history
            history = db.get_audit_history(days=30)
            db.disconnect()
    except Exception as e:
        print(f"Error loading audit log: {str(e)}")
        flash('Error loading audit log', 'error')
    
    return render_template('admin/audit_log.html', 
                         history=history,
                         user=session['user'])

# Keep the existing edit_line and delete_line functions but add similar audit logging...