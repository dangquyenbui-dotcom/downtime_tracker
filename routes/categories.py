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