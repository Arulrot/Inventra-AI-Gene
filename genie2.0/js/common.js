// Global Application State
window.InventAI = {
    isLoggedIn: false,
    currentUser: null,
    data: {
        products: [
            {
                id: 'P001',
                name: 'Wireless Gaming Mouse',
                brand: 'Logitech',
                category: 'Electronics',
                supplier: 'TechMart Solutions',
                price: 49.99,
                quantity: 8,
                minStock: 15,
                addedDate: '2024-08-01',
                expiryDate: '2025-12-31',
                status: 'low-stock'
            },
            {
                id: 'P002',
                name: 'Men\'s Cotton T-Shirt',
                brand: 'Nike',
                category: 'Men',
                supplier: 'Fashion World',
                price: 24.99,
                quantity: 25,
                minStock: 20,
                addedDate: '2024-08-02',
                expiryDate: '2025-08-30',
                status: 'in-stock'
            },
            {
                id: 'P003',
                name: 'Executive Office Chair',
                brand: 'Herman Miller',
                category: 'Furniture',
                supplier: 'Office Solutions',
                price: 299.99,
                quantity: 12,
                minStock: 8,
                addedDate: '2024-08-03',
                expiryDate: '2026-08-30',
                status: 'in-stock'
            },
            {
                id: 'P004',
                name: 'Kids Educational Toy',
                brand: 'LEGO',
                category: 'Kids',
                supplier: 'Toy World',
                price: 19.99,
                quantity: 3,
                minStock: 25,
                addedDate: '2024-08-04',
                expiryDate: '2025-12-31',
                status: 'low-stock'
            }
        ],
        suppliers: [
            {
                id: 'S001',
                name: 'TechMart Solutions',
                company: 'TechMart Pvt Ltd',
                contactPerson: 'John Smith',
                phone: '+1-555-0123',
                email: 'john@techmart.com',
                rating: 4.8,
                status: 'Active'
            },
            {
                id: 'S002',
                name: 'Fashion World',
                company: 'Fashion Corp',
                contactPerson: 'Sarah Johnson',
                phone: '+1-555-0124',
                email: 'sarah@fashionworld.com',
                rating: 4.5,
                status: 'Active'
            },
            {
                id: 'S003',
                name: 'Office Solutions',
                company: 'Office Solutions Inc',
                contactPerson: 'Mike Brown',
                phone: '+1-555-0125',
                email: 'mike@officesolutions.com',
                rating: 4.7,
                status: 'Active'
            }
        ],
        categories: [
            { id: 'C001', name: 'Electronics', icon: '📱', description: 'Electronic devices and gadgets' },
            { id: 'C002', name: 'Men', icon: '👨', description: 'Men\'s clothing and accessories' },
            { id: 'C003', name: 'Women', icon: '👩', description: 'Women\'s clothing and accessories' },
            { id: 'C004', name: 'Kids', icon: '👶', description: 'Children\'s items and toys' },
            { id: 'C005', name: 'Furniture', icon: '🪑', description: 'Furniture and home decor' },
            { id: 'C006', name: 'Sports', icon: '⚽', description: 'Sports equipment and accessories' }
        ],
        activities: [
            { time: '10:30 AM', message: '✅ System initialized successfully', type: 'success' },
            { time: '10:31 AM', message: '🤖 AI Engine activated and monitoring', type: 'info' },
            { time: '10:32 AM', message: '📦 Product "Wireless Mouse" stock low', type: 'warning' },
            { time: '10:33 AM', message: '📊 Dashboard statistics loaded', type: 'info' }
        ]
    }
};

// Utility Functions
const Utils = {
    // Format currency
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    },

    // Format date
    formatDate(date) {
        return new Date(date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },

    // Generate next ID
    generateNextId(prefix, dataArray) {
        const numbers = dataArray
            .map(item => parseInt(item.id.substring(1)))
            .filter(num => !isNaN(num));
        const maxNumber = numbers.length > 0 ? Math.max(...numbers) : 0;
        return `${prefix}${String(maxNumber + 1).padStart(3, '0')}`;
    },

    // Get current timestamp
    getCurrentTimestamp() {
        return new Date().toISOString().split('T')[0];
    },

    // Calculate days between dates
    daysBetween(date1, date2) {
        const oneDay = 24 * 60 * 60 * 1000;
        return Math.round(Math.abs((new Date(date1) - new Date(date2)) / oneDay));
    }
};

// Toast Notification System
const Toast = {
    show(message, type = 'success') {
        const toast = document.getElementById('toast');
        if (!toast) return;

        toast.textContent = message;
        toast.className = `toast ${type}`;
        
        // Trigger show animation
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);

        // Auto hide after 4 seconds
        setTimeout(() => {
            toast.classList.remove('show');
        }, 4000);
    },

    success(message) {
        this.show(message, 'success');
    },

    error(message) {
        this.show(message, 'error');
    },

    warning(message) {
        this.show(message, 'warning');
    },

    info(message) {
        this.show(message, 'info');
    }
};

// Time Display
function updateTimeDisplay() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    document.querySelectorAll('#currentTime').forEach(element => {
        element.textContent = timeString;
    });
}

// Authentication Functions
function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username')?.value.trim();
    const password = document.getElementById('password')?.value.trim();
    
    if (username === 'admin' && password === 'root') {
        InventAI.isLoggedIn = true;
        InventAI.currentUser = { username: 'admin', role: 'Administrator' };
        
        // Hide login, show dashboard
        const loginScreen = document.getElementById('loginScreen');
        const dashboard = document.getElementById('dashboard');
        
        if (loginScreen) loginScreen.style.display = 'none';
        if (dashboard) dashboard.style.display = 'grid';
        
        Toast.success('Welcome to InventAI Gene Pro!');
        addActivity('🔐 Admin user logged in successfully');
        
        // Initialize dashboard if function exists
        if (typeof initializeDashboard === 'function') {
            initializeDashboard();
        }
    } else {
        Toast.error('Invalid credentials. Please try again.');
    }
}

function handleLogout() {
    if (confirm('Are you sure you want to logout?')) {
        InventAI.isLoggedIn = false;
        InventAI.currentUser = null;
        
        // Redirect to main page or show login
        if (window.location.pathname !== '/index.html' && !window.location.pathname.endsWith('/')) {
            window.location.href = '../index.html';
        } else {
            const loginScreen = document.getElementById('loginScreen');
            const dashboard = document.getElementById('dashboard');
            
            if (loginScreen) loginScreen.style.display = 'flex';
            if (dashboard) dashboard.style.display = 'none';
            
            // Clear password field
            const passwordField = document.getElementById('password');
            if (passwordField) passwordField.value = '';
        }
        
        Toast.success('Logged out successfully');
    }
}

// Activity Management
function addActivity(message, type = 'info') {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
    
    const activity = {
        time: timeString,
        message: message,
        type: type
    };
    
    InventAI.data.activities.unshift(activity);
    
    // Keep only last 20 activities
    if (InventAI.data.activities.length > 20) {
        InventAI.data.activities = InventAI.data.activities.slice(0, 20);
    }
    
    // Update activity display if function exists
    if (typeof updateActivityDisplay === 'function') {
        updateActivityDisplay();
    }
}

// Statistics Calculation
function calculateStats() {
    const { products, suppliers, categories } = InventAI.data;
    
    return {
        totalProducts: products.length,
        lowStock: products.filter(p => p.quantity <= p.minStock).length,
        outOfStock: products.filter(p => p.quantity === 0).length,
        totalSuppliers: suppliers.filter(s => s.status === 'Active').length,
        totalCategories: categories.length,
        inventoryValue: products.reduce((sum, p) => sum + (p.price * p.quantity), 0),
        avgRating: suppliers.reduce((sum, s) => sum + s.rating, 0) / suppliers.length
    };
}

// Sidebar Toggle for Mobile
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
}

// Initialize common functionality
document.addEventListener('DOMContentLoaded', function() {
    // Update time every second
    updateTimeDisplay();
    setInterval(updateTimeDisplay, 1000);
    
    // Login form handler
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Logout button handler
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    
    // Sidebar toggle for mobile
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
        const sidebar = document.getElementById('sidebar');
        const sidebarToggle = document.getElementById('sidebarToggle');
        
        if (sidebar && sidebar.classList.contains('open')) {
            if (!sidebar.contains(event.target) && !sidebarToggle.contains(event.target)) {
                sidebar.classList.remove('open');
            }
        }
    });
    
    // Initialize page-specific functionality
    if (typeof initializePage === 'function') {
        initializePage();
    }
});

// Global error handler
window.addEventListener('error', function(event) {
    console.error('Application Error:', event.error);
    Toast.error('An unexpected error occurred. Please refresh the page.');
});

// Export globals for other scripts
window.Utils = Utils;
window.Toast = Toast;
window.addActivity = addActivity;
window.calculateStats = calculateStats;
window.handleLogin = handleLogin;
window.handleLogout = handleLogout;
