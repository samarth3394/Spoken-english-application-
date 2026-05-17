/**
 * Aspire English Hub - Main Application
 * ========================================
 * App initialization and global configuration.
 */

window.APP_CONFIG = {
    API_URL: 'http://localhost:8000',
    APP_NAME: 'Aspire English Hub',
    VERSION: '1.0.0'
};

document.addEventListener('DOMContentLoaded', () => {
    // Theme toggle
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);

    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('theme', next);
            themeBtn.textContent = next === 'dark' ? '☀️' : '🌙';
        });
    }

    // Mobile nav toggle
    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.getElementById('nav-menu');
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => navMenu.classList.toggle('nav-open'));
    }

    // Auth-aware nav
    updateNav();
});

function updateNav() {
    const authLinks = document.getElementById('auth-links');
    if (!authLinks) return;

    if (Auth.isLoggedIn()) {
        const user = Auth.getUser();
        authLinks.innerHTML = `
            <a href="/pages/dashboard.html" class="nav-link">Dashboard</a>
            ${Auth.isAdmin() ? '<a href="/pages/admin/dashboard.html" class="nav-link">Admin</a>' : ''}
            <button onclick="Auth.logout()" class="btn btn-outline btn-sm">Logout</button>
        `;
    } else {
        authLinks.innerHTML = `
            <a href="/pages/login.html" class="btn btn-outline btn-sm">Login</a>
            <a href="/pages/signup.html" class="btn btn-primary btn-sm">Sign Up</a>
        `;
    }
}
