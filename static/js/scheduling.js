// static/js/scheduling.js

document.addEventListener('DOMContentLoaded', function() {
    
    // --- INITIALIZATION ---
    initializeColumnToggle(); // Set up column toggling first
    attachAllEventListeners();
    
    // 1. Populate filters with all possible options from the full dataset first.
    updateFilterOptions(); 
    
    // 2. Now that all <option> elements exist, restore the saved selections.
    restoreFilters();      
    
    // 3. Finally, run the filter to update the grid view based on the restored state.
    filterGrid();          
    
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
    document.getElementById('resetBtn').addEventListener('click', resetFilters);
    document.getElementById('refreshBtn').addEventListener('click', () => {
        // Save filters before reloading
        saveFilters(); 
        sessionStorage.setItem('wasRefreshed', 'true');
        window.location.reload();
    });
    attachEditableListeners(document.getElementById('schedule-body'));
}

// --- FILTER PERSISTENCE ---
function saveFilters() {
    const filters = {
        facility: document.getElementById('facilityFilter').value,
        soType: document.getElementById('soTypeFilter').value,
        customer: document.getElementById('customerFilter').value,
        dueShip: document.getElementById('dueShipFilter').value,
    };
    sessionStorage.setItem('schedulingFilters', JSON.stringify(filters));
}

function restoreFilters() {
    const savedFilters = JSON.parse(sessionStorage.getItem('schedulingFilters'));
    if (savedFilters) {
        document.getElementById('facilityFilter').value = savedFilters.facility || '';
        document.getElementById('soTypeFilter').value = savedFilters.soType || '';
        document.getElementById('customerFilter').value = savedFilters.customer || '';
        document.getElementById('dueShipFilter').value = savedFilters.dueShip || '';
    }
}

// --- NEW: RESET FILTERS ---
function resetFilters() {
    document.getElementById('facilityFilter').value = '';
    document.getElementById('soTypeFilter').value = '';
    document.getElementById('customerFilter').value = '';
    document.getElementById('dueShipFilter').value = '';
    sessionStorage.removeItem('schedulingFilters');
    filterGrid(); // Re-apply the blank filters
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
    
    updateForecastCards(totalNoLowRisk, totalHighRisk);
}

function updateForecastCards(totalNoLowRisk, totalHighRisk) {
    // Helper to parse currency string to float from an element by ID
    const getValueFromCardById = (elementId) => {
        const cardElement = document.getElementById(elementId);
        if (!cardElement) return 0;
        return parseFloat(cardElement.textContent.replace(/[$,]/g, '')) || 0;
    };

    // Get values from the existing 6 cards
    const shippedCurrentMonth = getValueFromCardById('shipped-as-value');
    const fgBefore = getValueFromCardById('fg-on-hand-before');
    const fgCurrent = getValueFromCardById('fg-on-hand-current');
    const fgFuture = getValueFromCardById('fg-on-hand-future');

    // Calculate "Likely" forecast
    const forecastLikelyValue = shippedCurrentMonth + totalNoLowRisk + fgCurrent;

    // Calculate "May Be" forecast
    const forecastMaybeValue = shippedCurrentMonth + totalNoLowRisk + totalHighRisk + fgBefore + fgCurrent + fgFuture;

    // Update the new cards
    document.getElementById('forecast-likely-value').textContent = forecastLikelyValue.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
    document.getElementById('forecast-maybe-value').textContent = forecastMaybeValue.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
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
    saveFilters(); // Save the current filter state
    updateFilterOptions();
    updateRowCount();
    calculateTotals();
    validateAllRows();
}

// --- NEW: COLUMN TOGGLE LOGIC ---
const COLUMNS_CONFIG_KEY = 'schedulingColumnConfig';

function initializeColumnToggle() {
    const dropdown = document.getElementById('column-dropdown');
    const headers = document.querySelectorAll('.grid-table thead th');
    let savedConfig = JSON.parse(localStorage.getItem(COLUMNS_CONFIG_KEY));

    // Default configuration if nothing is saved
    if (!savedConfig) {
        savedConfig = {};
        headers.forEach(th => {
            const id = th.dataset.columnId;
            if (id) {
                // By default hide these columns
                const defaultHidden = ['Ord Qty - (00) Level', 'Total Shipped Qty', 'Produced Qty', 'ERP Can Make', 'ERP Low Risk', 'ERP High Risk', 'Unit Price'];
                savedConfig[id] = !defaultHidden.includes(id);
            }
        });
    }
    
    // Populate dropdown and set listeners
    headers.forEach(th => {
        const id = th.dataset.columnId;
        if (id) {
            const isVisible = savedConfig[id] !== false; // Default to visible if not specified
            const label = document.createElement('label');
            label.innerHTML = `<input type="checkbox" data-column-id="${id}" ${isVisible ? 'checked' : ''}> ${id}`;
            dropdown.appendChild(label);

            label.querySelector('input').addEventListener('change', handleColumnToggle);
        }
    });

    applyColumnVisibility(savedConfig);

    const columnsBtn = document.getElementById('columnsBtn');
    columnsBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
        if (!dropdown.contains(e.target) && !columnsBtn.contains(e.target)) {
            dropdown.classList.remove('show');
        }
    });
}

function handleColumnToggle(e) {
    const columnId = e.target.dataset.columnId;
    const isVisible = e.target.checked;
    
    let savedConfig = JSON.parse(localStorage.getItem(COLUMNS_CONFIG_KEY)) || {};
    savedConfig[columnId] = isVisible;
    localStorage.setItem(COLUMNS_CONFIG_KEY, JSON.stringify(savedConfig));
    
    applyColumnVisibility(savedConfig);
}

function applyColumnVisibility(config) {
    const table = document.querySelector('.grid-table');
    const headers = Array.from(table.querySelectorAll('thead th'));

    for (const columnId in config) {
        const isVisible = config[columnId];
        const headerIndex = headers.findIndex(th => th.dataset.columnId === columnId);

        if (headerIndex > -1) {
            const displayStyle = isVisible ? '' : 'none';
            // Toggle header
            table.querySelector(`th[data-column-id="${columnId}"]`).style.display = displayStyle;
            // Toggle all cells in that column
            table.querySelectorAll(`tbody tr`).forEach(row => {
                if (row.cells[headerIndex]) {
                    row.cells[headerIndex].style.display = displayStyle;
                }
            });
        }
    }
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
    scope.querySelectorAll('.editable:not(.view-only)').forEach(cell => {
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

    const headers = Array.from(document.querySelectorAll('.grid-table thead th'))
        .filter(th => th.style.display !== 'none') // Only include visible headers
        .map(th => th.textContent.trim());

    const rows = [];
    document.querySelectorAll('#schedule-body tr:not(.hidden-row)').forEach(row => {
        const rowData = [];
        row.querySelectorAll('td').forEach(cell => {
            // Exclude hidden columns and the hidden "SO Type" column from the export
            if (cell.style.display !== 'none' && cell.getAttribute('data-field') !== 'SO Type') {
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