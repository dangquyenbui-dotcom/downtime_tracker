# dangquyenbui-dotcom/downtime_tracker/downtime_tracker-5bb4163f1c166071f5c302dee6ed03e0344576eb/routes/mrp.py
"""
MRP (Material Requirements Planning) Viewer routes.
"""

from flask import Blueprint, render_template, session, redirect, url_for, flash
from auth import require_login
from routes.main import validate_session
from database.mrp_service import mrp_service

mrp_bp = Blueprint('mrp', __name__, url_prefix='/mrp')

@mrp_bp.route('/')
@validate_session
def view_mrp():
    """Renders the main MRP results page."""
    if not (session.get('user', {}).get('is_admin') or session.get('user', {}).get('is_scheduling_admin')):
        flash('MRP access is restricted to administrators and scheduling admins.', 'error')
        return redirect(url_for('main.dashboard'))

    try:
        mrp_results = mrp_service.calculate_mrp_suggestions()
    except Exception as e:
        flash(f'An error occurred while running the MRP calculation: {e}', 'error')
        mrp_results = []

    return render_template(
        'mrp/index.html',
        user=session['user'],
        mrp_results=mrp_results
    )