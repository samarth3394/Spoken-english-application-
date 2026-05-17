/**
 * Aspire English Hub - Utilities Module
 * =======================================
 * Shared utility functions for the frontend.
 */

const Utils = (() => {
    // Toast notifications
    function showToast(message, type = 'info', duration = 4000) {
        const container = document.getElementById('toast-container') || createToastContainer();
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        const icons = { info: 'ℹ️', success: '✅', warning: '⚠️', error: '❌', achievement: '🏆' };
        toast.innerHTML = `<span class="toast-icon">${icons[type] || 'ℹ️'}</span><span class="toast-msg">${message}</span>`;
        container.appendChild(toast);
        requestAnimationFrame(() => toast.classList.add('toast-show'));
        setTimeout(() => {
            toast.classList.remove('toast-show');
            toast.classList.add('toast-hide');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    function createToastContainer() {
        const c = document.createElement('div');
        c.id = 'toast-container';
        document.body.appendChild(c);
        return c;
    }

    // Loading state
    function showLoading(element, text = 'Loading...') {
        if (!element) return;
        element.dataset.originalContent = element.innerHTML;
        element.innerHTML = `<span class="spinner"></span> ${text}`;
        element.disabled = true;
    }

    function hideLoading(element) {
        if (!element) return;
        element.innerHTML = element.dataset.originalContent || '';
        element.disabled = false;
    }

    // Format duration
    function formatDuration(seconds) {
        if (!seconds || seconds < 0) return '0m';
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = seconds % 60;
        if (h > 0) return `${h}h ${m}m`;
        if (m > 0) return `${m}m ${s}s`;
        return `${s}s`;
    }

    // Format date
    function formatDate(dateStr) {
        return new Date(dateStr).toLocaleDateString('en-US', {
            year: 'numeric', month: 'short', day: 'numeric'
        });
    }

    function formatTimeAgo(dateStr) {
        const diff = (Date.now() - new Date(dateStr).getTime()) / 1000;
        if (diff < 60) return 'just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return `${Math.floor(diff / 86400)}d ago`;
    }

    // Sanitize HTML
    function sanitize(str) {
        const el = document.createElement('div');
        el.textContent = str;
        return el.innerHTML;
    }

    // Debounce
    function debounce(fn, delay = 300) {
        let timer;
        return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); };
    }

    // Navigate with SPA-like routing
    function navigate(page) {
        window.location.href = page;
    }

    // Score color
    function scoreColor(score) {
        if (score >= 80) return '#10b981';
        if (score >= 60) return '#f59e0b';
        if (score >= 40) return '#f97316';
        return '#ef4444';
    }

    // Generate avatar
    function getAvatar(name) {
        const colors = ['#6C63FF', '#FF6584', '#43E97B', '#FA709A', '#667EEA', '#F093FB'];
        const initials = (name || 'A').split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();
        const color = colors[initials.charCodeAt(0) % colors.length];
        return `<div class="avatar" style="background:${color}">${initials}</div>`;
    }

    return { showToast, showLoading, hideLoading, formatDuration, formatDate, formatTimeAgo, sanitize, debounce, navigate, scoreColor, getAvatar };
})();
