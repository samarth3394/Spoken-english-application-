/**
 * Aspire English Hub - WebSocket Handler
 * ========================================
 * Real-time communication via WebSockets.
 */

const WS = (() => {
    let socket = null;
    let reconnectAttempts = 0;
    const maxReconnect = 5;
    const listeners = {};

    function getWSUrl() {
        const base = API.BASE_URL.replace('http', 'ws');
        return `${base}/ws?token=${API.getToken()}`;
    }

    function connect() {
        if (socket?.readyState === WebSocket.OPEN) return;
        const token = API.getToken();
        if (!token) return;

        socket = new WebSocket(getWSUrl());

        socket.onopen = () => {
            console.log('🔌 WebSocket connected');
            reconnectAttempts = 0;
            emit('connected', {});
            startPing();
        };

        socket.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                emit(msg.type, msg.data || msg);
            } catch (e) {
                console.error('WS parse error:', e);
            }
        };

        socket.onclose = (event) => {
            console.log('🔌 WebSocket disconnected:', event.code);
            emit('disconnected', { code: event.code });
            stopPing();
            if (event.code !== 4001 && reconnectAttempts < maxReconnect) {
                const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
                setTimeout(() => { reconnectAttempts++; connect(); }, delay);
            }
        };

        socket.onerror = (error) => {
            console.error('WS error:', error);
            emit('error', { error });
        };
    }

    function disconnect() {
        stopPing();
        if (socket) { socket.close(); socket = null; }
    }

    function send(type, data = {}) {
        if (socket?.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type, ...data }));
        } else {
            console.warn('WS not connected, cannot send:', type);
        }
    }

    function on(event, callback) {
        if (!listeners[event]) listeners[event] = [];
        listeners[event].push(callback);
    }

    function off(event, callback) {
        if (listeners[event]) {
            listeners[event] = listeners[event].filter(cb => cb !== callback);
        }
    }

    function emit(event, data) {
        (listeners[event] || []).forEach(cb => {
            try { cb(data); } catch (e) { console.error(`WS listener error [${event}]:`, e); }
        });
    }

    let pingInterval = null;
    function startPing() {
        pingInterval = setInterval(() => send('ping'), 30000);
    }
    function stopPing() {
        if (pingInterval) { clearInterval(pingInterval); pingInterval = null; }
    }

    return { connect, disconnect, send, on, off };
})();
