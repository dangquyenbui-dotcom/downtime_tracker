Of course. It's an excellent idea to keep the `README.md` file current with the project's progress. Based on the successful implementation of the editable and persistent scheduling grid, I have updated the documentation to reflect its new capabilities.

Here is the new `README.md` file content for your project.

-----

# Downtime Tracker v1.9.0

## Overview

A robust, production-ready downtime tracking and production scheduling system built with Flask. This application is designed for factory floor use, optimized for tablet interfaces, and features seamless integration with Active Directory for authentication. It provides a bilingual interface (English/Spanish), enforces a single-session-per-user policy, and includes a scalable reporting and production scheduling module.

The system's architecture is designed for a hybrid data environment. It connects to a **read-only ERP database** for live, high-volume data (like open sales orders) and stores all user-generated data—such as downtime events and scheduling projections—in a separate, fully-controlled local SQL Server database (`ProductionDB`).

**Current Version:** 1.9.0 (Production Scheduling Module - Editable Grid)
**Status:** Production Ready

-----

## 🎯 Core Features

### ✅ Production Scheduling Module

  * **Live ERP Data Grid**: Displays all open sales orders from the read-only ERP database in an Excel-like grid that is optimized for desktop and can be scrolled horizontally.
  * **Editable Projections**: Planners can directly input "No/Low Risk Qty" and "High Risk Qty" values into the grid. Changes are saved instantly and automatically.
  * **Real-time Financial Calculations**: The corresponding dollar value columns (`$ No/Low Risk Qty`, `$ High Risk`) update immediately on the front-end as quantities are entered.
  * **Dynamic Filtering**: A client-side filter bar allows for instant filtering by Facility, SO Type, Customer, and "Due to Ship" month without page reloads.
  * **Dynamic Summary Totals**: Summary cards at the top of the page display real-time totals for key financial metrics, which update automatically as filters are applied.
  * **Persistent Data Storage**: All planner-entered projections are saved to a dedicated `ScheduleProjections` table in the local `ProductionDB`, ensuring data integrity and separation from the read-only ERP.
  * **Data Refresh**: A "Refresh Data" button allows the user to pull the latest data from the ERP on demand, with a "Last Updated" timestamp for clarity.

### ✅ Downtime Tracking

  * iPad-optimized, single-page entry form for ease of use on the factory floor.
  * Hierarchical downtime categories with color-coding for quick identification.
  * Auto-detection of the current work shift based on the time of entry.

### ✅ Reporting & Analytics

  * **Report Hub**: A central `/reports` page that lists all available reports, designed for future scalability.
  * **Downtime Summary Report**: An initial report with filters for date range, facility, and production line.
  * **Data Visualization**: Interactive doughnut and bar charts (via Chart.js) to visualize downtime by category and by production line.

### ✅ Security & Session Management

  * **Active Directory Authentication**: Secure user login using existing company credentials.
  * **Role-Based Access**: Differentiates between regular Users and Administrators based on AD group membership.
  * **Single-Session Enforcement**: Prevents a user from being logged in at more than one location simultaneously.

### ✅ Internationalization (i18n)

  * **Bilingual Interface**: Full support for US English and US Spanish, switchable on-the-fly.
  * **User Preference**: A user's selected language is saved to their profile and persists across sessions.

-----

## 🏗️ Architecture

### Technology Stack

  * **Backend**: Python, Flask, Waitress
  * **Database**: Microsoft SQL Server (via `pyodbc`) for local application data.
  * **ERP Connection**: Read-only connection to ERP database (Deacom) via `pyodbc`.
  * **Authentication**: Active Directory (via `ldap3`).
  * **Internationalization**: Flask-Babel.
  * **Frontend**: Jinja2, HTML, CSS, JavaScript (with Chart.js).

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
│
├── database/                   # Database modules
│   ├── connection.py           # Main DB connection
│   ├── erp_connection.py       # ERP DB connection (read-only)
│   ├── scheduling.py           # Combines ERP and local data
│   ├── reports.py              # Queries for analytical reports
│   └── ...                     # (modules for each table)
│
├── routes/                     # Flask blueprints
│   ├── main.py
│   ├── downtime.py
│   ├── erp_routes.py
│   ├── reports.py
│   ├── scheduling.py           # Routes for the scheduling module
│   └── admin/                  # Admin panel routes
│
├── static/                     # CSS and JavaScript files
│
├── templates/                  # Jinja2 HTML templates
│   ├── admin/
│   ├── components/
│   ├── downtime/
│   ├── reports/
│   ├── scheduling/             # Templates for scheduling
│   └── base.html
│
└── translations/               # Language files for i18n
```

-----

## 📊 Database Schema

#### New Table: `ScheduleProjections` (in Local `ProductionDB`)

This table is the writeable layer for the scheduling module. It stores the planner's manual inputs, cleanly separating them from the source ERP data.

```sql
CREATE TABLE [dbo].[ScheduleProjections](
	[projection_id] [int] IDENTITY(1,1) NOT NULL PRIMARY KEY,
	[so_number] [nvarchar](50) NOT NULL,
	[part_number] [nvarchar](100) NOT NULL,
	[can_make_no_risk] [decimal](18, 2) NULL,
	[low_risk] [decimal](18, 2) NULL,
	[high_risk] [decimal](18, 2) NULL,
	[updated_by] [nvarchar](100) NULL,
	[updated_date] [datetime] NULL,
    CONSTRAINT UQ_ScheduleProjection UNIQUE (so_number, part_number)
);
```

-----

## 🚀 Installation & Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Configure Environment**:
      * Create a `.env` file in the project root.
      * Populate it with your specific database, ERP, and Active Directory credentials.
3.  **Database Setup**:
      * Ensure the main application database (`ProductionDB`) exists on your local SQL Server.
      * The application will automatically create most tables on first run.
      * **Important**: You must manually run the `CREATE TABLE [dbo].[ScheduleProjections]` script to add the new table for the scheduling feature.
4.  **Run the Application**:
    ```bash
    python app.py
    ```

-----

## 🚧 Continuous Actions & Next Steps

  * **Enhance Scheduling UI**:
      * Add a grand total summary row at the bottom of the grid that also updates dynamically with the filters.
      * Consider adding visual cues for rows where the planner's projection differs from the original ERP data.
  * **Build Out OEE Reports**:
      * Create the necessary SQL queries to fetch production counts and scrap data from the ERP.
      * Develop a new report page to display the OEE (Availability, Performance, Quality) scores with trend charts.