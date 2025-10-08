// static/js/mrp.js
document.addEventListener('DOMContentLoaded', function() {
    initializeFilters();
    attachAllEventListeners();
    filterMRP(); // Run initial filter to update counts
});

function attachAllEventListeners() {
    // Accordion toggles
    document.querySelectorAll('.so-header').forEach(header => {
        header.addEventListener('click', function() {
            this.classList.toggle('expanded');
            const details = document.getElementById(this.dataset.target);
            if (details) {
                details.style.display === 'block' ? slideUp(details) : slideDown(details);
            }
        });
    });

    // Filter changes
    document.getElementById('facilityFilter').addEventListener('change', filterMRP);
    document.getElementById('buFilter').addEventListener('change', filterMRP);
    document.getElementById('customerFilter').addEventListener('change', filterMRP);
    document.getElementById('statusFilter').addEventListener('change', filterMRP);
    document.getElementById('resetBtn').addEventListener('click', resetFilters);
}

function initializeFilters() {
    const headers = document.querySelectorAll('.so-header');
    const facilityOptions = new Set();
    const buOptions = new Set();
    const customerOptions = new Set();

    headers.forEach(header => {
        facilityOptions.add(header.dataset.facility);
        buOptions.add(header.dataset.bu);
        customerOptions.add(header.dataset.customer);
    });

    populateSelect('facilityFilter', [...facilityOptions].sort());
    populateSelect('buFilter', [...buOptions].sort());
    populateSelect('customerFilter', [...customerOptions].sort());
}

function populateSelect(selectId, options) {
    const select = document.getElementById(selectId);
    options.forEach(optionText => {
        if (optionText) {
            const option = document.createElement('option');
            option.value = optionText;
            option.textContent = optionText;
            select.appendChild(option);
        }
    });
}

function filterMRP() {
    const facilityFilter = document.getElementById('facilityFilter').value;
    const buFilter = document.getElementById('buFilter').value;
    const customerFilter = document.getElementById('customerFilter').value;
    const statusFilter = document.getElementById('statusFilter').value;

    let visibleCount = 0;
    let okCount = 0;
    let partialCount = 0;
    let criticalCount = 0;

    document.querySelectorAll('.so-header').forEach(header => {
        let show = true;
        if (facilityFilter && header.dataset.facility !== facilityFilter) show = false;
        if (buFilter && header.dataset.bu !== buFilter) show = false;
        if (customerFilter && header.dataset.customer !== customerFilter) show = false;
        if (statusFilter && header.dataset.status !== statusFilter) show = false;

        header.classList.toggle('hidden-row', !show);
        
        if(show) {
            visibleCount++;
            if (header.dataset.status === 'ok') okCount++;
            if (header.dataset.status === 'partial') partialCount++;
            if (header.dataset.status === 'critical') criticalCount++;
        }
    });

    updateSummaryCards(visibleCount, okCount, partialCount, criticalCount);
}

function resetFilters() {
    document.getElementById('facilityFilter').value = '';
    document.getElementById('buFilter').value = '';
    document.getElementById('customerFilter').value = '';
    document.getElementById('statusFilter').value = '';
    filterMRP();
}

function updateSummaryCards(total, ok, partial, critical) {
    document.getElementById('total-orders').textContent = total;
    document.getElementById('full-production').textContent = ok;
    document.getElementById('partial-production').textContent = partial;
    document.getElementById('critical-shortage').textContent = critical;
}

/* Simple slide-down animation */
function slideDown(element) {
    element.style.display = 'block';
    let height = element.scrollHeight + 'px';
    element.style.height = 0;
    setTimeout(() => {
        element.style.transition = 'height 0.3s ease-in-out';
        element.style.height = height;
    }, 0);
    setTimeout(() => {
        element.style.removeProperty('height');
        element.style.removeProperty('transition');
    }, 300);
}

/* Simple slide-up animation */
function slideUp(element) {
    element.style.height = element.scrollHeight + 'px';
    setTimeout(() => {
        element.style.transition = 'height 0.3s ease-in-out';
        element.style.height = 0;
    }, 0);
    setTimeout(() => {
        element.style.display = 'none';
        element.style.removeProperty('height');
        element.style.removeProperty('transition');
    }, 300);
}