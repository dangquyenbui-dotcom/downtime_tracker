

# Downtime Tracker & Production Scheduler

## Overview

A robust, enterprise-ready web application designed for manufacturing environments, providing a comprehensive suite of tools for tracking production downtime, managing production schedules, and analyzing operational data. Built with Flask, this system is optimized for use on factory floor tablets, features seamless integration with Active Directory for secure authentication, and offers a fully bilingual (English/Spanish) user interface.

The application's hybrid data architecture connects to a **read-only ERP database** for live production data (like open sales orders) while storing all user-generated data—such as downtime events, scheduling projections, and audit logs—in a separate, fully-controlled local SQL Server database (`ProductionDB`).

**Current Version:** 1.9.2 (Scheduling Module Enhancement)
**Status:** Production Ready

-----

## 🎯 Core Features

### ✅ Downtime Tracking Module

  * **Tablet-Optimized Interface**: A single-page, responsive form for quick and easy downtime entry on the factory floor.
  * **Hierarchical Categories**: Define and manage multi-level downtime reasons with color-coding for rapid identification.
  * **ERP Job Integration**: Associate downtime events directly with specific production jobs pulled from the ERP system.
  * **Automatic Shift Detection**: The system intelligently identifies and assigns the correct work shift based on the time of entry.
  * **Real-time Entry Listing**: View a live-updating list of the day's downtime entries for the selected production line.

### ✅ Production Scheduling Module

  * **Live ERP Data Grid**: Displays open sales orders from the read-only ERP database in an Excel-like grid, optimized for wide-screen desktop use.
  * **Editable Projections**: Planners can directly input "No/Low Risk Qty" and "High Risk Qty" values into the grid, with changes saved instantly and automatically.
  * **Real-time Financial Calculations**: The grid dynamically updates dollar value columns as new quantities are entered.
  * **Advanced Inventory Valuation**:
      * **FG On Hand Value Cards**: The total value of Finished Goods on-hand inventory is split into two dynamically dated cards based on a monthly 19th-day cutoff, providing a forward-looking financial overview.
      * **Net Quantity Calculation**: The 'Net Qty' column is now calculated as `Ord Qty - Cur. Level` - `On hand Qty` to provide a clear view of immediate production requirements.
  * **Persistent Data Storage**: All planner-entered projections are saved to a dedicated `ScheduleProjections` table in the local `ProductionDB`, ensuring data integrity and separation from the ERP.

### ✅ Reporting & Analytics

  * **Centralized Report Hub**: A scalable `/reports` page for accessing all available system reports.
  * **Downtime Summary Report**: An interactive report with filters for date range, facility, and production line, featuring data visualizations for downtime by category and by line using Chart.js.

### ✅ Comprehensive Admin Panel

  * **Full System Management**: A dedicated administrative area to manage Facilities, Production Lines, Downtime Categories, and Shifts.
  * **User Management**: View user activity, login history, and permissions based on Active Directory group membership.
  * **Audit Log**: A detailed and filterable log that tracks every change made within the system, providing a complete history of all actions.

### ✅ Security & Session Management

  * **Active Directory Authentication**: Secure user login using existing corporate credentials.
  * **Role-Based Access Control**: Differentiates between regular Users and Administrators based on AD group membership, restricting access to sensitive areas.
  * **Single-Session Enforcement**: Prevents a single user from being logged in at multiple locations simultaneously by invalidating old sessions upon a new login.

### ✅ Internationalization (i18n)

  * **Bilingual Interface**: Full, on-the-fly support for US English and US Spanish.
  * **User Preference Persistence**: A user's selected language is saved to their profile and automatically applied across all sessions.

-----

## 🏗️ Architecture

### Technology Stack

  * **Backend**: Python, Flask
  * **Database**:
      * **Application DB**: Microsoft SQL Server (via `pyodbc`) for all user-generated data.
      * **ERP Connection**: Read-only connection to ERP database (via `pyodbc`) with resilient multi-driver support.
  * **Authentication**: Active Directory (via `ldap3`).
  * **Internationalization**: Flask-Babel.
  * **Frontend**: Jinja2, HTML, CSS, JavaScript (with Chart.js).
  * **Excel Export**: `openpyxl` for generating `.xlsx` reports.

### Project Structure

```
downtime_tracker/
├── app.py                      # Main application factory
├── config.py                   # Configuration loader from .env file
├── i18n_config.py              # Internationalization setup
├── requirements.txt            # Python dependencies
├── .env                        # Local environment variables
│
├── auth/                       # Active Directory authentication
│   └── ad_auth.py
│
├── database/                   # Database modules
│   ├── connection.py           # Main application DB connection
│   ├── erp_connection.py       # ERP DB connection (read-only, multi-driver support)
│   ├── scheduling.py           # Combines ERP and local data for scheduling
│   ├── reports.py              # Queries for analytical reports
│   └── ...                     # (modules for each local table: audit, users, etc.)
│
├── routes/                     # Flask blueprints
│   ├── main.py
│   ├── downtime.py
│   ├── scheduling.py
│   ├── reports.py
│   └── admin/                  # Admin panel blueprints
│
├── static/                     # CSS, JavaScript, and image files
│
├── templates/                  # Jinja2 HTML templates
│   ├── admin/
│   ├── components/
│   ├── downtime/
│   ├── reports/
│   ├── scheduling/
│   └── base.html
│
└── translations/               # Language files for i18n
```

-----

## 🚀 Installation & Setup

1.  **Install Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

2.  **Install ODBC Driver**:

      * Ensure a compatible Microsoft ODBC Driver for SQL Server is installed on the host machine. The application will automatically attempt to use a list of common drivers, including versions 17 and 18.

3.  **Configure Environment**:

      * Create a `.env` file in the project's root directory.
      * Populate it with your specific database, ERP, and Active Directory credentials. A `.env.example` file should be created to guide this process.

4.  **Database Setup**:

      * Ensure the main application database (e.g., `ProductionDB`) exists on your SQL Server.
      * The application will automatically create all necessary tables (like `AuditLog`, `ScheduleProjections`, `UserLogins`, etc.) on its first run.

5.  **Run the Application**:

    ```bash
    python app.py
    ```

    The application will be accessible on your local network at `http://<your-ip-address>:5000`.

-----

## 🚧 Continuous Actions & Next Steps

  * **Enhance Scheduling UI**: Add a grand total summary row at the bottom of the grid that updates dynamically with filters.
  * **Build Out OEE Reports**: Develop a new report page to display Overall Equipment Effectiveness (OEE) scores with trend charts.
  * **Downtime Analytics**: Create more in-depth reports, such as Pareto charts for downtime reasons and trend analysis over time.