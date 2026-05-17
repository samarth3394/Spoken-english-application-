/**
 * Aspire English Hub - Authentication Module
 * =============================================
 * Handles signup, login, logout, session persistence.
 */

const Auth = (() => {
    function getUser() {
        try { return JSON.parse(localStorage.getItem('user')); } catch { return null; }
    }

    function setUser(userData) {
        localStorage.setItem('user', JSON.stringify(userData));
    }

    function isLoggedIn() {
        return !!API.getToken() && !!getUser();
    }

    function isAdmin() {
        const user = getUser();
        return user && (user.role === 'admin' || user.role === 'super_admin');
    }

    async function signup(email, password, fullName, displayName) {
        const data = await API.post('/api/auth/signup', { email, password, full_name: fullName, display_name: displayName });
        if (data.access_token) {
            API.setTokens(data.access_token, data.refresh_token);
            setUser({ id: data.user_id, email: data.email || email, role: 'student' });
        }
        return data;
    }

    async function login(email, password) {
        const data = await API.post('/api/auth/login', { email, password });
        if (data.access_token) {
            API.setTokens(data.access_token, data.refresh_token);
            setUser({ id: data.user_id, email: data.email, role: data.role });
        }
        return data;
    }

    async function logout() {
        try { await API.post('/api/auth/logout'); } catch (e) { /* ignore */ }
        API.clearTokens();
        window.location.href = '/pages/login.html';
    }

    async function getProfile() {
        return API.get('/api/auth/me');
    }

    async function updateProfile(updates) {
        return API.put('/api/auth/me', updates);
    }

    function requireAuth() {
        if (!isLoggedIn()) {
            window.location.href = '/pages/login.html';
            return false;
        }
        return true;
    }

    function requireAdmin() {
        if (!isAdmin()) {
            window.location.href = '/pages/login.html';
            return false;
        }
        return true;
    }

    return { getUser, setUser, isLoggedIn, isAdmin, signup, login, logout, getProfile, updateProfile, requireAuth, requireAdmin };
})();
