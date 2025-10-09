Of course. It is an excellent idea to bring the project's master document up to date. We have made significant progress, and the `README.md` file should reflect the application's current, powerful capabilities.

I have written a new, comprehensive `README.md` from the ground up. It details every completed module, including the final, interactive **MRP Dashboard**, and provides a clear picture of the project as it stands now.

Here is the complete and updated `README.md` file:

# Production Portal: Downtime Tracker & MRP Scheduler

## Overview

A robust, enterprise-ready web application designed for manufacturing environments. This portal provides a comprehensive suite of tools for **tracking production downtime**, managing **production scheduling**, viewing critical ERP data like **Bills of Materials (BOM)** and **Purchase Orders (PO)**, and leveraging a powerful **Material Requirements Planning (MRP)** dashboard to guide production decisions.

The system's hybrid data architecture connects to a **read-only ERP database** for live production and material data while storing all user-generated data—such as downtime events, scheduling projections, and production capacity—in a separate, fully-controlled local SQL Server database (`ProductionDB`).

**Current Version:** 2.4.0 (MRP Dashboard Implemented)
**Status:** **All core modules are complete and operational.**

-----

## 🚀 Getting Started

### Prerequisites

  * Python 3.10+
  * Microsoft SQL Server
  * Access to an Active Directory domain (for production authentication)

### Installation & Setup

1.  **Clone the Repository:**

    ```bash
    git clone <your-repository-url>
    cd downtime_tracker
    ```

2.  **Set Up Environment Variables:**
    Create a file named `.env` in the root of the project and populate it with your environment-specific configurations. A template of required variables can be found in `config.py`.

3.  **Install Dependencies:**
    It is highly recommended to use a virtual environment.

    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # On Windows
    # source venv/bin/activate  # On macOS/Linux

    pip install -r requirements.txt
    ```

4.  **Run the Application:**
    Execute the main application file. The server will start in debug mode using standard HTTP.

    ```bash
    python app.py
    ```

5.  **Access the URL:**
    Open your browser and navigate to **`http://localhost:5000`** or the network URL provided in the terminal (e.g., `http://192.168.x.x:5000`).

-----

## 🎯 Core Modules

### ✅ Material Requirements Planning (MRP) Dashboard

A dynamic, filterable dashboard that serves as the central planning tool. It analyzes all open sales orders and provides intelligent, data-driven production suggestions.

  * **Filterable Interface:** Instantly narrow down sales orders by **Facility, Business Unit, Customer, and Production Status** (Full, Partial, Critical).
  * **Dynamic Summary Cards:** Get a real-time overview of the filtered data, including the total number of orders and their production feasibility.
  * **Collapsible Accordion View:** Each sales order is presented as a color-coded summary line for at-a-glance status checks. Clicking any order expands it to show a detailed material breakdown.
  * **Bottleneck Identification:** The system automatically highlights the specific raw material that is constraining production for each order.
  * **"Can Produce" Suggestions:** For each order, the dashboard displays the maximum quantity of a finished good that can be produced based on material availability.

### ✅ Downtime Tracking Module

A tablet-optimized interface for quick and easy downtime entry on the factory floor, featuring ERP job integration and a real-time list of the day's entries.

### ✅ Production Scheduling Module

An Excel-like grid that displays open sales orders from the ERP, allowing planners to input and save financial projections for "No/Low Risk" and "High Risk" production scenarios.

### ✅ BOM & PO Viewers

Dedicated, read-only interfaces for viewing and searching **Bills of Materials** and open **Purchase Orders** directly from the ERP, complete with client-side searching and Excel export functionality.

### ✅ Admin Panel & System Management

A comprehensive, role-restricted area for managing all aspects of the application.

  * **Facilities, Lines, Categories, Shifts:** Full CRUD (Create, Read, Update, Deactivate) management for all core data.
  * **Production Capacity:** A dedicated interface to define and manage the output capacity (e.g., units per shift) for each production line. This data is a critical input for the MRP engine.
  * **User Management & Audit Log:** Tools to view user activity and a complete history of all changes made within the system.

-----

## 🏗️ Architecture

### Technology Stack

  * **Backend**: Python, Flask
  * **Database**:
      * **Application DB**: Microsoft SQL Server (via `pyodbc`)
      * **ERP Connection**: Read-only connection to ERP database (via `pyodbc`)
  * **Authentication**: Active Directory (via `ldap3`)
  * **Frontend**: Jinja2, HTML, CSS, JavaScript
  * **Internationalization**: Flask-Babel
  * **Excel Export**: `openpyxl`

### Project Structure (Highlights)

```
/downtime_tracker/
|
├── app.py                  # Main application factory
|
├── /database/
│   ├── erp_connection.py   # Contains all ERP query functions
│   ├── mrp_service.py      # Core MRP calculation engine
│   ├── capacity.py         # Manages ProductionCapacity table
│   └── ...                 # Other database modules
|
├── /routes/
│   ├── mrp.py              # Routes for the MRP Dashboard page
│   ├── scheduling.py       # Routes for the Production Scheduling grid
│   ├── bom.py              # Routes for the BOM Viewer
│   ├── po.py               # Routes for the PO Viewer
│   └── /admin/
│       └── ...             # All administrative routes
|
├── /static/
│   ├── /css/
│   └── /js/
│       └── mrp.js          # JavaScript for the MRP Dashboard
|
├── /templates/
│   ├── dashboard.html
│   └── /mrp/
│       └── index.html      # Main MRP Dashboard page template
|
└── ...
```