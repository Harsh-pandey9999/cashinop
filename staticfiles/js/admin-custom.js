// Admin Custom JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Theme Switcher
    initializeThemeSwitcher();
    
    // Enhanced Navigation
    initializeNavigation();
    
    // Enhanced Tables
    initializeTables();
    
    // Enhanced Forms
    initializeForms();
    
    // Notifications
    initializeNotifications();
});

// Theme Switcher
function initializeThemeSwitcher() {
    const themeSwitch = document.createElement('div');
    themeSwitch.className = 'theme-switch-wrapper';
    themeSwitch.innerHTML = `
        <label class="theme-switch" for="theme-switch">
            <input type="checkbox" id="theme-switch">
            <span class="theme-switch-slider"></span>
        </label>
        <span class="theme-label">Dark Mode</span>
    `;
    
    // Add theme switcher to the navbar
    const navbar = document.querySelector('.navbar-nav');
    if (navbar) {
        navbar.appendChild(themeSwitch);
    }
    
    // Theme switch functionality
    const checkbox = document.getElementById('theme-switch');
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    // Set initial theme
    document.documentElement.setAttribute('data-theme', currentTheme);
    checkbox.checked = currentTheme === 'dark';
    
    // Theme switch event listener
    checkbox.addEventListener('change', function() {
        const theme = this.checked ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        // Update Jazzmin theme
        updateJazzminTheme(theme);
    });
}

// Update Jazzmin theme
function updateJazzminTheme(theme) {
    const themeLink = document.querySelector('link[href*="bootstrap"]');
    if (themeLink) {
        const currentHref = themeLink.href;
        const newHref = currentHref.replace(
            /bootstrap\.(min\.)?css/,
            `bootstrap-${theme}.min.css`
        );
        themeLink.href = newHref;
    }
}

// Enhanced Navigation
function initializeNavigation() {
    // Add active class to current nav item
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-sidebar .nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
    
    // Add hover effects
    document.querySelectorAll('.nav-sidebar .nav-item').forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.querySelector('.nav-link').style.transform = 'translateX(5px)';
        });
        
        item.addEventListener('mouseleave', function() {
            this.querySelector('.nav-link').style.transform = 'translateX(0)';
        });
    });
    
    // Collapsible sidebar
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            document.body.classList.toggle('sidebar-collapse');
        });
    }
}

// Enhanced Tables
function initializeTables() {
    // Add hover effects to table rows
    document.querySelectorAll('.table tbody tr').forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = 'rgba(0, 123, 255, 0.05)';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });
    
    // Add sorting functionality
    document.querySelectorAll('.table thead th').forEach(header => {
        if (header.dataset.sortable !== 'false') {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                sortTable(this);
            });
        }
    });
}

// Table sorting function
function sortTable(header) {
    const table = header.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const index = Array.from(header.parentElement.children).indexOf(header);
    const direction = header.dataset.direction === 'asc' ? -1 : 1;
    
    // Update sort direction
    header.dataset.direction = direction === 1 ? 'asc' : 'desc';
    
    // Sort rows
    rows.sort((a, b) => {
        const aValue = a.children[index].textContent.trim();
        const bValue = b.children[index].textContent.trim();
        return direction * aValue.localeCompare(bValue);
    });
    
    // Reorder rows
    rows.forEach(row => tbody.appendChild(row));
}

// Enhanced Forms
function initializeForms() {
    // Add focus effects to form controls
    document.querySelectorAll('.form-control').forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
    });
    
    // Add validation styles
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            
            this.querySelectorAll('[required]').forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.classList.add('is-invalid');
                } else {
                    input.classList.remove('is-invalid');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    });
}

// Notifications
function initializeNotifications() {
    // Create notification container if it doesn't exist
    if (!document.querySelector('.notification-container')) {
        const container = document.createElement('div');
        container.className = 'notification-container';
        document.body.appendChild(container);
    }
    
    // Show notification function
    window.showNotification = function(message, type = 'info') {
        const container = document.querySelector('.notification-container');
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;
        
        container.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('notification-hide');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
        
        // Close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.classList.add('notification-hide');
            setTimeout(() => notification.remove(), 300);
        });
    };
}

// Add loading state to buttons
document.addEventListener('click', function(e) {
    if (e.target.matches('button[type="submit"]')) {
        e.target.classList.add('loading');
    }
});

// Add tooltips
document.querySelectorAll('[data-tooltip]').forEach(element => {
    element.addEventListener('mouseenter', function() {
        const tooltip = this.getAttribute('data-tooltip');
        const tooltipElement = document.createElement('div');
        tooltipElement.className = 'tooltip';
        tooltipElement.textContent = tooltip;
        document.body.appendChild(tooltipElement);
        
        const rect = this.getBoundingClientRect();
        tooltipElement.style.top = `${rect.top - tooltipElement.offsetHeight - 5}px`;
        tooltipElement.style.left = `${rect.left + (rect.width - tooltipElement.offsetWidth) / 2}px`;
    });
    
    element.addEventListener('mouseleave', function() {
        const tooltip = document.querySelector('.tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    });
}); 