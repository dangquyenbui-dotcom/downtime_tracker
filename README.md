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

# Production Portal v2.1.0

The Production Portal is a comprehensive, web-based application designed to streamline and manage various aspects of a manufacturing environment. It provides real-time data, enhances visibility into production processes, and offers tools for planning, tracking, and reporting.

## About The Project

This portal serves as a centralized hub for production-related activities, integrating with the company's ERP system to provide up-to-date information. It is built with a focus on usability, accessibility, and data accuracy, empowering both shop floor operators and administrative staff.

### Key Technologies

* **Backend:** Python (Flask)
* **Frontend:** HTML, CSS, JavaScript
* **Database:** Microsoft SQL Server
* **Authentication:** Active Directory integration
* **Internationalization:** Flask-Babel for multi-language support (English & Spanish)

## Features

* **Role-Based Access Control:** Granular permissions for different user groups (Admin, User, Scheduling Admin, Scheduling User).
* **ERP Integration:** Real-time data synchronization with the ERP system for modules like BOM, PO, and MRP.
* **Internationalization:** Support for English and Spanish languages, with a user-friendly language selector.
* **Responsive UI:** A modern and responsive user interface that works on both desktop and mobile devices.
* **Dark Mode:** A theme-switcher for a personalized user experience.

## Modules

The Production Portal is composed of several modules, each designed to address a specific area of the production process:

### 1. Downtime Tracking

* **Purpose:** To record and analyze unplanned downtime events on the production floor.
* **Key Features:**
    * Simple and intuitive form for reporting downtime.
    * Real-time updates to the database.
    * Categorization of downtime reasons for better analysis.
* **Access:** Administrators and standard users.

### 2. Scheduling

* **Purpose:** To plan and visualize the production schedule based on open sales orders.
* **Key Features:**
    * Interactive calendar view of the production schedule.
    * Drag-and-drop interface for rescheduling production runs.
    * Capacity planning based on production line output.
* **Access:** Administrators and Scheduling users.

### 3. Bill of Materials (BOM) Viewer

* **Purpose:** To provide a read-only view of the Bill of Materials for all finished goods.
* **Key Features:**
    * Search and filter functionality to easily find BOMs.
    * Detailed view of all components, quantities, and units of measure.
    * Real-time data from the ERP system.
* **Access:** Administrators and Scheduling users.

### 4. Purchase Order (PO) Viewer

* **Purpose:** To view the status and details of open purchase orders for raw materials.
* **Key Features:**
    * Comprehensive list of all open POs.
    * Detailed view of each PO, including vendor, expected delivery date, and line items.
    * Live data from the ERP system.
* **Access:** Administrators and Scheduling users.

### 5. Material Requirements Planning (MRP)

* **Purpose:** To provide intelligent suggestions for production based on material availability.
* **Key Features:**
    * Analyzes open sales orders against current inventory and open POs.
    * Identifies potential material shortages and production bottlenecks.
    * Prioritizes production based on "Due to Ship" dates.
    * Color-coded status indicators for at-a-glance understanding.
* **Access:** Administrators and Scheduling users.

### 6. Admin Panel

* **Purpose:** To manage the core settings and data of the application.
* **Key Features:**
    * **Facilities Management:** Add, edit, and manage production facilities.
    * **Production Lines:** Configure and manage production lines within each facility.
    * **Downtime Categories:** Define the reasons for production downtime.
    * **Shifts:** Manage production shifts and schedules.
    * **Production Capacity:** Set the expected output per shift for each production line.
    * **User Management:** View all users and their access levels.
    * **Audit Log:** Track all significant changes made within the application.
* **Access:** Administrators only.

## Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

* Python 3.10+
* Pip (Python package installer)
* Access to the SQL Server database
* Access to the Active Directory domain

### Installation

1.  **Clone the repo**
    ```sh
    git clone [https://your-repo-url.com/production-portal.git](https://your-repo-url.com/production-portal.git)
    cd production-portal
    ```
2.  **Create a virtual environment**
    ```sh
    python -m venv venv
    ```
3.  **Activate the virtual environment**
    * **Windows:**
        ```sh
        .\venv\Scripts\activate
        ```
    * **macOS/Linux:**
        ```sh
        source venv/bin/activate
        ```
4.  **Install Python packages**
    ```sh
    pip install -r requirements.txt
    ```

### Configuration

All configuration is managed in the `config.py` file. You will need to set the following variables:

* **Database Credentials:**
    * `DB_SERVER`
    * `DB_NAME`
    * `DB_USER`
    * `DB_PASSWORD`
* **Active Directory Settings:**
    * `AD_DOMAIN`
    * `AD_SERVER`
    * `AD_ADMIN_GROUP`
    * `AD_USER_GROUP`
    * `AD_SCHEDULING_ADMIN_GROUP`
    * `AD_SCHEDULING_USER_GROUP`
* **Application Settings:**
    * `SECRET_KEY`: A strong, randomly generated secret key.
    * `SESSION_HOURS`: The number of hours a user session should remain active.
    * `TEST_MODE`: Set to `True` to bypass Active Directory authentication for local development.

### Running the Application

Once the installation and configuration are complete, you can run the application with the following command:

```sh
python app.py
```

The application will be accessible at `http://localhost:5000`.

## Internationalization (i18n)

The application uses `Flask-Babel` to provide support for multiple languages.

### Adding a New Language

1.  **Extract translatable strings:**
    ```sh
    pybabel extract -F babel.cfg -o messages.pot .
    ```
2.  **Create a new language catalog:** (e.g., for French)
    ```sh
    pybabel init -i messages.pot -d translations -l fr
    ```
3.  **Translate the strings** in the newly created `.po` file (`translations/fr/LC_MESSAGES/messages.po`).
4.  **Compile the translations:**
    ```sh
    pybabel compile -d translations
    ```

### Updating Translations

1.  **Extract the latest strings:**
    ```sh
    pybabel extract -F babel.cfg -o messages.pot .
    ```
2.  **Update the language catalogs:**
    ```sh
    pybabel update -i messages.pot -d translations
    ```
3.  **Translate any new strings** in the `.po` files.
4.  **Compile the updated translations:**
    ```sh
    pybabel compile -d translations
    ```