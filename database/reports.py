"""
Database operations for generating analytical reports.
"""

from .connection import get_db
from datetime import datetime

class ReportsDB:
    """Reporting database operations"""

    def __init__(self):
        self.db = get_db()

    def get_downtime_summary(self, start_date, end_date, facility_id=None, line_id=None):
        """
        Generates aggregated data for the downtime summary report.
        """
        with self.db.get_connection() as conn:
            
            # Base query and params
            base_sql = """
                FROM Downtimes d
                JOIN ProductionLines pl ON d.line_id = pl.line_id
                JOIN Facilities f ON pl.facility_id = f.facility_id
                JOIN DowntimeCategories dc ON d.category_id = dc.category_id
                WHERE d.is_deleted = 0
                AND d.start_time BETWEEN ? AND ?
            """
            params = [start_date, end_date]

            # Append filters
            if facility_id:
                base_sql += " AND f.facility_id = ? "
                params.append(facility_id)
            if line_id:
                base_sql += " AND pl.line_id = ? "
                params.append(line_id)

            # 1. Overall Stats
            stats_query = f"SELECT COUNT(*) as total_events, SUM(d.duration_minutes) as total_minutes {base_sql}"
            overall_stats = conn.execute_query(stats_query, params)

            # 2. Downtime by Category
            category_query = f"""
                SELECT 
                    dc.category_name, 
                    dc.color_code,
                    SUM(d.duration_minutes) as total_minutes
                {base_sql}
                GROUP BY dc.category_name, dc.color_code
                ORDER BY total_minutes DESC
            """
            by_category = conn.execute_query(category_query, params)

            # 3. Downtime by Production Line
            line_query = f"""
                SELECT 
                    pl.line_name,
                    SUM(d.duration_minutes) as total_minutes
                {base_sql}
                GROUP BY pl.line_name
                ORDER BY total_minutes DESC
            """
            by_line = conn.execute_query(line_query, params)
            
            # 4. Raw data for table view
            raw_data_query = f"""
                SELECT TOP 250
                    d.start_time,
                    d.duration_minutes,
                    f.facility_name,
                    pl.line_name,
                    dc.category_name,
                    d.entered_by,
                    d.reason_notes
                {base_sql}
                ORDER BY d.start_time DESC
            """
            raw_data = conn.execute_query(raw_data_query, params)

            # Calculate average
            total_events = overall_stats[0]['total_events'] if overall_stats else 0
            total_minutes = overall_stats[0]['total_minutes'] if overall_stats else 0
            avg_duration = (total_minutes / total_events) if total_events > 0 else 0

            return {
                'overall_stats': {
                    'total_events': total_events,
                    'total_minutes': total_minutes or 0,
                    'avg_duration': round(avg_duration, 1)
                },
                'by_category': by_category,
                'by_line': by_line,
                'raw_data': raw_data
            }

# Singleton instance
reports_db = ReportsDB()