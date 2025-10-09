# dangquyenbui-dotcom/downtime_tracker/downtime_tracker-5bb4163f1c166071f5c302dee6ed03e0344576eb/routes/mrp.py
"""
MRP (Material Requirements Planning) Viewer routes.
"""

from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify, send_file
from auth import require_login
from routes.main import validate_session
from database.mrp_service import mrp_service
import openpyxl
from io import BytesIO
from datetime import datetime

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

@mrp_bp.route('/api/export-xlsx', methods=['POST'])
@validate_session
def export_mrp_xlsx():
    """API endpoint to export the visible MRP data to an XLSX file."""
    if not (session.get('user', {}).get('is_admin') or session.get('user', {}).get('is_scheduling_admin')):
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    try:
        data = request.get_json()
        headers = data.get('headers', [])
        rows = data.get('rows', [])

        if not headers or not rows:
            return jsonify({'success': False, 'message': 'No data to export'}), 400

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "MRP Export"
        ws.append(headers)
        
        for row_data in rows:
            ws.append(row_data)

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mrp_export_{timestamp}.xlsx"

        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        print(f"Error exporting MRP: {e}")
        return jsonify({'success': False, 'message': 'An error occurred during export.'}), 500