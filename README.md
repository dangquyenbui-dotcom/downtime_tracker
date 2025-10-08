Of course. It is an excellent idea to update the project's master document to reflect all of our progress and solidify the plan for the final implementation phase. We have successfully gathered all the required data, and the next steps are now purely developmental.

I have written a new, highly detailed `README.md` file from the ground up. It documents every module we have built, including the new **Production Capacity** admin page, and clearly outlines the upcoming development work to create the final MRP engine and user interface.

Here is the complete and updated `README.md` file:

# Production Portal: Downtime Tracker & MRP Scheduler

## Overview

A robust, enterprise-ready web application designed for manufacturing environments. This portal provides a comprehensive suite of tools for **tracking production downtime**, **viewing Bills of Materials (BOM)**, viewing **Purchase Orders (PO)**, and a forthcoming **Material Requirements Planning (MRP)** module to guide production scheduling.

The system's hybrid data architecture connects to a **read-only ERP database** for live production and material data while storing all user-generated data—such as downtime events, scheduling projections, and production capacity—in a separate, fully-controlled local SQL Server database (`ProductionDB`).

**Current Version:** 2.3.0 (MRP Engine Development Phase)
**Status:** **All data gathering is complete. Ready for final MRP implementation.**

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
    Create a file named `.env` in the root of the project and populate it with your environment-specific configurations. A template can be found in `config.py`.

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

### ✅ Downtime Tracking Module

A tablet-optimized interface for quick and easy downtime entry on the factory floor, featuring ERP job integration and real-time entry listing.

### ✅ Production Scheduling Module

An Excel-like grid that displays open sales orders from the ERP, allowing planners to input and save financial projections.

### ✅ BOM Viewer Module

A dedicated, read-only interface for viewing and searching Bill of Materials data directly from the ERP, complete with client-side searching and Excel export functionality.

### ✅ Purchase Order (PO) Viewer Module

A dedicated, read-only interface for viewing and searching open and recently received Purchase Orders directly from the ERP, complete with client-side searching and Excel export functionality.

### ✅ Admin Panel & System Management

A comprehensive, role-restricted area for managing all aspects of the application.

  * **Facilities, Lines, Categories, Shifts:** Full CRUD (Create, Read, Update, Deactivate) management for all core data.
  * **Production Capacity (New\!):** A dedicated interface to define and manage the output capacity (e.g., units per shift) for each production line. This data is stored locally and is a critical input for the MRP engine.
  * **User Management & Audit Log:** Tools to view user activity and a complete history of all changes made within the system.

### 💡 MRP / Planning Module (Next To Be Developed)

This will be a **brand new, dedicated page** that serves as the core of the planning system. It will analyze sales orders and provide intelligent suggestions for production.

  * **Material Availability Calculation**: For every required component, the engine will calculate an **"Available for Production"** quantity by combining QC-approved on-hand inventory with incoming purchase orders.
  * **Bottleneck Identification**: The system will automatically pinpoint the specific raw material that is constraining the production of each sales order.
  * **"Can Produce" Suggestions**: The page will display the maximum quantity of a finished good that can be produced based on the identified material bottleneck.
  * **Capacity Planning**: The system will use the newly-defined production line capacities to estimate the number of shifts required to produce the suggested quantity.

-----

## 📋 MRP Implementation Plan & Action Items

This section outlines the development plan now that all necessary data sources and management tools are in place.

### Phase 1: Bill of Materials (BOM) Data - ✔️ **Complete**

  * **Status:** You have provided the comprehensive SQL query for BOMs.
  * **Result:** A fully functional **BOM Viewer** page exists at `/bom`.

### Phase 2: Purchase Order (PO) Data - ✔️ **Complete**

  * **Status:** You have provided the comprehensive SQL query for Purchase Orders.
  * **Result:** A fully functional **PO Viewer** page exists at `/po`.

### Phase 3: Inventory & Supply Data - ✔️ **Complete**

  * **Status:** You have provided the crucial query for identifying inventory with a `QC = 'Pending'` status, which allows us to determine true material availability.
  * **Result:** The logic for handling QC status and calculating available inventory is ready for implementation in the MRP engine.

### Phase 4: Production Capacity Data - ✔️ **Complete**

  * **Status:** You have provided the capacity data for key production lines.
  * **Result:** A new **Production Capacity Management** page has been created at `/admin/capacity`. This allows you to enter, view, and manage the capacity for every production line in the local database.

### Phase 5: MRP Engine Development - actionable **Action Item (For Me)**

  * **Objective:** With all data sources and management tools now complete, the next step is for me to build the core MRP logic and the new user interface.
  * **My Action Plan:**
    1.  **Develop the `MRPService`:** I will create the final backend service (`database/mrp_service.py`) that:
          * Takes a Sales Order as input.
          * Uses the `get_bom_data` function to find all required components.
          * For each component, calculates the **"Available for Production"** quantity using the formula: `(TotalOnHand - QCPending) + OpenPOQuantity`.
          * Identifies the single component that is the bottleneck (the "limiting factor").
          * Calculates the maximum number of finished goods that can be produced based on that bottleneck.
          * Uses the stored **Production Capacity** data to estimate the number of shifts required.
    2.  **Build the New MRP Page:**
          * Create a new route (`/mrp`) and a corresponding template (`templates/mrp/index.html`).
          * This page will display the results from the MRP engine in a clear, hierarchical table: for each Sales Order, it will show the suggested production quantity, the limiting factor, and the estimated shifts required.

### Phase 6: Business Logic Integration - (Future Discussion)

  * **Objective:** After the core engine is built, we will refine the suggestions based on your specific operational rules.
  * **Future Topics for Discussion:**
      * **Scheduling Priority:** How should the system rank orders when materials are scarce? (e.g., based on the "Due to Ship" date).
      * **Inventory Allocation:** Does your ERP "reserve" inventory for certain orders?
      * **Safety Stock:** Do you maintain minimum stock levels that the MRP system should not touch?

-----

## 🏗️ Architecture (Updated)

### Technology Stack

  * **Backend**: Python, Flask
  * **Database**:
      * **Application DB**: Microsoft SQL Server (via `pyodbc`)
      * **ERP Connection**: Read-only connection to ERP database (via `pyodbc`)
  * **Authentication**: Active Directory (via `ldap3`)
  * **Frontend**: Jinja2, HTML, CSS, JavaScript
  * **Excel Export**: `openpyxl`

### Project Structure (Highlights)

```
/downtime_tracker/
|
├── app.py
|
├── /database/
│   ├── erp_connection.py   # Contains all ERP query functions
│   ├── capacity.py         # [NEW] Manages ProductionCapacity table
│   └── mrp_service.py      # [PLANNED] Will contain the MRP calculation logic
|
├── /routes/
│   ├── bom.py
│   ├── po.py
│   ├── mrp.py              # [PLANNED] Routes for the new MRP page
│   └── /admin/
│       └── capacity.py     # [NEW] Routes for the Capacity Management page
|
├── /static/
│   └── /js/
│       ├── bom.js
│       ├── po.js
│       └── mrp.js          # [PLANNED] JavaScript for the new MRP page
|
├── /templates/
│   ├── dashboard.html      # Updated with links to BOM and PO Viewers
│   ├── /admin/
│   │   └── capacity.html   # [NEW] Capacity Management page
│   ├── /bom/
│   ├── /po/
│   └── /mrp/
│       └── index.html      # [PLANNED] Main MRP results page
|
└── ...
```