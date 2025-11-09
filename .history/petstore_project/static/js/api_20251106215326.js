// API Utility Functions
class PetStoreAPI {
    static baseURL = '/api';
    
    static async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
            },
            ...options
        };
        
        // Add auth token if available
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        
        try {
            const response = await fetch(url, config);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
    
    // Auth methods
    static async login(username, password) {
        return this.request('/auth/token/', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
    }
    
    static async register(userData) {
        return this.request('/auth/users/register/', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    }
    
    // Pet methods
    static async getPets(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/pets/pets/${queryString ? '?' + queryString : ''}`);
    }
    
    static async getPet(id) {
        return this.request(`/pets/pets/${id}/`);
    }
    
    static async getCategories() {
        return this.request('/pets/categories/');
    }
    
    // Order methods
    static async createOrder(orderData) {
        return this.request('/orders/orders/', {
            method: 'POST',
            body: JSON.stringify(orderData)
        });
    }
    
    static async getOrders() {
        return this.request('/orders/orders/');
    }
}

// Cart management
class CartManager {
    static getCart() {
        return JSON.parse(localStorage.getItem('cart') || '[]');
    }
    
    static addToCart(petId, quantity = 1) {
        const cart = this.getCart();
        const existingItem = cart.find(item => item.petId === petId);
        
        if (existingItem) {
            existingItem.quantity += quantity;
        } else {
            cart.push({ petId, quantity });
        }
        
        localStorage.setItem('cart', JSON.stringify(cart));
        this.updateCartCount();
    }
    
    static removeFromCart(petId) {
        const cart = this.getCart().filter(item => item.petId !== petId);
        localStorage.setItem('cart', JSON.stringify(cart));
        this.updateCartCount();
    }
    
    static updateCartCount() {
        const cart = this.getCart();
        const count = cart.reduce((total, item) => total + item.quantity, 0);
        
        const cartBadge = document.getElementById('cart-count');
        if (cartBadge) {
            cartBadge.textContent = count;
            cartBadge.style.display = count > 0 ? 'inline' : 'none';
        }
    }
    
    static clearCart() {
        localStorage.removeItem('cart');
        this.updateCartCount();
    }
}

// Initialize cart count on page load
document.addEventListener('DOMContentLoaded', function() {
    CartManager.updateCartCount();
});