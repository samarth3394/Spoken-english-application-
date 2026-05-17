/**
 * Aspire English Hub - API Client Module
 * ========================================
 * Centralized API communication layer.
 */

const API = (() => {
    const BASE_URL = window.APP_CONFIG?.API_URL || 'http://localhost:8000';

    function getToken() {
        return localStorage.getItem('access_token');
    }

    function setTokens(access, refresh) {
        localStorage.setItem('access_token', access);
        if (refresh) localStorage.setItem('refresh_token', refresh);
    }

    function clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
    }

    async function request(endpoint, options = {}) {
        const url = `${BASE_URL}${endpoint}`;
        const headers = { 'Content-Type': 'application/json', ...options.headers };
        const token = getToken();
        if (token) headers['Authorization'] = `Bearer ${token}`;

        try {
            const response = await fetch(url, { ...options, headers });

            if (response.status === 401) {
                const refreshed = await refreshToken();
                if (refreshed) {
                    headers['Authorization'] = `Bearer ${getToken()}`;
                    const retry = await fetch(url, { ...options, headers });
                    if (!retry.ok) throw new Error(`HTTP ${retry.status}`);
                    return retry.json();
                }
                clearTokens();
                window.location.href = '/pages/login.html';
                return null;
            }

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.detail || `HTTP ${response.status}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType?.includes('audio')) return response.blob();
            return response.json();
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    }

    async function refreshToken() {
        const refresh = localStorage.getItem('refresh_token');
        if (!refresh) return false;
        try {
            const res = await fetch(`${BASE_URL}/api/auth/refresh?refresh_token=${refresh}`, { method: 'POST' });
            if (res.ok) {
                const data = await res.json();
                setTokens(data.access_token, data.refresh_token);
                return true;
            }
        } catch (e) { console.error('Token refresh failed:', e); }
        return false;
    }

    return {
        BASE_URL,
        getToken,
        setTokens,
        clearTokens,
        get: (endpoint) => request(endpoint),
        post: (endpoint, data) => request(endpoint, { method: 'POST', body: JSON.stringify(data) }),
        put: (endpoint, data) => request(endpoint, { method: 'PUT', body: JSON.stringify(data) }),
        delete: (endpoint) => request(endpoint, { method: 'DELETE' }),
        upload: async (endpoint, formData) => {
            const headers = {};
            const token = getToken();
            if (token) headers['Authorization'] = `Bearer ${token}`;
            const res = await fetch(`${BASE_URL}${endpoint}`, { method: 'POST', headers, body: formData });
            if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
            return res.json();
        }
    };
})();
