// Dashboard specific functionality
let salesChart;

function initializeDashboard() {
    updateDashboardStats();
    updateActivityDisplay();
    updateTopProducts();
    createSalesChart();
    
    // Update last update time
    const lastUpdate = document.getElementById('lastUpdate');
    if (lastUpdate) {
        lastUpdate.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
    }
    
    addActivity('📊 Dashboard initialized successfully');
}

function updateDashboardStats() {
    const stats = calculateStats();
    
    // Update KPI cards
    const elements = {
        totalProducts: document.getElementById('totalProducts'),
        lowStock: document.getElementById('lowStock'),
        totalSuppliers: document.getElementById('totalSuppliers'),
        inventoryValue: document.getElementById('inventoryValue')
    };
    
    if (elements.totalProducts) elements.totalProducts.textContent = stats.totalProducts;
    if (elements.lowStock) elements.lowStock.textContent = stats.lowStock;
    if (elements.totalSuppliers) elements.totalSuppliers.textContent = stats.totalSuppliers;
    if (elements.inventoryValue) elements.inventoryValue.textContent = Utils.formatCurrency(stats.inventoryValue);
}

function updateActivityDisplay() {
    const activityList = document.getElementById('activityList');
    if (!activityList) return;
    
    activityList.innerHTML = '';
    
    InventAI.data.activities.slice(0, 5).forEach(activity => {
        const activityItem = document.createElement('div');
        activityItem.className = 'activity-item';
        
        const iconClass = activity.type === 'warning' ? 'fas fa-exclamation-triangle' :
                         activity.type === 'error' ? 'fas fa-times-circle' :
                         activity.type === 'success' ? 'fas fa-check-circle' : 'fas fa-info-circle';
        
        activityItem.innerHTML = `
            <div class="activity-icon">
                <i class="${iconClass}"></i>
            </div>
            <div class="activity-content">
                <div class="activity-title">${activity.message}</div>
                <div class="activity-time">${activity.time}</div>
            </div>
        `;
        
        activityList.appendChild(activityItem);
    });
}

function updateTopProducts() {
    const topProductsList = document.getElementById('topProductsList');
    if (!topProductsList) return;
    
    topProductsList.innerHTML = '';
    
    // Sort products by value (price * quantity)
    const sortedProducts = InventAI.data.products
        .map(product => ({
            ...product,
            value: product.price * product.quantity
        }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 5);
    
    sortedProducts.forEach((product, index) => {
        const productItem = document.createElement('div');
        productItem.className = 'product-item';
        
        productItem.innerHTML = `
            <div class="product-info">
                <div class="product-rank">${index + 1}</div>
                <div class="product-details">
                    <h4>${product.name}</h4>
                    <p>${product.brand} • ${product.category}</p>
                </div>
            </div>
            <div class="product-sales">${Utils.formatCurrency(product.value)}</div>
        `;
        
        topProductsList.appendChild(productItem);
    });
}

function createSalesChart() {
    const canvas = document.getElementById('salesChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Sample data for demo
    const data = [
        { day: 'Mon', sales: 1200 },
        { day: 'Tue', sales: 1900 },
        { day: 'Wed', sales: 800 },
        { day: 'Thu', sales: 1500 },
        { day: 'Fri', sales: 2000 },
        { day: 'Sat', sales: 2400 },
        { day: 'Sun', sales: 1100 }
    ];
    
    // Chart dimensions
    const padding = 60;
    const chartWidth = canvas.width - (padding * 2);
    const chartHeight = canvas.height - (padding * 2);
    
    // Find max value for scaling
    const maxSales = Math.max(...data.map(d => d.sales));
    
    // Draw axes
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 1;
    
    // Y-axis
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, canvas.height - padding);
    ctx.stroke();
    
    // X-axis
    ctx.beginPath();
    ctx.moveTo(padding, canvas.height - padding);
    ctx.lineTo(canvas.width - padding, canvas.height - padding);
    ctx.stroke();
    
    // Draw grid lines
    ctx.strokeStyle = '#f1f5f9';
    for (let i = 1; i <= 5; i++) {
        const y = padding + (chartHeight / 5) * i;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(canvas.width - padding, y);
        ctx.stroke();
    }
    
    // Draw data line
    ctx.strokeStyle = '#667eea';
    ctx.lineWidth = 3;
    ctx.beginPath();
    
    data.forEach((point, index) => {
        const x = padding + (chartWidth / (data.length - 1)) * index;
        const y = canvas.height - padding - (point.sales / maxSales) * chartHeight;
        
        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    
    ctx.stroke();
    
    // Draw data points
    ctx.fillStyle = '#667eea';
    data.forEach((point, index) => {
        const x = padding + (chartWidth / (data.length - 1)) * index;
        const y = canvas.height - padding - (point.sales / maxSales) * chartHeight;
        
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
    });
    
    // Draw labels
    ctx.fillStyle = '#64748b';
    ctx.font = '12px Inter, sans-serif';
    ctx.textAlign = 'center';
    
    data.forEach((point, index) => {
        const x = padding + (chartWidth / (data.length - 1)) * index;
        ctx.fillText(point.day, x, canvas.height - padding + 20);
    });
    
    // Y-axis labels
    ctx.textAlign = 'right';
    for (let i = 0; i <= 5; i++) {
        const value = (maxSales / 5) * (5 - i);
        const y = padding + (chartHeight / 5) * i + 5;
        ctx.fillText(`$${Math.round(value)}`, padding - 10, y);
    }
}

function refreshDashboard() {
    updateDashboardStats();
    updateActivityDisplay();
    updateTopProducts();
    createSalesChart();
    
    const lastUpdate = document.getElementById('lastUpdate');
    if (lastUpdate) {
        lastUpdate.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
    }
    
    addActivity('🔄 Dashboard refreshed');
    Toast.success('Dashboard refreshed successfully!');
}

// Page-specific initialization
function initializePage() {
    // Dashboard-specific initialization
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshDashboard);
    }
    
    // Auto-refresh every 5 minutes
    setInterval(refreshDashboard, 5 * 60 * 1000);
}

// Export for global access
window.initializeDashboard = initializeDashboard;
window.refreshDashboard = refreshDashboard;
window.initializePage = initializePage;
