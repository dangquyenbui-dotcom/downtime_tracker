Of course. Based on all the features and improvements we've implemented, I have completely rewritten the `README.md` file to provide a comprehensive and up-to-date overview of the Production Portal application.

Here is the new content for your `README.md` file:

# Production Portal: Downtime Tracker & MRP Scheduler

## Overview

A robust, enterprise-ready web application designed for manufacturing environments. This portal provides a comprehensive suite of tools for **tracking production downtime**, managing **production scheduling**, viewing critical ERP data like **Bills of Materials (BOM)** and **Purchase Orders (PO)**, and leveraging a powerful **Material Requirements Planning (MRP)** dashboard to guide production decisions.

The system's hybrid data architecture connects to a **read-only ERP database** for live production and material data while storing all user-generated data—such as downtime events, scheduling projections, and production capacity—in a separate, fully-controlled local SQL Server database (`ProductionDB`).

**Current Version:** 2.6.0 (MRP Dashboard Complete with advanced logic)
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

#### Core Logic & Business Rules:

  * **Sequential Allocation by Date:** The MRP engine first sorts all open Sales Orders by their "Due to Ship" date, from earliest to latest. It then processes them one by one, allocating available inventory to the highest-priority orders first.
  * **Finished Goods Allocation:** The system maintains a "live" in-memory inventory of finished goods. As it processes SOs, it depletes this on-hand stock sequentially. An SO is only marked "Ready to Ship" if the live inventory can fully cover its requirement at that moment.
  * **Inventory Availability:** The "Can Produce" calculation for items that require production is based on the sum of three key component inventory figures:
    1.  **Approved, On-Hand Inventory:** The main pool of unrestricted materials.
    2.  **Pending QC Inventory:** Materials that have been received but are awaiting quality inspection. These are included for planning purposes to provide a more realistic view of upcoming availability.
    3.  **Open Purchase Order Quantity:** Materials that are on order but not yet received.
  * **Two-Pass Calculation per Sales Order:** To ensure accuracy for production orders, the engine uses a two-pass system:
    1.  **Pass 1 (Discovery):** It first loops through all required components to find the single greatest constraint (the "bottleneck") and determines the absolute maximum quantity of the finished good that can be produced.
    2.  **Pass 2 (Allocation):** With the true "Can Produce" quantity established, it loops through the components a second time, allocating only the precise amount of each material needed from the "live" component inventory. This prevents over-allocation of non-bottleneck materials and frees them up for lower-priority orders.
  * **Committed Inventory Exclusion:** Inventory that has already been "Issued to Job" is considered Work-in-Progress (WIP) and is **excluded** from all MRP calculations to prevent double-promising materials.

#### Features:

  * **Holistic View:** Displays **all** open sales orders for data consistency and validation against the Scheduling page.
  * **Intelligent Filtering:** Instantly narrow down orders by **Business Unit (BU), Customer, Due to Ship (Month/Year), and Production Status**.
  * **Smart Statuses:**
      * **Ready to Ship:** Orders that can be fulfilled entirely from existing finished goods inventory.
      * **Partial Ship / Pending QC:** Orders that can be partially fulfilled from on-hand stock, with the remainder covered by stock that is pending quality control.
      * **Pending QC:** Orders that cannot be shipped from on-hand stock but can be fully covered by stock that is pending quality control.
      * **Full Production / Partial / Critical:** Statuses determined by comparing the "Can Produce" quantity against the required amount for production.
  * **Enhanced Tooltips:** Hovering over the 🔗 icon next to a component reveals a detailed tooltip showing the **total quantity allocated to prior orders** and a line-by-line breakdown of which specific Sales Orders consumed that inventory.
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