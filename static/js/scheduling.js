// static/js/scheduling.js

document.addEventListener('DOMContentLoaded', function() {
    
    // --- INITIALIZATION ---
    // Initial population of filters is now handled by filterGrid's call to updateFilterOptions
    attachAllEventListeners();
    filterGrid(); // Run initial filter to set everything up
    updateLastUpdatedTime();

    if (sessionStorage.getItem('wasRefreshed')) {
        dtUtils.showAlert('Data refreshed successfully!', 'success');
        sessionStorage.removeItem('wasRefreshed');
    }
});

// --- EVENT LISTENERS ---
function attachAllEventListeners() {
    document.getElementById('facilityFilter').addEventListener('change', filterGrid);
    document.getElementById('soTypeFilter').addEventListener('change', filterGrid);
    document.getElementById('customerFilter').addEventListener('change', filterGrid);
    document.getElementById('dueShipFilter').addEventListener('change', filterGrid);
    document.getElementById('exportBtn').addEventListener('click', exportVisibleDataToXlsx);
    document.getElementById('refreshBtn').addEventListener('click', () => {
        sessionStorage.setItem('wasRefreshed', 'true');
        window.location.reload();
    });
    attachEditableListeners(document.getElementById('schedule-body'));
}

// --- UI, FILTERING & TOTALS ---
function updateLastUpdatedTime() {
    const timestampEl = document.getElementById('lastUpdated');
    if (timestampEl) {
        const now = new Date();
        const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        timestampEl.textContent = `Last Updated: ${timeString}`;
    }
}

function calculateTotals() {
    let totalNoLowRisk = 0;
    let totalHighRisk = 0;

    document.querySelectorAll('#schedule-body tr:not(.hidden-row)').forEach(row => {
        const noLowRiskCell = row.querySelector('[data-calculated-for="No/Low Risk Qty"]');
        const highRiskCell = row.querySelector('[data-calculated-for="High Risk Qty"]');

        if (noLowRiskCell) totalNoLowRisk += parseFloat(noLowRiskCell.textContent.replace(/[$,]/g, '')) || 0;
        if (highRiskCell) totalHighRisk += parseFloat(highRiskCell.textContent.replace(/[$,]/g, '')) || 0;
    });

    document.getElementById('total-no-low-risk').textContent = totalNoLowRisk.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
    document.getElementById('total-high-risk').textContent = totalHighRisk.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
}

function updateRowCount() {
    const totalRows = document.querySelectorAll('#schedule-body tr[data-so-number]').length;
    const visibleRows = document.querySelectorAll('#schedule-body tr:not(.hidden-row)').length;
    const rowCountEl = document.getElementById('rowCount');
    if (rowCountEl) {
         if (totalRows === 0 && document.querySelector('#schedule-body td[colspan]')) {
             rowCountEl.textContent = `Showing 0 of 0 rows`;
        } else {
             rowCountEl.textContent = `Showing ${visibleRows} of ${totalRows} rows`;
        }
    }
}

function populateSelect(selectId, options, addBlankOption = false, selectedValue = null) {
    const select = document.getElementById(selectId);
    if (!select) return;

    select.innerHTML = `<option value="">All</option>`;
    options.forEach(optionText => {
        if (optionText) {
            const option = document.createElement('option');
            option.value = optionText;
            option.textContent = optionText;
            select.appendChild(option);
        }
    });
    if (addBlankOption) {
        const blankOption = document.createElement('option');
        blankOption.value = 'Blank';
        blankOption.textContent = 'Blank';
        select.appendChild(blankOption);
    }
    
    // Preserve the selection if it's still a valid option in the new list
    if (selectedValue) {
        const optionExists = Array.from(select.options).some(opt => opt.value === selectedValue);
        if (optionExists) {
            select.value = selectedValue;
        }
    }
}

function updateFilterOptions() {
    // Get current selections to preserve them
    const selectedFacility = document.getElementById('facilityFilter').value;
    const selectedSoType = document.getElementById('soTypeFilter').value;
    const selectedCustomer = document.getElementById('customerFilter').value;
    const selectedDueDate = document.getElementById('dueShipFilter').value;

    const allRows = document.getElementById('schedule-body').querySelectorAll('tr');
    
    // Temporarily apply filters to determine available options for other dropdowns
    const getOptionsFor = (filterToUpdate) => {
        const options = new Set();
        let hasBlank = false;
        
        allRows.forEach(row => {
            if (row.cells.length < 5) return;
            
            const facility = row.querySelector('[data-field="Facility"]')?.textContent || '';
            const soType = row.querySelector('[data-field="SO Type"]')?.textContent || '';
            const customer = row.querySelector('[data-field="Customer Name"]')?.textContent || '';
            const dueDate = row.querySelector('[data-field="Due to Ship"]')?.textContent.trim() || '';
            const dueDateMonthYear = (dueDate && dueDate.includes('/')) ? `${dueDate.split('/')[0].padStart(2, '0')}/${dueDate.split('/')[2]}` : 'Blank';

            let matches = true;
            if (filterToUpdate !== 'facility' && selectedFacility && facility !== selectedFacility) matches = false;
            if (filterToUpdate !== 'soType' && selectedSoType && soType !== selectedSoType) matches = false;
            if (filterToUpdate !== 'customer' && selectedCustomer && customer !== selectedCustomer) matches = false;
            if (filterToUpdate !== 'dueShip' && selectedDueDate) {
                if (selectedDueDate === 'Blank' && dueDate !== '') matches = false;
                else if (selectedDueDate !== 'Blank' && dueDateMonthYear !== selectedDueDate) matches = false;
            }

            if (matches) {
                switch(filterToUpdate) {
                    case 'facility': options.add(facility); break;
                    case 'soType': options.add(soType); break;
                    case 'customer': options.add(customer); break;
                    case 'dueShip': 
                        if (dueDateMonthYear === 'Blank') hasBlank = true;
                        else options.add(dueDateMonthYear);
                        break;
                }
            }
        });
        return { options: [...options].sort(), hasBlank };
    };
    
    const facilityOpts = getOptionsFor('facility');
    const soTypeOpts = getOptionsFor('soType');
    const customerOpts = getOptionsFor('customer');
    const dueDateOpts = getOptionsFor('dueShip');

    const sortedDueDates = dueDateOpts.options.sort((a, b) => {
        const [aMonth, aYear] = a.split('/');
        const [bMonth, bYear] = b.split('/');
        return new Date(aYear, aMonth - 1) - new Date(bYear, bMonth - 1);
    });

    populateSelect('facilityFilter', facilityOpts.options, false, selectedFacility);
    populateSelect('soTypeFilter', soTypeOpts.options, false, selectedSoType);
    populateSelect('customerFilter', customerOpts.options, false, selectedCustomer);
    populateSelect('dueShipFilter', sortedDueDates, dueDateOpts.hasBlank, selectedDueDate);
}

function filterGrid() {
    const facilityFilter = document.getElementById('facilityFilter').value;
    const soTypeFilter = document.getElementById('soTypeFilter').value;
    const customerFilter = document.getElementById('customerFilter').value;
    const dueShipFilter = document.getElementById('dueShipFilter').value;

    document.getElementById('schedule-body').querySelectorAll('tr').forEach(row => {
        if (row.cells.length < 2) return;
        const facility = row.querySelector('[data-field="Facility"]')?.textContent || '';
        const soType = row.querySelector('[data-field="SO Type"]')?.textContent || '';
        const customer = row.querySelector('[data-field="Customer Name"]')?.textContent || '';
        const dueDate = row.querySelector('[data-field="Due to Ship"]')?.textContent.trim() || '';
        
        let show = true;
        if (facilityFilter && facility !== facilityFilter) show = false;
        if (soTypeFilter && soType !== soTypeFilter) show = false;
        if (customerFilter && customer !== customerFilter) show = false;
        
        if (dueShipFilter) {
            if (dueShipFilter === 'Blank') {
                if (dueDate !== '') show = false;
            } else {
                if (!dueDate || !dueDate.includes('/')) {
                    show = false;
                } else {
                    const [month, day, year] = dueDate.split('/');
                    if (`${month.padStart(2, '0')}/${year}` !== dueShipFilter) {
                        show = false;
                    }
                }
            }
        }
        row.classList.toggle('hidden-row', !show);
    });
    
    // After filtering rows, update everything else.
    updateFilterOptions();
    updateRowCount();
    calculateTotals();
    validateAllRows();
}


// --- VALIDATION & SUGGESTION LOGIC ---
function validateAllRows() {
    document.querySelectorAll('#schedule-body tr:not(.hidden-row)').forEach(validateRow);
}

function validateRow(row) {
    // Clear previous warnings
    row.classList.remove('row-warning');
    const existingFix = row.querySelector('.suggestion-fix');
    if (existingFix) existingFix.remove();

    // Get values
    const netQtyCell = row.cells[9];
    const noLowRiskCell = row.querySelector('[data-risk-type="No/Low Risk Qty"]');
    const highRiskCell = row.querySelector('[data-risk-type="High Risk Qty"]');

    if (!netQtyCell || !noLowRiskCell || !highRiskCell) return;

    const netQty = parseFloat(netQtyCell.textContent.replace(/,/g, '')) || 0;
    const noLowRiskQty = parseFloat(noLowRiskCell.textContent.replace(/,/g, '')) || 0;
    const highRiskQty = parseFloat(highRiskCell.textContent.replace(/,/g, '')) || 0;

    const totalProjected = noLowRiskQty + highRiskQty;
    const difference = totalProjected - netQty;

    // Check if the difference is significant (handles floating point inaccuracies)
    if (Math.abs(difference) > 0.01) {
        row.classList.add('row-warning'); // Always add warning if there's a discrepancy

        // ONLY show the "Fix" button if the total projected is LESS than the Net Qty
        if (difference < 0) { // This means totalProjected is less than netQty
            // Suggest a fix by adding the shortfall to the No/Low Risk Qty
            const suggestedNoLowRisk = Math.max(0, noLowRiskQty - difference);

            const fixButton = document.createElement('button');
            fixButton.className = 'suggestion-fix';
            fixButton.title = `Suggestion: Set to ${suggestedNoLowRisk.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})} to match Net Qty`;
            fixButton.textContent = 'Fix';
            fixButton.dataset.suggestion = suggestedNoLowRisk;
            fixButton.onclick = function() { applySuggestion(this); };
            
            noLowRiskCell.appendChild(fixButton);
        }
    }
}


function applySuggestion(buttonElement) {
    const suggestion = parseFloat(buttonElement.dataset.suggestion);
    const cell = buttonElement.closest('td');

    if (cell) {
        // Set the new value and trigger the save process
        cell.textContent = suggestion.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        cell.focus();
        cell.blur();
    }
}

// --- EDITABLE CELL LOGIC ---
function attachEditableListeners(scope) {
    scope.querySelectorAll('.editable').forEach(cell => {
        cell.addEventListener('blur', handleCellBlur);
        cell.addEventListener('focus', handleCellFocus);
        cell.addEventListener('keydown', handleCellKeyDown);
    });
}

function handleCellBlur() {
    const el = this;
    el.querySelectorAll('.status-indicator').forEach(indicator => indicator.remove());
    const originalValue = el.getAttribute('data-original-value') || '0';
    let newValue = el.textContent.trim().replace(/[$,]/g, '');

    if (isNaN(newValue) || newValue.trim() === '') {
        el.textContent = (parseFloat(originalValue) || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        dtUtils.showAlert('Please enter a valid number.', 'error');
        return;
    }
    const quantity = parseFloat(newValue);
    el.textContent = quantity.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    
    // Re-validate the row after editing
    validateRow(el.closest('tr'));

    if (Math.abs(parseFloat(originalValue) - quantity) < 0.001) return;

    const statusIndicator = document.createElement('span');
    statusIndicator.className = 'status-indicator saving';
    el.appendChild(statusIndicator);
    
    const row = el.closest('tr');
    const soNumber = row.dataset.soNumber;
    const partNumber = row.dataset.partNumber;
    const riskType = el.dataset.riskType;
    const price = parseFloat(el.dataset.price) || 0;

    const payload = { so_number: soNumber, part_number: partNumber, risk_type: riskType, quantity: quantity };

    fetch('/scheduling/api/update-projection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(response => {
        if (!response.ok) { throw new Error(`HTTP error ${response.status}`); }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            statusIndicator.className = 'status-indicator success';
            el.setAttribute('data-original-value', quantity.toString());

            const calculatedCell = row.querySelector(`[data-calculated-for="${riskType}"]`);
            if (calculatedCell) {
                const newDollarValue = quantity * price;
                calculatedCell.textContent = newDollarValue.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
            }
            calculateTotals();
            setTimeout(() => { statusIndicator.style.opacity = '0'; }, 2000);
        } else {
            throw new Error(data.message || 'Save failed.');
        }
    })
    .catch(error => {
        console.error('Save Error:', error);
        statusIndicator.className = 'status-indicator error';
        el.innerHTML = (parseFloat(originalValue) || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        const errorIndicator = document.createElement('span');
        errorIndicator.className = 'status-indicator error';
        errorIndicator.style.opacity = '1';
        el.appendChild(errorIndicator);
        dtUtils.showAlert(`Save failed: ${error.message}`, 'error');
    });
}

function handleCellFocus(e) {
    const cleanValue = e.target.textContent.trim().replace(/[$,]/g, '');
    e.target.setAttribute('data-original-value', cleanValue);
    // Remove suggestion button on focus for easier editing
    e.target.querySelectorAll('.suggestion-fix').forEach(btn => btn.remove());
}

function handleCellKeyDown(e) {
    if (!/[\d.]/.test(e.key) && !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab', 'Enter'].includes(e.key)) { e.preventDefault(); }
    if (e.key === 'Enter') { e.preventDefault(); e.target.blur(); }
}

// --- EXPORT LOGIC ---
function exportVisibleDataToXlsx() {
    const exportBtn = document.getElementById('exportBtn');
    exportBtn.disabled = true;
    exportBtn.textContent = '📥 Generating...';

    const headers = Array.from(document.querySelectorAll('.grid-table thead th')).map(th => th.textContent.trim());

    const rows = [];
    document.querySelectorAll('#schedule-body tr:not(.hidden-row)').forEach(row => {
        const rowData = [];
        row.querySelectorAll('td').forEach(cell => {
            // Exclude the hidden "SO Type" column from the export
            if (cell.getAttribute('data-field') !== 'SO Type') {
                rowData.push(cell.textContent.trim());
            }
        });
        rows.push(rowData);
    });

    if (rows.length === 0) {
        dtUtils.showAlert('No data to export.', 'info');
        exportBtn.disabled = false;
        exportBtn.textContent = '📥 Download XLSX';
        return;
    }
    
    fetch('/scheduling/api/export-xlsx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ headers, rows })
    })
    .then(response => {
        if (!response.ok) { throw new Error('Network response was not ok.'); }
        const disposition = response.headers.get('Content-Disposition');
        const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
        const filename = (matches != null && matches[1]) ? matches[1].replace(/['"]/g, '') : 'schedule_export.xlsx';
        return Promise.all([response.blob(), filename]);
    })
    .then(([blob, filename]) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        
        exportBtn.disabled = false;
        exportBtn.textContent = '📥 Download XLSX';
    })
    .catch(error => {
        console.error('Export error:', error);
        dtUtils.showAlert('An error occurred during the export.', 'error');
        exportBtn.disabled = false;
        exportBtn.textContent = '📥 Download XLSX';
    });
}