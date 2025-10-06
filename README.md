# Downtime Tracker & Production Scheduler

## Overview

A robust, enterprise-ready web application designed for manufacturing environments, providing a comprehensive suite of tools for tracking production downtime, managing production schedules, and analyzing operational data. Built with Flask, this system is optimized for use on factory floor tablets, features seamless integration with Active Directory for secure authentication, and offers a fully bilingual (English/Spanish) user interface.

The application's hybrid data architecture connects to a **read-only ERP database** for live production data (like open sales orders) while storing all user-generated data—such as downtime events, scheduling projections, and audit logs—in a separate, fully-controlled local SQL Server database (`ProductionDB`).

**Current Version:** 1.9.4 (Granular Security Update)
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
  * **Granular Role-Based Access**:
      * **Scheduling Admins** (`Scheduling_Admin` group) have full access to view and edit scheduling projections.
      * **Scheduling Users** (`Scheduling_User` group) have read-only access to the scheduling grid.
  * **Editable Projections**: Planners can directly input "No/Low Risk Qty" and "High Risk Qty" values into the grid, with changes saved instantly and automatically.
  * **Real-time Financial Calculations**: The grid dynamically updates dollar value columns as new quantities are entered.
  * **Advanced Financial Summaries**:
      * **Multi-Period Inventory Valuation**: The total value of Finished Goods inventory is split into three dynamic, time-sensitive cards.
      * **Current Month Shipping Value**: A summary card displays the total dollar value of all products shipped in the current calendar month.
      * **Shipment Forecasting**: Two dedicated cards provide dynamic forecasts for likely and potential shipment values based on current data.
  * **Persistent Data Storage**: All planner-entered projections are saved to a dedicated `ScheduleProjections` table in the local `ProductionDB`, ensuring data integrity and separation from the ERP.
  * **Customizable View**: Users can show or hide columns to customize their grid view, with preferences saved locally.

### ✅ Reporting & Analytics

  * **Centralized Report Hub**: A scalable `/reports` page for accessing all available system reports.
  * **Downtime Summary Report**: An interactive report with filters for date range, facility, and production line, featuring data visualizations for downtime by category and by line using Chart.js.

### ✅ Comprehensive Admin Panel

  * **Full System Management**: A dedicated administrative area to manage Facilities, Production Lines, Downtime Categories, and Shifts.
  * **User Management**: View user activity, login history, and permissions based on Active Directory group membership.
  * **Audit Log**: A detailed and filterable log that tracks every change made within the system, providing a complete history of all actions.

### ✅ Security & Session Management

  * **Active Directory Authentication**: Secure user login using existing corporate credentials.
  * **Granular Role-Based Access**: Differentiates between four distinct roles, restricting access to sensitive areas:
      * `DowntimeTracker_Admin`: Full administrative access to all modules.
      * `DowntimeTracker_User`: Can only access the "Report Downtime" page.
      * `Scheduling_Admin`: Can view and edit the "Scheduling" page.
      * `Scheduling_User`: Can only view the "Scheduling" page (read-only).
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