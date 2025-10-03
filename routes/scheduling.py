"""
Production Scheduling routes
Handles display and updates for the production scheduling grid.
"""

from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for, flash
from auth import require_login, require_admin
from routes.main import validate_session
from database import scheduling_db
import traceback

# The url_prefix makes this blueprint's routes available under '/scheduling'
scheduling_bp = Blueprint('scheduling', __name__, url_prefix='/scheduling')

@scheduling_bp.route('/')
@validate_session
def index():
    """Renders the main production scheduling grid page."""
    if not require_login(session):
        return redirect(url_for('main.login'))
    
    if not require_admin(session):
        flash('Admin privileges are required to access the scheduling module.', 'error')
        return redirect(url_for('main.dashboard'))

    # Fetch data from ERP joined with local projections
    schedule_data = scheduling_db.get_schedule_data()
    
    return render_template('scheduling/index.html', schedule_data=schedule_data)

@scheduling_bp.route('/api/update-projection', methods=['POST'])
@validate_session
def update_projection():
    """API endpoint to save projection data from the grid."""
    if not require_login(session) or not require_admin(session):
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Invalid data received'}), 400

        # Extract data from the JSON payload
        so_number = data.get('so_number')
        part_number = data.get('part_number')
        risk_type = data.get('risk_type')
        quantity = data.get('quantity')
        username = session.get('user', {}).get('username', 'unknown')

        # Basic validation
        if not all([so_number, part_number, risk_type]):
             return jsonify({'success': False, 'message': 'Missing required fields: so_number, part_number, or risk_type'}), 400

        try:
            quantity = float(quantity) if quantity is not None else 0.0
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Quantity must be a valid number'}), 400

        # Call the database method to perform the upsert
        success, message = scheduling_db.update_projection(
            so_number=so_number,
            part_number=part_number,
            risk_type=risk_type,
            quantity=quantity,
            username=username
        )

        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'An internal server error occurred.'}), 500