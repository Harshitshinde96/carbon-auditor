// Replace this with your actual API Gateway URL
const API_BASE_URL = 'https://jddd2cy8of.execute-api.ap-south-1.amazonaws.com/dev';

// Generic fetch wrapper to handle API calls with mock fallback support
const API = {
    async get(endpoint, mockFile) {
        try {
            // Support both real endpoints and mock endpoints depending on how it's called
            const url = endpoint.includes('mock') || endpoint.includes('.json') ? endpoint : `${API_BASE_URL}/api/v1/${endpoint}`;
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error("API Get Error:", error);
            if (mockFile) {
                console.warn(`Falling back to mock file: ${mockFile}`);
                const res = await fetch(mockFile);
                return await res.json();
            }
            throw error;
        }
    },
    
    async post(endpoint, data, mockFile) {
        try {
            const url = endpoint.includes('mock') ? endpoint : `${API_BASE_URL}/api/v1/${endpoint}`;
            const options = {
                method: 'POST',
                body: data instanceof FormData ? data : JSON.stringify(data)
            };
            if (!(data instanceof FormData)) {
                options.headers = { 'Content-Type': 'application/json' };
            }
            const response = await fetch(url, options);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error("API Post Error:", error);
            if (mockFile) {
                return { success: true, message: "Mock POST success", data: data };
            }
            throw error;
        }
    }
};

// DOM Utilities
const DOM = {
    el: (selector) => document.querySelector(selector),
    all: (selector) => document.querySelectorAll(selector),
    create: (tag, classes = "", html = "") => {
        const el = document.createElement(tag);
        if (classes) el.className = classes;
        if (html) el.innerHTML = html;
        return el;
    },
    formatCurrency: (amount, currency = 'USD') => {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount);
    },
    formatDate: (dateString) => {
        if (!dateString) return "N/A";
        const options = { year: 'numeric', month: 'short', day: 'numeric' };
        return new Date(dateString).toLocaleDateString('en-US', options);
    },
    formatNumber: (num) => {
        return new Intl.NumberFormat('en-US').format(num);
    }
};
