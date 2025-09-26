"""
Downtime Categories management routes
Handles hierarchical category structure with main and sub-categories
"""

from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify, flash
from auth import require_login, require_admin
from database import db

# Create blueprint
categories_bp = Blueprint('categories', __name__)

def get_client_info():
    """Get client IP and user agent for audit logging"""
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    user_agent = request.environ.get('HTTP_USER_AGENT', '')[:500]
    return ip, user_agent

@categories_bp.route('/admin/categories')
def categories():
    """Manage downtime categories"""
    if not require_login(session):
        return redirect(url_for('main.login'))
    
    if not require_admin(session):
        flash('Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    categories_list = []
    error_message = None
    
    try:
        if db.connect():
            # Check if table exists
            if not db.check_table_exists('DowntimeCategories'):
                error_message = "DowntimeCategories table does not exist. Please run init_database.py to create tables."
            else:
                # Get all categories with parent-child relationship
                query = """
                    SELECT 
                        c1.category_id,
                        c1.category_name,
                        c1.category_code,
                        c1.description,
                        c1.parent_id,
                        c1.color_code,
                        c1.notification_required,
                        c1.is_active,
                        c1.created_date,
                        c1.created_by,
                        c1.modified_date,
                        c1.modified_by,
                        c2.category_name as parent_name,
                        c2.category_code as parent_code
                    FROM DowntimeCategories c1
                    LEFT JOIN DowntimeCategories c2 ON c1.parent_id = c2.category_id
                    ORDER BY 
                        CASE WHEN c1.parent_id IS NULL THEN c1.category_code ELSE c2.category_code END,
                        c1.parent_id,
                        c1.category_code
                """
                categories_list = db.execute_query(query)
                
                # Organize categories hierarchically
                main_categories = {}
                for cat in categories_list:
                    if cat['parent_id'] is None:
                        cat['subcategories'] = []
                        main_categories[cat['category_id']] = cat
                
                # Add subcategories to their parents
                for cat in categories_list:
                    if cat['parent_id'] and cat['parent_id'] in main_categories:
                        main_categories[cat['parent_id']]['subcategories'].append(cat)
                
                # Convert to list for template
                categories_list = list(main_categories.values())
                
            db.disconnect()
        else:
            error_message = "Failed to connect to database."
    except Exception as e:
        error_message = f'Error loading categories: {str(e)}'
        print(f"Exception in categories route: {str(e)}")
    
    if error_message:
        flash(error_message, 'error')
    
    return render_template('admin/categories.html', 
                         categories=categories_list, 
                         user=session['user'])

@categories_bp.route('/admin/categories/add', methods=['POST'])
def add_category():
    """Add new category with audit logging"""
    if not require_login(session) or not require_admin(session):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        category_name = request.form.get('category_name', '').strip()
        category_code = request.form.get('category_code', '').strip().upper()
        description = request.form.get('description', '').strip()
        parent_id = request.form.get('parent_id')
        color_code = request.form.get('color_code', '#667eea')
        notification_required = request.form.get('notification_required') == 'true'
        
        if not category_name or not category_code:
            return jsonify({'success': False, 'message': 'Category name and code are required'})
        
        # Convert empty parent_id to None
        if parent_id == '' or parent_id == '0':
            parent_id = None
        else:
            parent_id = int(parent_id)
        
        ip, user_agent = get_client_info()
        
        if db.connect():
            # Check if code already exists
            existing = db.execute_query(
                "SELECT category_id FROM DowntimeCategories WHERE category_code = ?",
                (category_code,)
            )
            
            if existing:
                db.disconnect()
                return jsonify({'success': False, 'message': 'Category code already exists'})
            
            # Check which columns exist
            columns_query = """
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'DowntimeCategories'
            """
            columns_result = db.execute_query(columns_query)
            existing_columns = [col['COLUMN_NAME'] for col in columns_result] if columns_result else []
            
            # Build INSERT query based on available columns
            if 'parent_id' in existing_columns:
                success = db.execute_query(
                    """INSERT INTO DowntimeCategories 
                       (category_name, category_code, description, parent_id, 
                        color_code, notification_required, is_active, created_by, created_date)
                       VALUES (?, ?, ?, ?, ?, ?, 1, ?, GETDATE())""",
                    (category_name, category_code, description or None, parent_id,
                     color_code, 1 if notification_required else 0, session['user']['username'])
                )
            else:
                # Legacy table structure without parent_id
                success = db.execute_query(
                    """INSERT INTO DowntimeCategories 
                       (category_name, category_code, description, 
                        color_code, notification_required, is_active, created_by, created_date)
                       VALUES (?, ?, ?, ?, ?, 1, ?, GETDATE())""",
                    (category_name, category_code, description or None,
                     color_code, 1 if notification_required else 0, session['user']['username'])
                )
            
            # Get the new category ID for audit logging
            if success:
                new_category = db.execute_query(
                    "SELECT TOP 1 category_id FROM DowntimeCategories WHERE category_code = ? ORDER BY category_id DESC",
                    (category_code,)
                )
                
                if new_category:
                    category_id = new_category[0]['category_id']
                    
                    # Log the creation
                    initial_values = {
                        'category_name': {'old': None, 'new': category_name},
                        'category_code': {'old': None, 'new': category_code},
                        'is_active': {'old': None, 'new': '1'}
                    }
                    
                    if parent_id:
                        initial_values['parent_id'] = {'old': None, 'new': str(parent_id)}
                    
                    db.log_audit(
                        table_name='DowntimeCategories',
                        record_id=category_id,
                        action_type='INSERT',
                        changes=initial_values,
                        username=session['user']['username'],
                        ip=ip,
                        user_agent=user_agent,
                        notes=f"Created category: {category_code} - {category_name}"
                    )
            
            db.disconnect()
            
            if success:
                return jsonify({'success': True, 'message': 'Category added successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to add category'})
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'})
            
    except Exception as e:
        print(f"Error adding category: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred'})

@categories_bp.route('/admin/categories/edit/<int:category_id>', methods=['POST'])
def edit_category(category_id):
    """Edit existing category with detailed change tracking"""
    if not require_login(session) or not require_admin(session):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        category_name = request.form.get('category_name', '').strip()
        description = request.form.get('description', '').strip()
        color_code = request.form.get('color_code', '#667eea')
        notification_required = request.form.get('notification_required') == 'true'
        
        if not category_name:
            return jsonify({'success': False, 'message': 'Category name is required'})
        
        ip, user_agent = get_client_info()
        
        if db.connect():
            # Get current values for audit comparison
            old_record = db.get_record_before_update('DowntimeCategories', 'category_id', category_id)
            
            if not old_record:
                db.disconnect()
                return jsonify({'success': False, 'message': 'Category not found'})
            
            # Track changes
            changes = {}
            if old_record.get('category_name') != category_name:
                changes['category_name'] = {
                    'old': old_record.get('category_name'),
                    'new': category_name
                }
            
            old_desc = old_record.get('description', '')
            new_desc = description or None
            if old_desc != new_desc:
                changes['description'] = {
                    'old': old_desc,
                    'new': new_desc
                }
            
            if old_record.get('color_code') != color_code:
                changes['color_code'] = {
                    'old': old_record.get('color_code'),
                    'new': color_code
                }
            
            old_notification = bool(old_record.get('notification_required'))
            if old_notification != notification_required:
                changes['notification_required'] = {
                    'old': '1' if old_notification else '0',
                    'new': '1' if notification_required else '0'
                }
            
            # Only update if there are changes
            if not changes:
                db.disconnect()
                return jsonify({'success': True, 'message': 'No changes detected'})
            
            # Update category
            success = db.execute_query(
                """UPDATE DowntimeCategories 
                   SET category_name = ?, description = ?, color_code = ?, 
                       notification_required = ?, modified_by = ?, modified_date = GETDATE()
                   WHERE category_id = ?""",
                (category_name, description or None, color_code, 
                 1 if notification_required else 0, session['user']['username'], category_id)
            )
            
            # Log the changes
            if success and changes:
                db.log_audit(
                    table_name='DowntimeCategories',
                    record_id=category_id,
                    action_type='UPDATE',
                    changes=changes,
                    username=session['user']['username'],
                    ip=ip,
                    user_agent=user_agent,
                    notes=f"Updated category: {old_record.get('category_code')} - {old_record.get('category_name')}"
                )
            
            db.disconnect()
            
            if success:
                return jsonify({'success': True, 'message': 'Category updated successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to update category'})
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'})
            
    except Exception as e:
        print(f"Error editing category: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred'})

@categories_bp.route('/admin/categories/delete/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    """Deactivate category with audit logging"""
    if not require_login(session) or not require_admin(session):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        ip, user_agent = get_client_info()
        
        if db.connect():
            # Get current category details
            old_record = db.get_record_before_update('DowntimeCategories', 'category_id', category_id)
            
            if not old_record:
                db.disconnect()
                return jsonify({'success': False, 'message': 'Category not found'})
            
            # Check if already inactive
            if not old_record.get('is_active'):
                db.disconnect()
                return jsonify({'success': False, 'message': 'Category is already deactivated'})
            
            # Check if category has subcategories
            subcategories = db.execute_query(
                "SELECT COUNT(*) as count FROM DowntimeCategories WHERE parent_id = ? AND is_active = 1",
                (category_id,)
            )
            
            if subcategories and subcategories[0]['count'] > 0:
                db.disconnect()
                return jsonify({'success': False, 'message': 'Cannot deactivate category with active subcategories'})
            
            # Check if category is used in downtime records
            downtimes = db.execute_query(
                "SELECT COUNT(*) as count FROM Downtimes WHERE category_id = ?",
                (category_id,)
            )
            
            # Deactivate category
            success = db.execute_query(
                """UPDATE DowntimeCategories 
                   SET is_active = 0, modified_by = ?, modified_date = GETDATE()
                   WHERE category_id = ?""",
                (session['user']['username'], category_id)
            )
            
            # Log the deactivation
            if success:
                changes = {
                    'is_active': {'old': '1', 'new': '0'}
                }
                
                db.log_audit(
                    table_name='DowntimeCategories',
                    record_id=category_id,
                    action_type='DEACTIVATE',
                    changes=changes,
                    username=session['user']['username'],
                    ip=ip,
                    user_agent=user_agent,
                    notes=f"Deactivated category: {old_record.get('category_code')} - {old_record.get('category_name')}"
                )
            
            if downtimes and downtimes[0]['count'] > 0:
                message = f"Category '{old_record.get('category_name')}' deactivated (has {downtimes[0]['count']} historical records)"
            else:
                message = f"Category '{old_record.get('category_name')}' deactivated successfully"
            
            db.disconnect()
            
            if success:
                return jsonify({'success': True, 'message': message})
            else:
                return jsonify({'success': False, 'message': 'Failed to deactivate category'})
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'})
            
    except Exception as e:
        print(f"Error deleting category: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred'})

@categories_bp.route('/admin/categories/init-standard', methods=['POST'])
def init_standard_categories():
    """Initialize standard manufacturing downtime categories"""
    if not require_login(session) or not require_admin(session):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        ip, user_agent = get_client_info()
        
        # Standard manufacturing downtime categories
        standard_categories = [
            # Equipment/Mechanical
            {'code': 'EQ', 'name': 'Equipment/Mechanical', 'color': '#e53e3e', 'parent': None, 'notify': True, 
             'subcategories': [
                 {'code': 'EQ00', 'name': 'Mechanical Failure', 'color': '#e53e3e'},
                 {'code': 'EQ01', 'name': 'Electrical Failure', 'color': '#e53e3e'},
                 {'code': 'EQ02', 'name': 'Hydraulic/Pneumatic', 'color': '#e53e3e'},
                 {'code': 'EQ03', 'name': 'Control System', 'color': '#e53e3e'},
                 {'code': 'EQ99', 'name': 'Other Equipment', 'color': '#e53e3e'}
             ]},
            # Material
            {'code': 'MT', 'name': 'Material', 'color': '#dd6b20', 'parent': None, 'notify': True,
             'subcategories': [
                 {'code': 'MT00', 'name': 'Material Shortage', 'color': '#dd6b20'},
                 {'code': 'MT01', 'name': 'Wrong Material', 'color': '#dd6b20'},
                 {'code': 'MT02', 'name': 'Material Quality Issue', 'color': '#dd6b20'},
                 {'code': 'MT99', 'name': 'Other Material', 'color': '#dd6b20'}
             ]},
            # Quality
            {'code': 'QC', 'name': 'Quality Control', 'color': '#d69e2e', 'parent': None, 'notify': True,
             'subcategories': [
                 {'code': 'QC00', 'name': 'Quality Hold', 'color': '#d69e2e'},
                 {'code': 'QC01', 'name': 'Inspection', 'color': '#d69e2e'},
                 {'code': 'QC02', 'name': 'Rework', 'color': '#d69e2e'},
                 {'code': 'QC03', 'name': 'Scrap', 'color': '#d69e2e'},
                 {'code': 'QC99', 'name': 'Other Quality', 'color': '#d69e2e'}
             ]},
            # Changeover/Setup
            {'code': 'CO', 'name': 'Changeover/Setup', 'color': '#38a169', 'parent': None, 'notify': False,
             'subcategories': [
                 {'code': 'CO00', 'name': 'Product Changeover', 'color': '#38a169'},
                 {'code': 'CO01', 'name': 'Tool Change', 'color': '#38a169'},
                 {'code': 'CO02', 'name': 'Setup/Adjustment', 'color': '#38a169'},
                 {'code': 'CO99', 'name': 'Other Changeover', 'color': '#38a169'}
             ]},
            # Meetings
            {'code': 'ME', 'name': 'Meeting', 'color': '#3182ce', 'parent': None, 'notify': False,
             'subcategories': [
                 {'code': 'ME00', 'name': 'Safety Meeting', 'color': '#3182ce'},
                 {'code': 'ME01', 'name': 'Town Hall Meeting', 'color': '#3182ce'},
                 {'code': 'ME02', 'name': 'Team Meeting', 'color': '#3182ce'},
                 {'code': 'ME99', 'name': 'Other Meeting', 'color': '#3182ce'}
             ]},
            # Training
            {'code': 'TR', 'name': 'Training', 'color': '#805ad5', 'parent': None, 'notify': False,
             'subcategories': [
                 {'code': 'TR00', 'name': 'Operator Training', 'color': '#805ad5'},
                 {'code': 'TR01', 'name': 'Safety Training', 'color': '#805ad5'},
                 {'code': 'TR02', 'name': 'Skills Development', 'color': '#805ad5'},
                 {'code': 'TR99', 'name': 'Other Training', 'color': '#805ad5'}
             ]},
            # Operator
            {'code': 'OP', 'name': 'Operator', 'color': '#d53f8c', 'parent': None, 'notify': True,
             'subcategories': [
                 {'code': 'OP00', 'name': 'No Operator', 'color': '#d53f8c'},
                 {'code': 'OP01', 'name': 'Operator Error', 'color': '#d53f8c'},
                 {'code': 'OP02', 'name': 'Insufficient Staff', 'color': '#d53f8c'},
                 {'code': 'OP99', 'name': 'Other Operator', 'color': '#d53f8c'}
             ]},
            # Breaks
            {'code': 'BR', 'name': 'Break', 'color': '#319795', 'parent': None, 'notify': False,
             'subcategories': [
                 {'code': 'BR00', 'name': 'Scheduled Break', 'color': '#319795'},
                 {'code': 'BR01', 'name': 'Lunch Break', 'color': '#319795'},
                 {'code': 'BR02', 'name': 'Shift Change', 'color': '#319795'}
             ]},
            # Maintenance
            {'code': 'PM', 'name': 'Planned Maintenance', 'color': '#2d3748', 'parent': None, 'notify': False,
             'subcategories': [
                 {'code': 'PM00', 'name': 'Preventive Maintenance', 'color': '#2d3748'},
                 {'code': 'PM01', 'name': 'Cleaning', 'color': '#2d3748'},
                 {'code': 'PM02', 'name': 'Calibration', 'color': '#2d3748'},
                 {'code': 'PM99', 'name': 'Other Maintenance', 'color': '#2d3748'}
             ]},
            # Other
            {'code': 'OT', 'name': 'Other', 'color': '#718096', 'parent': None, 'notify': False,
             'subcategories': [
                 {'code': 'OT00', 'name': 'Power Outage', 'color': '#718096'},
                 {'code': 'OT01', 'name': 'IT System Issue', 'color': '#718096'},
                 {'code': 'OT02', 'name': 'Weather/Natural', 'color': '#718096'},
                 {'code': 'OT99', 'name': 'Other/Unspecified', 'color': '#718096'}
             ]}
        ]
        
        if db.connect():
            added = 0
            skipped = 0
            
            # Check if parent_id column exists
            columns_query = """
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'DowntimeCategories'
            """
            columns_result = db.execute_query(columns_query)
            existing_columns = [col['COLUMN_NAME'] for col in columns_result] if columns_result else []
            has_parent_id = 'parent_id' in existing_columns
            
            for main_cat in standard_categories:
                # Check if main category exists
                existing = db.execute_query(
                    "SELECT category_id FROM DowntimeCategories WHERE category_code = ?",
                    (main_cat['code'],)
                )
                
                if not existing:
                    # Add main category
                    if has_parent_id:
                        success = db.execute_query(
                            """INSERT INTO DowntimeCategories 
                               (category_name, category_code, description, parent_id,
                                color_code, notification_required, is_active, created_by, created_date)
                               VALUES (?, ?, ?, NULL, ?, ?, 1, ?, GETDATE())""",
                            (main_cat['name'], main_cat['code'], f"Main category for {main_cat['name']}",
                             main_cat['color'], 1 if main_cat.get('notify', False) else 0, 
                             session['user']['username'])
                        )
                    else:
                        success = db.execute_query(
                            """INSERT INTO DowntimeCategories 
                               (category_name, category_code, description,
                                color_code, notification_required, is_active, created_by, created_date)
                               VALUES (?, ?, ?, ?, ?, 1, ?, GETDATE())""",
                            (main_cat['name'], main_cat['code'], f"Main category for {main_cat['name']}",
                             main_cat['color'], 1 if main_cat.get('notify', False) else 0, 
                             session['user']['username'])
                        )
                    
                    if success:
                        added += 1
                        
                        # Get the parent ID
                        parent_result = db.execute_query(
                            "SELECT category_id FROM DowntimeCategories WHERE category_code = ?",
                            (main_cat['code'],)
                        )
                        
                        if parent_result and has_parent_id and 'subcategories' in main_cat:
                            parent_id = parent_result[0]['category_id']
                            
                            # Add subcategories
                            for sub_cat in main_cat['subcategories']:
                                # Check if subcategory exists
                                sub_existing = db.execute_query(
                                    "SELECT category_id FROM DowntimeCategories WHERE category_code = ?",
                                    (sub_cat['code'],)
                                )
                                
                                if not sub_existing:
                                    sub_success = db.execute_query(
                                        """INSERT INTO DowntimeCategories 
                                           (category_name, category_code, description, parent_id,
                                            color_code, notification_required, is_active, created_by, created_date)
                                           VALUES (?, ?, ?, ?, ?, ?, 1, ?, GETDATE())""",
                                        (sub_cat['name'], sub_cat['code'], None, parent_id,
                                         sub_cat['color'], 0, session['user']['username'])
                                    )
                                    if sub_success:
                                        added += 1
                                else:
                                    skipped += 1
                else:
                    skipped += 1
                    
                    # Still try to add missing subcategories if parent exists
                    if has_parent_id and 'subcategories' in main_cat:
                        parent_id = existing[0]['category_id']
                        for sub_cat in main_cat['subcategories']:
                            sub_existing = db.execute_query(
                                "SELECT category_id FROM DowntimeCategories WHERE category_code = ?",
                                (sub_cat['code'],)
                            )
                            if not sub_existing:
                                db.execute_query(
                                    """INSERT INTO DowntimeCategories 
                                       (category_name, category_code, description, parent_id,
                                        color_code, notification_required, is_active, created_by, created_date)
                                       VALUES (?, ?, ?, ?, ?, ?, 1, ?, GETDATE())""",
                                    (sub_cat['name'], sub_cat['code'], None, parent_id,
                                     sub_cat['color'], 0, session['user']['username'])
                                )
                                added += 1
            
            # Log the bulk operation
            db.log_audit(
                table_name='DowntimeCategories',
                record_id=0,
                action_type='BULK_INSERT',
                username=session['user']['username'],
                ip=ip,
                user_agent=user_agent,
                notes=f"Initialized standard categories: {added} added, {skipped} already existed"
            )
            
            db.disconnect()
            
            return jsonify({
                'success': True, 
                'message': f'Standard categories initialized: {added} added, {skipped} already existed'
            })
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'})
            
    except Exception as e:
        print(f"Error initializing standard categories: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred'})