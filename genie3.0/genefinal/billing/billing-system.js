// Enhanced Retail Billing System - Complete JavaScript Implementation
class EnhancedBillingSystem {
    constructor() {
        this.products = [];
        this.categories = [];
        this.suppliers = [];
        this.customers = [];
        this.cart = [];
        this.currentCustomer = null;
        this.currentBill = null;
        this.appliedCoupon = null;
        this.selectedPaymentMethod = 'cash';
        this.loyaltyPointsToUse = 0;
        this.availableCoupons = [];
        this.currentSection = 'pos';
        this.calculatorValue = '';
        this.calculatorOperator = '';
        this.calculatorPreviousValue = '';
        
        this.init();
    }

    async init() {
        try {
            this.showLoading('Initializing system...');
            
            // Initialize all data
            await Promise.all([
                this.loadProducts(),
                this.loadCategories(),
                this.loadSuppliers(),
                this.loadCustomers(),
                this.loadDashboardStats()
            ]);
            
            this.setupEventListeners();
            this.updateDateTime();
            this.showSection('pos');
            this.calculateTotals();
            
            this.showNotification('System Ready', 'success', 'Enhanced billing system initialized successfully');
        } catch (error) {
            console.error('Initialization failed:', error);
            this.showNotification('System Error', 'error', 'Failed to initialize system');
        } finally {
            this.hideLoading();
        }
    }

    // API Helper Methods
    async apiCall(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                headers: { 'Content-Type': 'application/json' },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }

    // Data Loading Methods
    async loadProducts(filters = {}) {
        try {
            const params = new URLSearchParams(filters);
            this.products = await this.apiCall(`/api/products?${params}`);
            this.displayProducts();
            this.updateProductStats();
        } catch (error) {
            this.showNotification('Load Error', 'error', 'Failed to load products');
        }
    }

    async loadCategories() {
        try {
            this.categories = await this.apiCall('/api/categories');
            this.populateCategoryDropdowns();
        } catch (error) {
            console.error('Failed to load categories:', error);
        }
    }

    async loadSuppliers() {
        try {
            this.suppliers = await this.apiCall('/api/suppliers');
            this.populateSupplierDropdowns();
        } catch (error) {
            console.error('Failed to load suppliers:', error);
        }
    }

    async loadCustomers() {
        try {
            this.customers = await this.apiCall('/api/customers');
            this.displayCustomers();
        } catch (error) {
            console.error('Failed to load customers:', error);
        }
    }

    async loadDashboardStats() {
        try {
            const stats = await this.apiCall('/api/dashboard/stats');
            this.updateDashboardStats(stats);
        } catch (error) {
            console.error('Failed to load dashboard stats:', error);
        }
    }

    // Display Methods
    displayProducts(products = this.products) {
        const container = document.getElementById('productsGrid');
        
        if (!products.length) {
            container.innerHTML = `
                <div class="loading-spinner">
                    <i class="fas fa-box-open" style="font-size: 48px; opacity: 0.3;"></i>
                    <p>No products found</p>
                </div>
            `;
            return;
        }

        container.innerHTML = products.map(product => `
            <div class="product-card" data-product-id="${product.id}" onclick="billing.selectProduct(${product.id})">
                <div class="product-image">
                    ${product.image_url ? 
                        `<img src="${product.image_url}" alt="${product.name}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 6px;">` :
                        `<i class="fas fa-cube"></i>`
                    }
                </div>
                <div class="product-name" title="${product.name}">${product.name}</div>
                <div class="product-price">₹${product.selling_price.toLocaleString('en-IN', {minimumFractionDigits: 2})}</div>
                <div class="product-stock ${product.current_stock <= product.minimum_stock ? 'low' : ''}">
                    Stock: ${product.current_stock}
                    ${product.current_stock <= product.minimum_stock ? '<i class="fas fa-exclamation-triangle"></i>' : ''}
                </div>
                ${product.discount_percent > 0 ? `<div class="product-discount">${product.discount_percent}% OFF</div>` : ''}
            </div>
        `).join('');
    }

    displayCustomers() {
        const container = document.getElementById('customersGrid');
        
        if (!this.customers.length) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-users" style="font-size: 48px; opacity: 0.3;"></i>
                    <p>No customers found</p>
                    <button class="btn-primary" onclick="billing.openCustomerModal()">
                        <i class="fas fa-plus"></i> Add First Customer
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = this.customers.map(customer => `
            <div class="customer-card">
                <div class="customer-header">
                    <div class="customer-avatar">
                        <i class="fas fa-user-circle"></i>
                    </div>
                    <div class="customer-info">
                        <h4>${customer.name}</h4>
                        <p>${customer.phone}</p>
                        <div class="customer-tier tier-${customer.tier}">
                            <i class="fas fa-crown"></i>
                            ${customer.tier.charAt(0).toUpperCase() + customer.tier.slice(1)}
                        </div>
                    </div>
                </div>
                <div class="customer-stats">
                    <div class="stat">
                        <span class="stat-value">₹${customer.total_spent.toLocaleString('en-IN')}</span>
                        <span class="stat-label">Total Spent</span>
                    </div>
                    <div class="stat">
                        <span class="stat-value">${customer.total_orders}</span>
                        <span class="stat-label">Orders</span>
                    </div>
                    <div class="stat">
                        <span class="stat-value">${customer.loyalty_points}</span>
                        <span class="stat-label">Points</span>
                    </div>
                </div>
                <div class="customer-actions">
                    <button class="btn-secondary btn-sm" onclick="billing.editCustomer(${customer.id})">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn-secondary btn-sm" onclick="billing.viewCustomerHistory(${customer.id})">
                        <i class="fas fa-history"></i> History
                    </button>
                </div>
            </div>
        `).join('');
    }

    populateCategoryDropdowns() {
        const selects = ['categoryFilter', 'productFormCategory'];
        
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                const currentValue = select.value;
                select.innerHTML = '<option value="">Select Category</option>' +
                    this.categories.map(cat => `<option value="${cat.id}">${cat.name}</option>`).join('');
                if (currentValue) select.value = currentValue;
            }
        });

        // Update filter buttons
        const filterContainer = document.querySelector('.category-filters');
        if (filterContainer) {
            const activeCategory = filterContainer.querySelector('.filter-btn.active')?.dataset.category || '';
            filterContainer.innerHTML = `
                <button class="filter-btn ${!activeCategory ? 'active' : ''}" data-category="" onclick="billing.filterByCategory('')">All</button>
                ${this.categories.slice(0, 6).map(cat => `
                    <button class="filter-btn ${activeCategory === cat.id.toString() ? 'active' : ''}" 
                            data-category="${cat.id}" onclick="billing.filterByCategory('${cat.id}')">${cat.name}</button>
                `).join('')}
            `;
        }
    }

    populateSupplierDropdowns() {
        const selects = ['supplierFilter', 'productFormSupplier'];
        
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                const currentValue = select.value;
                select.innerHTML = '<option value="">Select Supplier</option>' +
                    this.suppliers.map(sup => `<option value="${sup.id}">${sup.name}</option>`).join('');
                if (currentValue) select.value = currentValue;
            }
        });
    }

    updateDashboardStats(stats) {
        // Update header stats
        document.getElementById('todayRevenue').textContent = `₹${stats.today.today_revenue.toLocaleString('en-IN')}`;
        document.getElementById('todayOrders').textContent = stats.today.today_bills;

        // Update analytics stats
        if (document.getElementById('totalRevenue')) {
            document.getElementById('totalRevenue').textContent = `₹${stats.today.today_revenue.toLocaleString('en-IN')}`;
            document.getElementById('totalOrders').textContent = stats.today.today_bills;
            document.getElementById('totalCustomers').textContent = stats.customers.total_customers;
            document.getElementById('totalProducts').textContent = stats.products.total_products;
        }
    }

    updateProductStats() {
        const totalProducts = this.products.length;
        const lowStockCount = this.products.filter(p => p.current_stock <= p.minimum_stock).length;
        const outOfStockCount = this.products.filter(p => p.current_stock === 0).length;

        // Update any product stats displays
        const statsElements = document.querySelectorAll('.product-stats');
        statsElements.forEach(element => {
            element.innerHTML = `
                <span class="stat-item">
                    <i class="fas fa-boxes"></i>
                    <span>${totalProducts}</span> Total
                </span>
                ${lowStockCount > 0 ? `
                    <span class="stat-item warning">
                        <i class="fas fa-exclamation-triangle"></i>
                        <span>${lowStockCount}</span> Low Stock
                    </span>
                ` : ''}
                ${outOfStockCount > 0 ? `
                    <span class="stat-item error">
                        <i class="fas fa-times-circle"></i>
                        <span>${outOfStockCount}</span> Out of Stock
                    </span>
                ` : ''}
            `;
        });
    }

    // Product Management
    selectProduct(productId) {
        // Clear previous selection
        document.querySelectorAll('.product-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        const product = this.products.find(p => p.id === productId);
        if (!product) {
            this.showNotification('Product Error', 'error', 'Product not found');
            return;
        }

        if (product.current_stock <= 0) {
            this.showNotification('Out of Stock', 'warning', 'This product is currently out of stock');
            return;
        }

        // Highlight selected product
        const productCard = document.querySelector(`[data-product-id="${productId}"]`);
        if (productCard) {
            productCard.classList.add('selected');
        }

        // Add to cart
        this.addToCart(product, 1);
    }

    addToCart(product, quantity = 1) {
        const existingItem = this.cart.find(item => item.product_id === product.id);
        
        if (existingItem) {
            const newQuantity = existingItem.quantity + quantity;
            if (newQuantity > product.current_stock) {
                this.showNotification('Stock Limit', 'warning', `Only ${product.current_stock} units available`);
                return;
            }
            existingItem.quantity = newQuantity;
            existingItem.line_total = existingItem.unit_price * newQuantity;
        } else {
            if (quantity > product.current_stock) {
                this.showNotification('Stock Limit', 'warning', `Only ${product.current_stock} units available`);
                return;
            }
            
            this.cart.push({
                product_id: product.id,
                name: product.name,
                sku: product.sku,
                unit_price: product.selling_price,
                cost_price: product.cost_price,
                quantity: quantity,
                discount_percent: 0,
                discount_amount: 0,
                tax_rate: 18,
                tax_amount: (product.selling_price * quantity * 18) / 100,
                line_total: product.selling_price * quantity,
                profit_amount: (product.selling_price - product.cost_price) * quantity,
                stock_available: product.current_stock
            });
        }

        this.updateCartDisplay();
        this.calculateTotals();
        this.showNotification('Added to Cart', 'success', `${product.name} added to cart`);
    }

    updateCartDisplay() {
        const container = document.getElementById('cartItems');
        const cartCount = document.getElementById('cartCount');
        
        const itemCount = this.cart.length;
        const totalQuantity = this.cart.reduce((sum, item) => sum + item.quantity, 0);
        
        cartCount.textContent = itemCount === 0 ? '0 items' : 
            `${itemCount} item${itemCount > 1 ? 's' : ''} (${totalQuantity} qty)`;

        if (this.cart.length === 0) {
            container.innerHTML = `
                <div class="empty-cart">
                    <i class="fas fa-shopping-cart"></i>
                    <p>Cart is empty</p>
                    <small>Add products to start billing</small>
                </div>
            `;
            return;
        }

        container.innerHTML = this.cart.map((item, index) => `
            <div class="cart-item">
                <div class="cart-item-info">
                    <div class="cart-item-name" title="${item.name}">${item.name}</div>
                    <div class="cart-item-price">₹${item.unit_price.toFixed(2)} each</div>
                    <div class="cart-item-sku">${item.sku || 'N/A'}</div>
                </div>
                <div class="quantity-controls">
                    <button class="qty-btn" onclick="billing.updateCartQuantity(${index}, ${item.quantity - 1})">
                        <i class="fas fa-minus"></i>
                    </button>
                    <input type="number" class="qty-input" value="${item.quantity}" 
                           min="1" max="${item.stock_available}"
                           onchange="billing.updateCartQuantity(${index}, parseInt(this.value) || 1)">
                    <button class="qty-btn" onclick="billing.updateCartQuantity(${index}, ${item.quantity + 1})">
                        <i class="fas fa-plus"></i>
                    </button>
                </div>
                <div class="cart-item-total">₹${item.line_total.toFixed(2)}</div>
                <button class="qty-btn btn-remove" onclick="billing.removeFromCart(${index})" title="Remove Item">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `).join('');
    }

    updateCartQuantity(index, newQuantity) {
        if (newQuantity <= 0) {
            this.removeFromCart(index);
            return;
        }

        const item = this.cart[index];
        if (newQuantity > item.stock_available) {
            this.showNotification('Stock Limit', 'warning', `Only ${item.stock_available} units available`);
            return;
        }

        item.quantity = newQuantity;
        item.line_total = item.unit_price * newQuantity;
        item.tax_amount = (item.line_total * item.tax_rate) / 100;
        item.profit_amount = (item.unit_price - item.cost_price) * newQuantity;
        
        this.updateCartDisplay();
        this.calculateTotals();
    }

    removeFromCart(index) {
        const item = this.cart[index];
        this.cart.splice(index, 1);
        
        // Clear selection if this was the selected product
        const productCard = document.querySelector(`[data-product-id="${item.product_id}"]`);
        if (productCard) {
            productCard.classList.remove('selected');
        }
        
        this.updateCartDisplay();
        this.calculateTotals();
        this.showNotification('Removed', 'info', `${item.name} removed from cart`);
    }

    clearCart() {
        if (this.cart.length === 0) {
            this.showNotification('Empty Cart', 'info', 'Cart is already empty');
            return;
        }

        this.cart = [];
        
        // Clear all product selections
        document.querySelectorAll('.product-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        this.updateCartDisplay();
        this.calculateTotals();
        this.showNotification('Cart Cleared', 'info', 'All items removed from cart');
    }

    // Customer Management
    async searchCustomer() {
        const phone = document.getElementById('customerPhone').value.trim();
        
        if (!phone || !/^\d{10}$/.test(phone)) {
            this.clearCustomerDisplay();
            if (phone && phone.length > 0) {
                this.showNotification('Invalid Phone', 'warning', 'Please enter a valid 10-digit phone number');
            }
            return;
        }

        try {
            this.showLoading('Searching customer...');
            const customer = await this.apiCall(`/api/customers?phone=${phone}`);
            
            if (customer && !customer.error) {
                this.currentCustomer = customer;
                this.displayCustomerDetails(customer);
                this.showNotification('Customer Found', 'success', `Welcome back, ${customer.name}!`);
            } else {
                this.clearCustomerDisplay();
                this.showNotification('New Customer', 'info', 'Customer not found. Click "New" to create account.');
            }
        } catch (error) {
            this.clearCustomerDisplay();
            console.error('Customer search failed:', error);
        } finally {
            this.hideLoading();
        }
    }

    displayCustomerDetails(customer) {
        const detailsContainer = document.getElementById('customerDetails');
        
        // Update customer info
        document.getElementById('customerName').textContent = customer.name;
        document.getElementById('customerEmail').textContent = customer.email || 'No email provided';
        document.getElementById('customerOrders').textContent = customer.total_orders || 0;
        document.getElementById('customerPoints').textContent = customer.loyalty_points || 0;
        
        // Update loyalty tier
        const tierElement = document.getElementById('loyaltyTier');
        const tierName = document.getElementById('tierName');
        
        tierElement.className = `loyalty-tier tier-${customer.tier}`;
        tierName.textContent = customer.tier.charAt(0).toUpperCase() + customer.tier.slice(1);
        
        // Configure points slider
        const pointsSlider = document.getElementById('pointsSlider');
        const maxPoints = document.getElementById('maxPoints');
        
        const maxUsablePoints = Math.min(customer.loyalty_points, Math.floor(this.getSubtotal() * 0.5)); // Max 50% of bill
        pointsSlider.max = maxUsablePoints;
        pointsSlider.value = 0;
        maxPoints.textContent = maxUsablePoints;
        
        this.loyaltyPointsToUse = 0;
        document.getElementById('selectedPoints').textContent = '0';
        
        // Show customer details
        detailsContainer.style.display = 'block';
        
        // Recalculate totals
        this.calculateTotals();
    }

    clearCustomerDisplay() {
        this.currentCustomer = null;
        this.loyaltyPointsToUse = 0;
        document.getElementById('customerDetails').style.display = 'none';
        this.calculateTotals();
    }

    // Coupon Management
    async applyCoupon() {
        const couponCode = document.getElementById('couponCode').value.trim().toUpperCase();
        
        if (!couponCode) {
            this.showNotification('Invalid Input', 'warning', 'Please enter a coupon code');
            return;
        }

        if (this.cart.length === 0) {
            this.showNotification('Empty Cart', 'warning', 'Add items to cart before applying coupon');
            return;
        }

        try {
            this.showLoading('Validating coupon...');
            
            const validationData = {
                code: couponCode,
                amount: this.getSubtotal(),
                customer_tier: this.currentCustomer?.tier || 'bronze',
                customer_id: this.currentCustomer?.id || null,
                category_ids: [...new Set(this.cart.map(item => {
                    const product = this.products.find(p => p.id === item.product_id);
                    return product?.category_id;
                }).filter(Boolean))]
            };

            const result = await this.apiCall('/api/coupons/validate', {
                method: 'POST',
                body: JSON.stringify(validationData)
            });

            if (result.valid) {
                this.appliedCoupon = {
                    ...result.coupon,
                    calculated_discount: result.discount
                };
                
                document.getElementById('couponCode').style.borderColor = 'var(--success-color)';
                this.showAppliedCoupon(couponCode, result.discount);
                this.calculateTotals();
                this.showNotification('Coupon Applied!', 'success', 
                    `${couponCode} applied. You saved ₹${result.discount.toFixed(2)}`);
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            document.getElementById('couponCode').style.borderColor = 'var(--error-color)';
            this.showNotification('Invalid Coupon', 'error', error.message);
        } finally {
            this.hideLoading();
        }
    }

    showAppliedCoupon(code, discount) {
        const appliedCouponDiv = document.getElementById('appliedCoupon');
        document.getElementById('appliedCouponCode').textContent = code;
        document.getElementById('appliedCouponDiscount').textContent = `₹${discount.toFixed(2)} off`;
        appliedCouponDiv.style.display = 'flex';
    }

    removeCoupon() {
        this.appliedCoupon = null;
        document.getElementById('couponCode').value = '';
        document.getElementById('couponCode').style.borderColor = '';
        document.getElementById('appliedCoupon').style.display = 'none';
        this.calculateTotals();
        this.showNotification('Coupon Removed', 'info', 'Coupon discount removed');
    }

    async showAvailableCoupons() {
        try {
            this.showLoading('Loading available coupons...');
            
            const subtotal = this.getSubtotal();
            const customerTier = this.currentCustomer?.tier || 'bronze';
            
            // Load all coupons
            const allCoupons = await this.apiCall('/api/coupons');
            
            // Filter applicable coupons
            const applicableCoupons = allCoupons.filter(coupon => {
                // Check minimum amount
                if (subtotal < coupon.min_purchase_amount) return false;
                
                // Check tier eligibility
                if (coupon.applicable_customer_tiers && 
                    !coupon.applicable_customer_tiers.includes(customerTier)) return false;
                
                // Check if still usable
                if (coupon.used_count >= coupon.usage_limit) return false;
                
                return true;
            });

            this.displayCouponsModal(applicableCoupons, subtotal);
            document.getElementById('couponsModal').style.display = 'block';
            
        } catch (error) {
            this.showNotification('Load Error', 'error', 'Failed to load coupons');
        } finally {
            this.hideLoading();
        }
    }

    displayCouponsModal(coupons, subtotal) {
        const container = document.getElementById('couponsList');
        
        if (coupons.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-ticket-alt" style="font-size: 48px; opacity: 0.3;"></i>
                    <p>No applicable coupons</p>
                    <small>Add more items or upgrade your membership for better offers</small>
                </div>
            `;
            return;
        }

        container.innerHTML = coupons.map(coupon => {
            // Calculate potential discount
            let discount = 0;
            if (coupon.discount_type === 'percentage') {
                discount = Math.min((subtotal * coupon.discount_value) / 100, coupon.max_discount_amount);
            } else {
                discount = Math.min(coupon.discount_value, subtotal);
            }

            return `
                <div class="coupon-card-modal" onclick="billing.applyCouponFromModal('${coupon.code}')">
                    <div class="coupon-header-modal">
                        <div class="coupon-code-modal">${coupon.code}</div>
                        <div class="coupon-discount-modal">
                            ${coupon.discount_value}${coupon.discount_type === 'percentage' ? '%' : '₹'} OFF
                        </div>
                    </div>
                    <div class="coupon-description-modal">${coupon.description}</div>
                    <div class="coupon-details-modal">
                        <div>Min. purchase: ₹${coupon.min_purchase_amount.toLocaleString('en-IN')}</div>
                        <div>Max. discount: ₹${coupon.max_discount_amount.toLocaleString('en-IN')}</div>
                        <div>Valid until: ${new Date(coupon.valid_until).toLocaleDateString('en-IN')}</div>
                        <div style="color: #fbbf24; font-weight: bold;">You'll save: ₹${discount.toFixed(2)}</div>
                    </div>
                    <button class="coupon-apply-modal" onclick="event.stopPropagation(); billing.applyCouponFromModal('${coupon.code}')">
                        Apply Coupon
                    </button>
                </div>
            `;
        }).join('');
    }

    applyCouponFromModal(code) {
        document.getElementById('couponCode').value = code;
        this.closeCouponsModal();
        this.applyCoupon();
    }

    closeCouponsModal() {
        document.getElementById('couponsModal').style.display = 'none';
    }

    // Calculation Methods
    getSubtotal() {
        return this.cart.reduce((sum, item) => sum + item.line_total, 0);
    }

    calculateTotals() {
        const subtotal = this.getSubtotal();
        
        // Update subtotal display
        document.getElementById('subtotal').textContent = `₹${subtotal.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;

        if (subtotal === 0) {
            this.resetTotalsDisplay();
            return;
        }

        // Manual discount
        const manualDiscountPercent = parseFloat(document.getElementById('manualDiscount').value) || 0;
        const manualDiscount = (subtotal * manualDiscountPercent) / 100;

        // Coupon discount
        const couponDiscount = this.appliedCoupon ? this.appliedCoupon.calculated_discount : 0;

        // Loyalty points discount
        const loyaltyDiscount = this.loyaltyPointsToUse;

        // Use best discount (manual vs coupon)
        const bestDiscount = Math.max(manualDiscount, couponDiscount);
        const totalDiscount = bestDiscount + loyaltyDiscount;
        
        // Calculate tax on discounted amount
        const discountedAmount = Math.max(0, subtotal - totalDiscount);
        const tax = discountedAmount * 0.18; // 18% GST
        const netAmount = discountedAmount + tax;

        // Update displays
        this.updateDiscountDisplays(manualDiscount, couponDiscount, loyaltyDiscount);
        
        document.getElementById('taxAmount').textContent = `₹${tax.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
        document.getElementById('netAmount').textContent = `₹${netAmount.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;

        // Calculate loyalty points to earn
        if (this.currentCustomer) {
            const pointsToEarn = Math.floor(netAmount / 100); // 1 point per ₹100
            document.getElementById('pointsToEarn').textContent = pointsToEarn;
            document.getElementById('loyaltyEarning').style.display = pointsToEarn > 0 ? 'flex' : 'none';
        } else {
            document.getElementById('loyaltyEarning').style.display = 'none';
        }

        // Enable/disable generate button
        const hasItems = this.cart.length > 0;
        const hasValidCustomer = this.currentCustomer || (
            document.getElementById('customerPhone').value.trim().length === 10
        );
        
        document.getElementById('generateBillBtn').disabled = !(hasItems && hasValidCustomer);

        // Update loyalty points slider if customer exists
        if (this.currentCustomer) {
            const pointsSlider = document.getElementById('pointsSlider');
            const maxUsablePoints = Math.min(this.currentCustomer.loyalty_points, Math.floor(subtotal * 0.5));
            pointsSlider.max = maxUsablePoints;
            document.getElementById('maxPoints').textContent = maxUsablePoints;
            
            // Reset if current selection exceeds new maximum
            if (this.loyaltyPointsToUse > maxUsablePoints) {
                this.loyaltyPointsToUse = maxUsablePoints;
                pointsSlider.value = maxUsablePoints;
                document.getElementById('selectedPoints').textContent = maxUsablePoints;
            }
        }
    }

    updateDiscountDisplays(manual, coupon, loyalty) {
        // Manual or coupon discount (show better one)
        const discountLine = document.getElementById('discountLine');
        const bestDiscount = Math.max(manual, coupon);
        
        if (bestDiscount > 0) {
            discountLine.style.display = 'flex';
            const discountType = manual > coupon ? 'Manual' : 'Coupon';
            document.getElementById('discountAmount').textContent = `-₹${bestDiscount.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
            discountLine.querySelector('span').textContent = `${discountType} Discount`;
        } else {
            discountLine.style.display = 'none';
        }

        // Loyalty points discount
        const loyaltyLine = document.getElementById('loyaltyLine');
        if (loyalty > 0) {
            loyaltyLine.style.display = 'flex';
            document.getElementById('loyaltyAmount').textContent = `-₹${loyalty.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
        } else {
            loyaltyLine.style.display = 'none';
        }
    }

    resetTotalsDisplay() {
        ['discountLine', 'loyaltyLine', 'loyaltyEarning'].forEach(id => {
            document.getElementById(id).style.display = 'none';
        });
        
        document.getElementById('taxAmount').textContent = '₹0.00';
        document.getElementById('netAmount').textContent = '₹0.00';
        document.getElementById('generateBillBtn').disabled = true;
    }

    // Bill Generation
    async generateBill() {
        const phone = document.getElementById('customerPhone').value.trim();

        if (this.cart.length === 0) {
            this.showNotification('Empty Cart', 'warning', 'Please add items to cart');
            return;
        }

        if (!this.currentCustomer && (!phone || !/^\d{10}$/.test(phone))) {
            this.showNotification('Customer Required', 'warning', 'Please enter customer phone number');
            return;
        }

        try {
            this.showLoading('Generating bill...');

            // Calculate all totals
            const subtotal = this.getSubtotal();
            const manualDiscountPercent = parseFloat(document.getElementById('manualDiscount').value) || 0;
            const manualDiscount = (subtotal * manualDiscountPercent) / 100;
            const couponDiscount = this.appliedCoupon ? this.appliedCoupon.calculated_discount : 0;
            const bestDiscount = Math.max(manualDiscount, couponDiscount);
            const totalDiscount = bestDiscount + this.loyaltyPointsToUse;
            const discountedAmount = Math.max(0, subtotal - totalDiscount);
            const tax = discountedAmount * 0.18;
            const netAmount = discountedAmount + tax;
            const pointsToEarn = this.currentCustomer ? Math.floor(netAmount / 100) : 0;

            // Prepare bill data
            const billData = {
                customer_id: this.currentCustomer?.id || null,
                cashier_name: 'POS User',
                subtotal: subtotal,
                total_discount: bestDiscount,
                loyalty_points_used: this.loyaltyPointsToUse,
                loyalty_discount: this.loyaltyPointsToUse,
                coupon_discount: couponDiscount,
                tax_amount: tax,
                round_off: 0,
                net_amount: netAmount,
                paid_amount: netAmount,
                change_amount: 0,
                payment_method: this.selectedPaymentMethod,
                coupon_code: this.appliedCoupon?.code || null,
                loyalty_points_earned: pointsToEarn,
                items: this.cart
            };

            // If no customer exists, create one with just phone
            if (!this.currentCustomer) {
                const customerData = {
                    name: `Customer ${phone}`,
                    phone: phone
                };

                try {
                    await this.apiCall('/api/customers', {
                        method: 'POST',
                        body: JSON.stringify(customerData)
                    });
                } catch (error) {
                    console.error('Failed to create customer:', error);
                }
            }

            // Create the bill
            const billResult = await this.apiCall('/api/bills', {
                method: 'POST',
                body: JSON.stringify(billData)
            });

            if (billResult.success) {
                this.currentBill = {
                    ...billData,
                    bill_number: billResult.bill_number,
                    bill_id: billResult.bill_id,
                    customer_phone: phone,
                    customer_name: this.currentCustomer?.name || `Customer ${phone}`
                };

                // Update bill number display
                document.getElementById('billNumber').textContent = billResult.bill_number;

                // Enable print button
                document.getElementById('printBillBtn').disabled = false;

                // Show bill preview or directly print
                this.showNotification('Bill Generated!', 'success', 
                    `Bill ${billResult.bill_number} generated successfully. Points earned: ${pointsToEarn}`);

                // Auto-print if enabled
                setTimeout(() => this.printBill(), 500);
            } else {
                throw new Error('Failed to generate bill');
            }

        } catch (error) {
            console.error('Bill generation failed:', error);
            this.showNotification('Bill Error', 'error', 'Failed to generate bill. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    printBill() {
        if (!this.currentBill) {
            this.showNotification('No Bill', 'warning', 'Please generate a bill first');
            return;
        }

        const printContent = this.generatePrintContent();
        
        const printWindow = window.open('', '_blank', 'width=800,height=600');
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Bill - ${this.currentBill.bill_number}</title>
                <style>
                    body { 
                        font-family: 'Courier New', monospace; 
                        margin: 0; 
                        padding: 20px; 
                        font-size: 14px; 
                        line-height: 1.4;
                    }
                    .header { 
                        text-align: center; 
                        margin-bottom: 20px; 
                        border-bottom: 2px solid #000; 
                        padding-bottom: 15px; 
                    }
                    .header h1 { 
                        margin: 0 0 5px 0; 
                        font-size: 24px; 
                    }
                    .bill-details { 
                        display: flex; 
                        justify-content: space-between; 
                        margin-bottom: 20px; 
                    }
                    .items-table { 
                        width: 100%; 
                        border-collapse: collapse; 
                        margin-bottom: 20px; 
                    }
                    .items-table th, 
                    .items-table td { 
                        padding: 8px; 
                        text-align: left; 
                        border-bottom: 1px solid #ddd; 
                    }
                    .items-table th { 
                        background: #f5f5f5; 
                        font-weight: bold; 
                    }
                    .totals { 
                        text-align: right; 
                        margin-top: 20px; 
                    }
                    .totals div { 
                        margin: 5px 0; 
                    }
                    .total-final { 
                        font-size: 18px; 
                        font-weight: bold; 
                        border-top: 2px solid #000; 
                        padding-top: 10px; 
                        margin-top: 10px; 
                    }
                    .footer { 
                        text-align: center; 
                        margin-top: 30px; 
                        padding-top: 20px; 
                        border-top: 1px dashed #666; 
                        font-size: 12px; 
                    }
                    @media print { 
                        body { margin: 0; padding: 10px; font-size: 12px; } 
                        .header h1 { font-size: 20px; }
                        .total-final { font-size: 16px; }
                    }
                </style>
            </head>
            <body>${printContent}</body>
            </html>
        `);
        
        printWindow.document.close();
        printWindow.focus();
        
        setTimeout(() => {
            printWindow.print();
            printWindow.close();
        }, 250);
        
        this.showNotification('Printing', 'info', 'Bill sent to printer');
        
        // Clear all after printing
        setTimeout(() => this.clearAll(), 2000);
    }

    generatePrintContent() {
        const bill = this.currentBill;
        const now = new Date();

        return `
            <div class="header">
                <h1>INVENTA AI GENE</h1>
                <div>Enhanced Retail Billing System</div>
                <div>📞 +91-9899459288 | 📧 info@inventaaigene.com</div>
                <div>Delhi-110053 | GST: 07AAACI5482L1ZY</div>
            </div>
            
            <div class="bill-details">
                <div>
                    <strong>BILL TO:</strong><br>
                    ${bill.customer_name}<br>
                    ${bill.customer_phone}<br>
                    ${this.currentCustomer?.email ? `${this.currentCustomer.email}<br>` : ''}
                </div>
                <div style="text-align: right;">
                    <strong>Bill No:</strong> ${bill.bill_number}<br>
                    <strong>Date:</strong> ${now.toLocaleDateString('en-IN')}<br>
                    <strong>Time:</strong> ${now.toLocaleTimeString('en-IN')}<br>
                    <strong>Payment:</strong> ${bill.payment_method.toUpperCase()}<br>
                    <strong>Cashier:</strong> ${bill.cashier_name}
                </div>
            </div>
            
            <table class="items-table">
                <thead>
                    <tr>
                        <th>ITEM</th>
                        <th style="text-align: center;">QTY</th>
                        <th style="text-align: right;">RATE</th>
                        <th style="text-align: right;">AMOUNT</th>
                    </tr>
                </thead>
                <tbody>
                    ${this.cart.map(item => `
                        <tr>
                            <td>
                                ${item.name}<br>
                                <small style="color: #666;">${item.sku || 'N/A'}</small>
                            </td>
                            <td style="text-align: center;">${item.quantity}</td>
                            <td style="text-align: right;">₹${item.unit_price.toFixed(2)}</td>
                            <td style="text-align: right;">₹${item.line_total.toFixed(2)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            
            <div class="totals">
                <div>Subtotal: ₹${bill.subtotal.toFixed(2)}</div>
                ${bill.total_discount > 0 ? `<div>Discount: -₹${bill.total_discount.toFixed(2)}</div>` : ''}
                ${bill.loyalty_discount > 0 ? `<div>Loyalty Points Used: -₹${bill.loyalty_discount.toFixed(2)}</div>` : ''}
                ${bill.coupon_code ? `<div>Coupon (${bill.coupon_code}): Applied</div>` : ''}
                <div>GST (18%): ₹${bill.tax_amount.toFixed(2)}</div>
                <div class="total-final">NET AMOUNT: ₹${bill.net_amount.toFixed(2)}</div>
                ${bill.loyalty_points_earned > 0 ? `<div style="margin-top: 10px; color: #666;">Loyalty Points Earned: ${bill.loyalty_points_earned}</div>` : ''}
            </div>
            
            <div class="footer">
                <div><strong>THANK YOU FOR YOUR BUSINESS!</strong></div>
                <div>Visit again for exciting offers and deals!</div>
                <div style="margin-top: 15px;">This is a computer generated invoice</div>
                <div>For support: info@inventaaigene.com</div>
            </div>
        `;
    }

    // Utility Functions
    clearAll() {
        // Reset all data
        this.cart = [];
        this.currentCustomer = null;
        this.currentBill = null;
        this.appliedCoupon = null;
        this.loyaltyPointsToUse = 0;
        this.selectedPaymentMethod = 'cash';

        // Clear form inputs
        document.getElementById('customerPhone').value = '';
        document.getElementById('couponCode').value = '';
        document.getElementById('manualDiscount').value = '0';
        
        // Clear displays
        this.clearCustomerDisplay();
        document.getElementById('appliedCoupon').style.display = 'none';
        document.getElementById('billNumber').textContent = 'Draft';
        
        // Reset button states
        document.getElementById('generateBillBtn').disabled = true;
        document.getElementById('printBillBtn').disabled = true;
        
        // Clear product selections
        document.querySelectorAll('.product-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Reset payment method
        document.querySelectorAll('.payment-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector('[data-method="cash"]').classList.add('active');

        this.updateCartDisplay();
        this.calculateTotals();
        
        this.showNotification('Ready', 'info', 'System ready for next transaction');
    }

    // Event Listeners Setup
    setupEventListeners() {
        // Product search
        const productSearch = document.getElementById('productSearch');
        let searchTimeout;
        
        productSearch?.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.loadProducts({ search: e.target.value.trim() });
            }, 300);
        });

        // Customer phone search
        const customerPhone = document.getElementById('customerPhone');
        customerPhone?.addEventListener('input', (e) => {
            clearTimeout(this.customerTimeout);
            this.customerTimeout = setTimeout(() => {
                if (e.target.value.length === 10) {
                    this.searchCustomer();
                } else if (e.target.value.length === 0) {
                    this.clearCustomerDisplay();
                }
            }, 500);
        });

        // Loyalty points slider
        const pointsSlider = document.getElementById('pointsSlider');
        pointsSlider?.addEventListener('input', (e) => {
            this.loyaltyPointsToUse = parseInt(e.target.value);
            document.getElementById('selectedPoints').textContent = this.loyaltyPointsToUse;
            this.calculateTotals();
        });

        // Manual discount
        const manualDiscount = document.getElementById('manualDiscount');
        manualDiscount?.addEventListener('input', () => {
            this.calculateTotals();
        });

        // Payment method selection
        document.querySelectorAll('.payment-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.payment-btn').forEach(b => b.classList.remove('active'));
                e.currentTarget.classList.add('active');
                this.selectedPaymentMethod = e.currentTarget.dataset.method;
            });
        });

        // Amount received for cash payments
        const amountReceived = document.getElementById('amountReceived');
        amountReceived?.addEventListener('input', () => {
            this.calculateChange();
        });

        // Form submissions
        const customerForm = document.getElementById('customerForm');
        customerForm?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveCustomer();
        });

        const productForm = document.getElementById('productForm');
        productForm?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveProduct();
        });

        // Modal close on outside click
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.style.display = 'none';
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.altKey) {
                switch (e.code) {
                    case 'KeyN':
                        e.preventDefault();
                        this.clearAll();
                        break;
                    case 'KeyP':
                        e.preventDefault();
                        if (!document.getElementById('printBillBtn').disabled) {
                            this.printBill();
                        }
                        break;
                    case 'KeyG':
                        e.preventDefault();
                        if (!document.getElementById('generateBillBtn').disabled) {
                            this.generateBill();
                        }
                        break;
                    case 'KeyC':
                        e.preventDefault();
                        document.getElementById('customerPhone').focus();
                        break;
                    case 'KeyS':
                        e.preventDefault();
                        document.getElementById('productSearch').focus();
                        break;
                }
            }
        });
    }

    // Modal and Form Management
    openCustomerModal() {
        document.getElementById('customerModalTitle').textContent = 'Add New Customer';
        document.getElementById('customerForm').reset();
        document.getElementById('customerModal').style.display = 'block';
    }

    closeCustomerModal() {
        document.getElementById('customerModal').style.display = 'none';
    }

    async saveCustomer() {
        const formData = {
            name: document.getElementById('customerFormName').value.trim(),
            phone: document.getElementById('customerFormPhone').value.trim(),
            email: document.getElementById('customerFormEmail').value.trim(),
            address: document.getElementById('customerFormAddress').value.trim(),
            city: document.getElementById('customerFormCity').value.trim(),
            date_of_birth: document.getElementById('customerFormDOB').value,
            gender: document.getElementById('customerFormGender').value,
            tags: document.getElementById('customerFormTags').value.trim(),
            referred_by: document.getElementById('customerFormReferral').value.trim()
        };

        if (!formData.name || !formData.phone) {
            this.showNotification('Missing Information', 'warning', 'Name and phone number are required');
            return;
        }

        if (!/^\d{10}$/.test(formData.phone)) {
            this.showNotification('Invalid Phone', 'warning', 'Please enter a valid 10-digit phone number');
            return;
        }

        try {
            this.showLoading('Saving customer...');
            
            const result = await this.apiCall('/api/customers', {
                method: 'POST',
                body: JSON.stringify(formData)
            });

            if (result.success) {
                this.closeCustomerModal();
                
                // Auto-populate customer phone in POS
                document.getElementById('customerPhone').value = formData.phone;
                this.searchCustomer();
                
                await this.loadCustomers(); // Refresh customer list
                
                this.showNotification('Customer Saved!', 'success', 
                    `${formData.name} added successfully. Welcome bonus: ${result.welcome_points} points!`);
            }
        } catch (error) {
            this.showNotification('Save Failed', 'error', 'Failed to save customer');
        } finally {
            this.hideLoading();
        }
    }

    openProductModal() {
        document.getElementById('productModalTitle').textContent = 'Add New Product';
        document.getElementById('productForm').reset();
        this.switchProductTab('basic');
        document.getElementById('productModal').style.display = 'block';
    }

    closeProductModal() {
        document.getElementById('productModal').style.display = 'none';
    }

    switchProductTab(tabName) {
        // Remove active from all tabs and panels
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));
        
        // Add active to selected tab and panel
        event.target?.classList.add('active');
        document.getElementById(`${tabName}-tab`)?.classList.add('active');
    }

    async saveProduct() {
        const formData = {
            product_id: document.getElementById('productFormId').value.trim(),
            sku: document.getElementById('productFormSKU').value.trim(),
            barcode: document.getElementById('productFormBarcode').value.trim(),
            name: document.getElementById('productFormName').value.trim(),
            description: document.getElementById('productFormDescription').value.trim(),
            category_id: document.getElementById('productFormCategory').value,
            supplier_id: document.getElementById('productFormSupplier').value,
            brand: document.getElementById('productFormBrand').value.trim(),
            model: document.getElementById('productFormModel').value.trim(),
            cost_price: document.getElementById('productFormCostPrice').value,
            selling_price: document.getElementById('productFormSellingPrice').value,
            mrp: document.getElementById('productFormMRP').value,
            discount_percent: document.getElementById('productFormDiscountPercent').value || 0,
            current_stock: document.getElementById('productFormCurrentStock').value,
            minimum_stock: document.getElementById('productFormMinStock').value || 5,
            maximum_stock: document.getElementById('productFormMaxStock').value || 1000,
            unit: document.getElementById('productFormUnit').value,
            weight: document.getElementById('productFormWeight').value,
            dimensions: document.getElementById('productFormDimensions').value.trim(),
            batch_number: document.getElementById('productFormBatchNumber').value.trim(),
            manufacturing_date: document.getElementById('productFormMfgDate').value,
            expiry_date: document.getElementById('productFormExpiryDate').value,
            warranty_period: document.getElementById('productFormWarranty').value || 0,
            hsn_code: document.getElementById('productFormHSN').value.trim(),
            tags: document.getElementById('productFormTags').value.trim(),
            image_url: document.getElementById('productFormImageURL').value.trim()
        };

        // Validate required fields
        const required = ['product_id', 'name', 'category_id', 'supplier_id', 'cost_price', 'selling_price', 'current_stock'];
        for (const field of required) {
            if (!formData[field]) {
                this.showNotification('Missing Information', 'warning', `${field.replace('_', ' ')} is required`);
                return;
            }
        }

        try {
            this.showLoading('Saving product...');
            
            const result = await this.apiCall('/api/products', {
                method: 'POST',
                body: JSON.stringify(formData)
            });

            if (result.success) {
                this.closeProductModal();
                await this.loadProducts(); // Refresh product list
                this.showNotification('Product Saved!', 'success', `${formData.name} added successfully`);
            }
        } catch (error) {
            this.showNotification('Save Failed', 'error', error.message || 'Failed to save product');
        } finally {
            this.hideLoading();
        }
    }

    // Filter and Search Methods
    filterByCategory(categoryId) {
        // Update active filter button
        document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[data-category="${categoryId}"]`)?.classList.add('active');
        
        // Load products with filter
        const filters = categoryId ? { category_id: categoryId } : {};
        this.loadProducts(filters);
    }

    clearSearch() {
        document.getElementById('productSearch').value = '';
        this.loadProducts();
    }

    calculateChange() {
        const netAmount = parseFloat(document.getElementById('netAmount').textContent.replace(/[₹,]/g, ''));
        const amountReceived = parseFloat(document.getElementById('amountReceived').value) || 0;
        const change = amountReceived - netAmount;
        
        const changeContainer = document.getElementById('changeAmount');
        const changeValue = document.getElementById('changeValue');
        
        if (change > 0) {
            changeContainer.style.display = 'flex';
            changeValue.textContent = `₹${change.toFixed(2)}`;
        } else {
            changeContainer.style.display = 'none';
        }
    }

    // Section Navigation
    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Show selected section
        document.getElementById(sectionName)?.classList.add('active');
        
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[onclick="showSection('${sectionName}')"]`)?.classList.add('active');
        
        this.currentSection = sectionName;
        
        // Load section-specific data
        if (sectionName === 'customers') {
            this.loadCustomers();
        } else if (sectionName === 'analytics') {
            this.loadAnalytics();
        }
    }

    async loadAnalytics() {
        try {
            this.showLoading('Loading analytics...');
            
            // Load AI recommendations
            const recommendations = await this.apiCall('/api/ai/recommendations');
            this.displayRecommendations(recommendations);
            
        } catch (error) {
            console.error('Failed to load analytics:', error);
        } finally {
            this.hideLoading();
        }
    }

    displayRecommendations(recommendations) {
        const container = document.getElementById('recommendationsList');
        
        if (!recommendations.length) {
            container.innerHTML = `
                <div class="no-recommendations">
                    <i class="fas fa-lightbulb"></i>
                    <p>No active recommendations</p>
                    <button class="btn-primary" onclick="billing.runAIAnalysis()">
                        <i class="fas fa-robot"></i> Run AI Analysis
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = recommendations.map(rec => `
            <div class="recommendation-item priority-${rec.priority}">
                <div class="recommendation-header">
                    <span class="recommendation-type">${rec.type.replace('_', ' ')}</span>
                    <span class="recommendation-priority">Priority: ${rec.priority}</span>
                </div>
                <div class="recommendation-message">${rec.message}</div>
                ${rec.product_name ? `<div class="recommendation-product">Product: ${rec.product_name}</div>` : ''}
                <div class="recommendation-actions">
                    <button class="btn-sm btn-primary" onclick="billing.handleRecommendation(${rec.id})">
                        Take Action
                    </button>
                    <button class="btn-sm btn-secondary" onclick="billing.dismissRecommendation(${rec.id})">
                        Dismiss
                    </button>
                </div>
            </div>
        `).join('');
    }

    async runAIAnalysis() {
        try {
            this.showLoading('Running AI analysis...');
            
            const result = await this.apiCall('/api/ai/analyze');
            
            if (result.success) {
                this.showNotification('AI Analysis Complete', 'success', 
                    `Generated ${result.recommendations_generated} recommendations`);
                this.loadAnalytics(); // Refresh recommendations
            }
        } catch (error) {
            this.showNotification('Analysis Failed', 'error', 'Failed to run AI analysis');
        } finally {
            this.hideLoading();
        }
    }

    // Calculator Methods
    openCalculator() {
        document.getElementById('calculatorModal').style.display = 'block';
        this.clearCalculator();
    }

    closeCalculator() {
        document.getElementById('calculatorModal').style.display = 'none';
    }

    appendToCalculator(value) {
        const display = document.getElementById('calculatorDisplay');
        if (display.value === '0' && !isNaN(value)) {
            display.value = value;
        } else {
            display.value += value;
        }
    }

    clearCalculator() {
        document.getElementById('calculatorDisplay').value = '0';
        this.calculatorValue = '';
        this.calculatorOperator = '';
        this.calculatorPreviousValue = '';
    }

    clearEntry() {
        document.getElementById('calculatorDisplay').value = '0';
    }

    calculate() {
        const display = document.getElementById('calculatorDisplay');
        try {
            const result = eval(display.value.replace('×', '*'));
            display.value = result;
        } catch (error) {
            display.value = 'Error';
        }
    }

    // UI Helper Functions
    updateDateTime() {
        const now = new Date();
        const options = {
            weekday: 'short',
            day: 'numeric',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        };
        
        document.getElementById('currentDateTime').textContent = now.toLocaleDateString('en-IN', options);
        setTimeout(() => this.updateDateTime(), 1000);
    }

    showNotification(title, type, message) {
        const container = document.getElementById('notificationContainer');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        notification.innerHTML = `
            <i class="notification-icon ${icons[type]}"></i>
            <div class="notification-content">
                <div class="notification-title">${title}</div>
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;

        container.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    showLoading(message = 'Loading...') {
        document.getElementById('loadingMessage').textContent = message;
        document.getElementById('loadingOverlay').style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loadingOverlay').style.display = 'none';
    }

    // Tab switching for discount panel
    switchDiscountTab(tabName) {
        document.querySelectorAll('.discount-tabs .tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.discount-tab-panel').forEach(panel => panel.classList.remove('active'));
        
        event.target.classList.add('active');
        document.getElementById(`${tabName}-discount`).classList.add('active');
    }

    // Payment method selection
    selectPaymentMethod(method) {
        document.querySelectorAll('.payment-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[data-method="${method}"]`).classList.add('active');
        this.selectedPaymentMethod = method;
        
        // Show/hide payment details based on method
        const cashDetails = document.getElementById('cashPaymentDetails');
        if (method === 'cash') {
            cashDetails.style.display = 'block';
        } else {
            cashDetails.style.display = 'none';
        }
    }

    // Utility methods for fullscreen, etc.
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    }
}

// Initialize the billing system
let billing;

document.addEventListener('DOMContentLoaded', () => {
    billing = new EnhancedBillingSystem();
});

// Global function bindings for HTML onclick events
function showSection(section) { billing.showSection(section); }
function clearSearch() { billing.clearSearch(); }
function openCustomerModal() { billing.openCustomerModal(); }
function closeCustomerModal() { billing.closeCustomerModal(); }
function searchCustomer() { billing.searchCustomer(); }
function applyCoupon() { billing.applyCoupon(); }
function removeCoupon() { billing.removeCoupon(); }
function showAvailableCoupons() { billing.showAvailableCoupons(); }
function closeCouponsModal() { billing.closeCouponsModal(); }
function generateBill() { billing.generateBill(); }
function printBill() { billing.printBill(); }
function clearCart() { billing.clearCart(); }
function clearAll() { billing.clearAll(); }
function calculateChange() { billing.calculateChange(); }
function openProductModal() { billing.openProductModal(); }
function closeProductModal() { billing.closeProductModal(); }
function switchProductTab(tab) { billing.switchProductTab(tab); }
function filterByCategory(id) { billing.filterByCategory(id); }
function switchDiscountTab(tab) { billing.switchDiscountTab(tab); }
function selectPaymentMethod(method) { billing.selectPaymentMethod(method); }
function openCalculator() { billing.openCalculator(); }
function closeCalculator() { billing.closeCalculator(); }
function appendToCalculator(value) { billing.appendToCalculator(value); }
function clearCalculator() { billing.clearCalculator(); }
function clearEntry() { billing.clearEntry(); }
function calculate() { billing.calculate(); }
function runAIAnalysis() { billing.runAIAnalysis(); }
function toggleFullscreen() { billing.toggleFullscreen(); }

// Additional utility functions
function holdBill() {
    billing.showNotification('Feature Coming Soon', 'info', 'Bill hold feature will be available in next update');
}

function exportProducts() {
    billing.showNotification('Feature Coming Soon', 'info', 'Export functionality will be available soon');
}

function exportCustomers() {
    billing.showNotification('Feature Coming Soon', 'info', 'Export functionality will be available soon');
}

function filterProducts() {
    const search = document.getElementById('productSearchFilter').value;
    const category = document.getElementById('categoryFilter').value;
    const supplier = document.getElementById('supplierFilter').value;
    
    const filters = {};
    if (search) filters.search = search;
    if (category) filters.category_id = category;
    if (supplier) filters.supplier_id = supplier;
    
    billing.loadProducts(filters);
}

function setProductsView(view) {
    document.querySelectorAll('.view-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // View switching logic can be implemented here
    billing.showNotification('View Changed', 'info', `Switched to ${view} view`);
}

// Keyboard shortcuts helper
document.addEventListener('keydown', (e) => {
    // Show shortcuts help with F1
    if (e.key === 'F1') {
        e.preventDefault();
        billing.showNotification('Keyboard Shortcuts', 'info', 
            'Alt+N: New Transaction | Alt+P: Print | Alt+G: Generate Bill | Alt+C: Customer Search | Alt+S: Product Search');
    }
});

console.log('🚀 Enhanced Retail Billing System - JavaScript Loaded');
