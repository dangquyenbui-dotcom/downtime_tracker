# Audit Logging System - Setup & Troubleshooting Guide

## 📋 Overview
The Downtime Tracker includes comprehensive audit logging that tracks all changes to:
- Facilities (create, update, deactivate)
- Production Lines (create, update, deactivate)
- Future: Downtime entries, categories, shifts, etc.

## 🚀 Quick Setup

### 1. Initialize the AuditLog Table
```bash
python init_audit_table.py
```

This will:
- Create the AuditLog table if it doesn't exist
- Add proper indexes for performance
- Insert a test entry to verify it's working

### 2. Test Audit Logging
```bash
python test_audit_logging.py
```

This will:
- Create test audit entries
- Verify the logging mechanism works
- Display recent audit logs

### 3. Verify in the Application
1. Start the application: `python app.py`
2. Login as an admin user
3. Go to Admin Panel → Facilities
4. Create or edit a facility
5. Go to Admin Panel → Audit Log
6. You should see your changes recorded

## 🔍 Troubleshooting

### Problem: No audit logs appearing

**Check 1: AuditLog Table Exists**
```sql
-- Run in SQL Server Management Studio
USE ProductionDB;
SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'AuditLog';
```

If the table doesn't exist, run:
```bash
python init_audit_table.py
```

**Check 2: Database Commits**
The fixed `database.py` now includes `self.connection.commit()` in the `log_audit()` method. If you're still using the old version, update it.

**Check 3: View Raw Data**
```sql
-- Check if ANY audit logs exist
SELECT TOP 10 * FROM AuditLog ORDER BY changed_date DESC;
```

**Check 4: Console Output**
When you create/edit a facility, you should see console output like:
```
✅ Audit logged: INSERT on Facilities ID 1 by admin_user
```

If you see error messages instead:
```
❌ Audit logging failed: [error message]
```

### Problem: "AuditLog table doesn't exist" error

Run the initialization script:
```bash
python init_audit_table.py
```

Or create manually in SQL:
```sql
CREATE TABLE AuditLog (
    audit_id INT IDENTITY(1,1) PRIMARY KEY,
    table_name NVARCHAR(100) NOT NULL,
    record_id INT,
    action_type NVARCHAR(50) NOT NULL,
    field_name NVARCHAR(100),
    old_value NVARCHAR(MAX),
    new_value NVARCHAR(MAX),
    changed_by NVARCHAR(100) NOT NULL,
    changed_date DATETIME NOT NULL DEFAULT GETDATE(),
    user_ip NVARCHAR(50),
    user_agent NVARCHAR(500),
    additional_notes NVARCHAR(MAX)
);

CREATE INDEX IX_AuditLog_Table ON AuditLog(table_name, record_id);
CREATE INDEX IX_AuditLog_Date ON AuditLog(changed_date DESC);
CREATE INDEX IX_AuditLog_User ON AuditLog(changed_by);
```

### Problem: Audit logs created but not visible in web UI

**Check 1: Date Filtering**
The audit log page shows last 30 days by default. Check if your system date is correct.

**Check 2: Direct Query**
```sql
-- Get all audit logs
SELECT * FROM AuditLog ORDER BY changed_date DESC;
```

**Check 3: Browser Console**
Open browser developer tools (F12) and check for JavaScript errors on the Audit Log page.

## 📊 What Gets Logged

### For Facilities:
- **CREATE**: Facility name, location, active status
- **UPDATE**: Old and new values for each changed field
- **DEACTIVATE**: Status change from active to inactive

### For Production Lines:
- **CREATE**: Line name, code, facility, active status  
- **UPDATE**: Old and new values for each changed field
- **DEACTIVATE**: Status change from active to inactive

### Each audit entry includes:
- **Who**: Username of the person making the change
- **When**: Exact timestamp
- **Where**: IP address and browser info
- **What**: Specific fields that changed
- **Values**: Both old and new values

## 🛠️ Manual Testing

### Test Facility Audit:
1. Login as admin
2. Go to `/admin/facilities`
3. Add a new facility called "Test Facility"
4. Edit it and change the location
5. Deactivate it
6. Go to `/admin/audit-log`
7. You should see 3 entries for this facility

### Test via SQL:
```sql
-- Insert test audit entry
INSERT INTO AuditLog (
    table_name, record_id, action_type, 
    field_name, old_value, new_value,
    changed_by, changed_date, 
    user_ip, additional_notes
) VALUES (
    'Facilities', 999, 'TEST',
    'test_field', 'old_test', 'new_test',
    'manual_test', GETDATE(),
    '127.0.0.1', 'Manual SQL test'
);

-- Verify it was inserted
SELECT * FROM AuditLog WHERE record_id = 999;
```

## 📈 Performance Considerations

The AuditLog table has indexes on:
- `(table_name, record_id)` - For looking up history of specific records
- `changed_date DESC` - For chronological queries
- `changed_by` - For user activity reports

If the table grows very large (>1 million rows), consider:
1. Archiving old entries (>1 year)
2. Partitioning by date
3. Creating a summary table for reporting

## 🔐 Security Notes

- Audit logs should never be deleted directly
- Only the database admin should have DELETE permissions on AuditLog
- Consider setting up a database trigger to prevent deletions
- Regular backups of the AuditLog table are recommended

## 📝 Viewing Audit Logs

### In the Application:
- **All Logs**: `/admin/audit-log`
- **Facility History**: Click "History" button on any facility
- **Line History**: Click "History" button on any production line

### Via SQL:
```sql
-- Last 24 hours of changes
SELECT * FROM AuditLog 
WHERE changed_date >= DATEADD(hour, -24, GETDATE())
ORDER BY changed_date DESC;

-- All changes by a specific user
SELECT * FROM AuditLog 
WHERE changed_by = 'username'
ORDER BY changed_date DESC;

-- History of a specific facility
SELECT * FROM AuditLog 
WHERE table_name = 'Facilities' AND record_id = 1
ORDER BY changed_date DESC;
```

## ✅ Verification Checklist

- [ ] AuditLog table exists in database
- [ ] Running `python test_audit_logging.py` shows success
- [ ] Creating a facility generates audit logs
- [ ] Editing a facility shows old and new values
- [ ] Audit Log page (`/admin/audit-log`) displays entries
- [ ] Console shows "✅ Audit logged" messages
- [ ] No "❌ Audit logging failed" errors in console

## Need Help?

If audit logging still isn't working after following this guide:

1. Check the console output when running the app
2. Look for error messages in the browser console
3. Verify database permissions for the ProductionUser
4. Ensure the database connection isn't timing out
5. Check that transactions are being committed

Remember: The audit log is critical for compliance and troubleshooting, so it's worth ensuring it works correctly!