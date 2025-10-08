Of course. I have rewritten the `README.md` file to be more comprehensive and to reflect all the latest updates to the application, including the UI enhancements and the detailed file structure you requested.

Here is the updated `README.md`:

# Downtime Tracker & Production Scheduler

## Overview

A robust, enterprise-ready web application designed for manufacturing environments, providing a comprehensive suite of tools for tracking production downtime, managing production schedules, and analyzing operational data. Built with Flask, this system is optimized for use on factory floor tablets, features seamless integration with Active Directory for secure authentication, and offers a fully bilingual (English/Spanish) user interface.

The application's hybrid data architecture connects to a **read-only ERP database** for live production data (like open sales orders) while storing all user-generated data—such as downtime events, scheduling projections, and audit logs—in a separate, fully-controlled local SQL Server database (`ProductionDB`).

**Current Version:** 1.9.5 (UI & Calculation Enhancements)
**Status:** Production Ready

-----

## 🎯 Core Features

### ✅ Downtime Tracking Module

  * **Tablet-Optimized Interface**: A refactored and streamlined single-page form for quick and easy downtime entry on the factory floor, with separated CSS and JavaScript for better performance and maintainability.
  * **Hierarchical Categories**: Define and manage multi-level downtime reasons with color-coding for rapid identification.
  * **ERP Job Integration**: Associate downtime events directly with specific production jobs pulled from the ERP system.
  * **Automatic Shift Detection**: The system intelligently identifies and assigns the correct work shift based on the time of entry.
  * **Real-time Entry Listing**: View a live-updating list of the day's downtime entries for the selected production line.

### ✅ Production Scheduling Module

  * **Live ERP Data Grid**: Displays open sales orders from the read-only ERP database in an Excel-like grid, optimized for wide-screen desktop use.
  * **Granular Role-Based Access**:
      * **Scheduling Admins** (`Scheduling_Admin` group) have full access to view and edit scheduling projections.
      * **Scheduling Users** (`Scheduling_User` group) have read-only access to the scheduling grid.
  * **Editable Projections**: Planners can directly input "No/Low Risk Qty" and "High Risk Qty" values into the grid, with changes saved instantly and automatically.
  * **Real-time Financial Calculations**: The grid dynamically updates dollar value columns as new quantities are entered.
  * **Advanced Financial Summaries**:
      * **Multi-Period Inventory Valuation**: The total value of Finished Goods inventory is split into three dynamic, time-sensitive cards with descriptive date-based labels.
      * **Current Month Shipping Value**: A summary card displays the total dollar value of all products shipped in the current calendar month.
      * **Forecasting Cards**: Summary cards provide "Likely" and "May Be" shipment forecasts based on real-time data.
  * **Intelligent "Fix" Suggestions**: A color-coded "Fix" button appears next to editable quantities, turning red for shortfalls and yellow for surpluses, allowing for one-click correction.
  * **Persistent Data Storage**: All planner-entered projections are saved to a dedicated `ScheduleProjections` table in the local `ProductionDB`, ensuring data integrity and separation from the ERP.
  * **Customizable View**: Users can show or hide columns to customize their grid view, with preferences saved locally.
  * **Excel Export**: Download the currently visible grid data as a formatted `.xlsx` file.

### ✅ Reporting & Analytics

  * **Centralized Report Hub**: A scalable `/reports` page for accessing all available system reports.
  * **Downtime Summary Report**: An interactive report with filters for date range, facility, and production line, featuring data visualizations for downtime by category and by line using Chart.js.

### ✅ Comprehensive Admin Panel

  * **Full System Management**: A dedicated administrative area to manage Facilities, Production Lines, Downtime Categories, and Shifts.
  * **User Management**: View user activity, login history, and permissions based on Active Directory group membership.
  * **Audit Log**: A detailed and filterable log that tracks every change made within the system, providing a complete history of all actions.

### ✅ Branding & Theming

  * **Custom Company Branding**: The company logo is integrated throughout the application, including the main navigation and login page.
  * **Automatic Theme Switching**: The logo automatically switches between light and dark versions to match the selected UI theme.

### ✅ Security & Session Management

  * **Active Directory Authentication**: Secure user login using existing corporate credentials.
  * **Granular Role-Based Access**: Differentiates between four distinct roles, restricting access to sensitive areas:
      * `DowntimeTracker_Admin`: Full administrative access to all modules.
      * `DowntimeTracker_User`: Can only access the "Report Downtime" page.
      * `Scheduling_Admin`: Can view and edit the "Scheduling" page.
      * `Scheduling_User`: Can only view the "Scheduling" page (read-only).
  * **Single-Session Enforcement**: Prevents a single user from being logged in at multiple locations simultaneously by invalidating old sessions upon a new login.

### ✅ Internationalization (i18n)

  * **Bilingual Interface**: Full, on-the-fly support for US English and US Spanish, managed via Flask-Babel.
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

### Folder & File Structure

The project follows a modular structure to separate concerns into distinct blueprints and directories:

```
/downtime_tracker/
|
├── app.py                  # Main application factory and entry point
├── config.py               # Central configuration from environment variables
├── requirements.txt        # Python package dependencies
├── README.md               # Project documentation (this file)
|
├── /auth/                  # Handles authentication and authorization
│   ├── ad_auth.py          # Active Directory authentication logic
│   └── __init__.py         # Package initializer
|
├── /database/              # Data access layer for all database interactions
│   ├── connection.py       # Main application database connection (ProductionDB)
│   ├── erp_connection.py   # Read-only ERP database connection
│   ├── audit.py            # Logic for the AuditLog table
│   ├── categories.py       # Logic for DowntimeCategories table
│   ├── facilities.py       # Logic for Facilities table
│   ├── production_lines.py # Logic for ProductionLines table
│   ├── scheduling.py       # Logic for ScheduleProjections table
│   ├── sessions.py         # Logic for ActiveSessions table
│   ├── shifts.py           # Logic for Shifts table
│   ├── users.py            # Logic for UserLogins & UserPreferences tables
│   ├── reports.py          # Queries for generating reports
│   └── __init__.py         # Initializes and exports all DB modules
|
├── /routes/                # Flask blueprints for different application sections
│   ├── main.py             # Core routes (login, dashboard, logout)
│   ├── downtime.py         # Routes for the downtime entry module
│   ├── scheduling.py       # Routes for the production scheduling module
│   ├── reports.py          # Routes for the reporting hub and specific reports
│   ├── erp_routes.py       # API routes for fetching data from the ERP
│   └── /admin/             # Blueprint package for all admin panel routes
│       ├── panel.py        # Main admin panel dashboard
│       ├── facilities.py   # Routes for facility management
│       ├── production_lines.py # Routes for line management
│       ├── categories.py   # Routes for category management
│       ├── shifts.py       # Routes for shift management
│       ├── users.py        # Routes for user management
│       └── audit.py        # Routes for viewing the audit log
|
├── /static/                # Frontend assets
│   ├── /css/               # Stylesheets
│   │   ├── base.css        # Core application styles
│   │   ├── admin.css       # Styles for the admin panel
│   │   └── downtime.css    # Styles for the downtime entry page
│   ├── /js/                # JavaScript files
│   │   ├── common.js       # Shared utility functions (modals, alerts)
│   │   ├── downtime.js     # Logic for the downtime entry page
│   │   ├── scheduling.js   # Logic for the scheduling grid
│   │   └── theme.js        # Light/dark mode theme management
│   └── /img/               # Image assets
│       ├── wepackitall-logo-final-rgb-web.jpg
│       └── wepackitall-logo-final-rgb-reversed-web.png
|
├── /templates/             # Jinja2 HTML templates
│   ├── base.html           # Main application layout template
│   ├── login.html          # Standalone login page
│   ├── dashboard.html      # Main user dashboard
│   ├── /admin/             # Templates for the admin panel
│   ├── /downtime/          # Templates for the downtime module
│   ├── /scheduling/        # Templates for the scheduling module
│   └── /reports/           # Templates for the reporting module
|
├── /translations/          # Internationalization (i18n) files
│   ├── babel.cfg           # Babel configuration
│   ├── messages.pot        # Template for new translations
│   ├── /en/LC_MESSAGES/    # English language files
│   └── /es/LC_MESSAGES/    # Spanish language files
|
└── /utils/                 # Shared helper functions and validators
    ├── helpers.py          # General utility functions
    ├── validators.py       # Input validation functions
    └── __init__.py         # Package initializer
```