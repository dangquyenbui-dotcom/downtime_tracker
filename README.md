Of course. It is an excellent idea to bring the project's master document up to date. We have made significant progress, and the `README.md` file should reflect the application's current, powerful capabilities.

I have written a new, comprehensive `README.md` from the ground up. It details every completed module, including the final, interactive **MRP Dashboard**, and provides a clear picture of the project as it stands now.

Here is the complete and updated `README.md` file:

# Production Portal: Downtime Tracker & MRP Scheduler

## Overview

A robust, enterprise-ready web application designed for manufacturing environments. This portal provides a comprehensive suite of tools for **tracking production downtime**, managing **production scheduling**, viewing critical ERP data like **Bills of Materials (BOM)** and **Purchase Orders (PO)**, and leveraging a powerful **Material Requirements Planning (MRP)** dashboard to guide production decisions.

The system's hybrid data architecture connects to a **read-only ERP database** for live production and material data while storing all user-generated data—such as downtime events, scheduling projections, and production capacity—in a separate, fully-controlled local SQL Server database (`ProductionDB`).

**Current Version:** 2.5.0 (MRP Dashboard Complete)
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
    cd production_portal_dev
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

A dynamic, filterable dashboard that serves as the central planning tool. It analyzes all open sales orders, provides intelligent production suggestions based on material availability, and prioritizes orders by their "Due to Ship" date.

  * **Holistic View:** Displays **all** open sales orders for data consistency and validation against the Scheduling page.
  * **Intelligent Filtering:** Instantly narrow down orders by **Business Unit (BU), Customer, Due to Ship (Month/Year), and Production Status** (Full Production, Partial, Critical, Ready to Ship).
  * **Prioritized Allocation:** The MRP engine processes orders chronologically by their "Due to Ship" date, allocating scarce materials to the most urgent orders first.
  * **Smart Statuses:**
      * **Ready to Ship:** Orders that can be fulfilled entirely from existing finished goods inventory are clearly marked and do not have an expandable detail view, simplifying the interface.
      * **Full Production / Partial / Critical:** Statuses are determined by comparing the "Can Produce" quantity against the required amount.
  * **Shared Component Identification:** A 🔗 icon and detailed tooltip automatically appear next to any raw material that is required by more than one open sales order, instantly highlighting potential cross-order conflicts.
  * **Live Inventory Simulation:** The component detail view shows the inventory available *before* the current order's demand was considered and shows the exact amount `Allocated`, providing a clear picture of how the live inventory pool is being depleted.
  * **Excel Export:** Download the currently filtered and sorted view of the MRP data, including all component details, to an XLSX file.

### ✅ Production Scheduling Module

An Excel-like grid that displays all open sales orders from the ERP, allowing planners to input and save financial projections for different risk scenarios.

### ✅ Downtime Tracking Module

A tablet-optimized interface for quick and easy downtime entry on the factory floor, featuring ERP job integration and a real-time list of the day's entries.

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
/production_portal_dev/
|
├── app.py                  # Main application factory
|
├── /database/
│   ├── erp_connection.py   # Handles read-only connection to the ERP
│   ├── erp_service.py      # Contains all ERP query functions
│   ├── mrp_service.py      # Core MRP calculation engine
│   ├── capacity.py         # Manages ProductionCapacity table
│   └── ...                 # Other local database modules (downtimes, users, etc.)
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
│       ├── mrp.js          # JavaScript for the MRP Dashboard
│       └── scheduling.js   # JavaScript for the Scheduling page
|
├── /templates/
│   ├── dashboard.html
│   └── /mrp/
│       └── index.html      # Main MRP Dashboard page template
|
└── ...
```