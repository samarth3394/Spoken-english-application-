/**
 * Aspire English Hub - WebRTC Handler
 * =====================================
 * Browser-based voice calling with WebRTC.
 */

const WebRTCHandler = (() => {
    let peerConnection = null;
    let localStream = null;
    let remoteStream = null;
    let currentCallId = null;
    let callTimer = null;
    let callDuration = 0;
    const listeners = {};

    const ICE_SERVERS = [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' },
        { urls: 'stun:stun2.l.google.com:19302' }
    ];

    function on(event, cb) {
        if (!listeners[event]) listeners[event] = [];
        listeners[event].push(cb);
    }

    function emit(event, data) {
        (listeners[event] || []).forEach(cb => cb(data));
    }

    async function getLocalStream() {
        try {
            localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
            return localStream;
        } catch (err) {
            console.error('Microphone access denied:', err);
            emit('error', { message: 'Microphone access is required for voice calls.' });
            throw err;
        }
    }

    function createPeerConnection(callId) {
        currentCallId = callId;
        peerConnection = new RTCPeerConnection({ iceServers: ICE_SERVERS });

        // Add local audio track
        if (localStream) {
            localStream.getTracks().forEach(track => peerConnection.addTrack(track, localStream));
        }

        // Handle remote stream
        peerConnection.ontrack = (event) => {
            remoteStream = event.streams[0];
            emit('remoteStream', remoteStream);
        };

        // ICE candidates
        peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                WS.send('ice_candidate', { call_id: callId, candidate: event.candidate });
            }
        };

        // Connection state
        peerConnection.onconnectionstatechange = () => {
            const state = peerConnection.connectionState;
            emit('connectionState', state);
            if (state === 'connected') {
                startTimer();
                WS.send('call_connected', { call_id: callId });
            } else if (state === 'disconnected' || state === 'failed') {
                emit('callEnded', { reason: state });
            }
        };

        return peerConnection;
    }

    async function createOffer(callId) {
        await getLocalStream();
        createPeerConnection(callId);
        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);
        WS.send('offer', { call_id: callId, sdp: offer });
        emit('calling', { callId });
    }

    async function handleOffer(callId, sdp) {
        await getLocalStream();
        createPeerConnection(callId);
        await peerConnection.setRemoteDescription(new RTCSessionDescription(sdp));
        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);
        WS.send('answer', { call_id: callId, sdp: answer });
    }

    async function handleAnswer(sdp) {
        if (peerConnection) {
            await peerConnection.setRemoteDescription(new RTCSessionDescription(sdp));
        }
    }

    async function handleIceCandidate(candidate) {
        if (peerConnection && candidate) {
            try {
                await peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
            } catch (e) { console.error('ICE candidate error:', e); }
        }
    }

    function toggleMute() {
        if (localStream) {
            const audioTrack = localStream.getAudioTracks()[0];
            if (audioTrack) {
                audioTrack.enabled = !audioTrack.enabled;
                return !audioTrack.enabled; // returns true if now muted
            }
        }
        return false;
    }

    function endCall() {
        stopTimer();
        if (currentCallId) {
            WS.send('end_call', { call_id: currentCallId });
        }
        cleanup();
        emit('callEnded', { duration: callDuration });
    }

    function cleanup() {
        stopTimer();
        if (localStream) {
            localStream.getTracks().forEach(t => t.stop());
            localStream = null;
        }
        if (peerConnection) {
            peerConnection.close();
            peerConnection = null;
        }
        remoteStream = null;
        currentCallId = null;
    }

    function startTimer() {
        callDuration = 0;
        callTimer = setInterval(() => {
            callDuration++;
            emit('timerUpdate', callDuration);
        }, 1000);
    }

    function stopTimer() {
        if (callTimer) { clearInterval(callTimer); callTimer = null; }
    }

    function formatTime(seconds) {
        const m = Math.floor(seconds / 60).toString().padStart(2, '0');
        const s = (seconds % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    }

    // Wire up WS events
    WS.on('offer', (data) => handleOffer(data.call_id, data.sdp));
    WS.on('answer', (data) => handleAnswer(data.sdp));
    WS.on('ice_candidate', (data) => handleIceCandidate(data.candidate));
    WS.on('call_ended', (data) => { cleanup(); emit('callEnded', data); });

    return { on, createOffer, handleOffer, toggleMute, endCall, cleanup, formatTime, getLocalStream };
})();
