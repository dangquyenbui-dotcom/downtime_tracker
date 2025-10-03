/**
 * Theme Management System
 * Handles dark/light theme switching with persistence
 */

(function() {
    'use strict';
    
    // Show body after everything is loaded
    document.addEventListener('DOMContentLoaded', function() {
        document.body.classList.add('loaded');
        
        // Initialize theme toggle if it exists
        initializeTheme();
    });
    
    function initializeTheme() {
        const themeToggle = document.getElementById('themeToggle');
        if (!themeToggle) return;
        
        const htmlElement = document.documentElement;
        
        // Theme is already set in the head, just sync the toggle
        const currentTheme = htmlElement.getAttribute('data-theme') || 'light';
        themeToggle.checked = currentTheme === 'dark';
        
        // Handle theme toggle
        themeToggle.addEventListener('change', function() {
            const theme = this.checked ? 'dark' : 'light';
            htmlElement.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
            
            // Notify other tabs/windows about theme change
            window.dispatchEvent(new CustomEvent('themeChange', { detail: theme }));
        });
        
        // Listen for theme changes from other tabs
        window.addEventListener('storage', function(e) {
            if (e.key === 'theme') {
                const theme = e.newValue || 'light';
                htmlElement.setAttribute('data-theme', theme);
                themeToggle.checked = theme === 'dark';
            }
        });
        
        // Listen for theme change events within same tab
        window.addEventListener('themeChange', function(e) {
            const theme = e.detail;
            htmlElement.setAttribute('data-theme', theme);
            themeToggle.checked = theme === 'dark';
        });
    }
})();