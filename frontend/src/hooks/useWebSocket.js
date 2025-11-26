import { useState, useEffect, useCallback, useRef } from 'react';

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export const useWebSocket = (jobId) => {
    const [status, setStatus] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const wsRef = useRef(null);

    const connect = useCallback(() => {
        if (!jobId) return;

        const ws = new WebSocket(`${WS_BASE_URL}/ws/jobs/${jobId}`);

        ws.onopen = () => {
            console.log('WebSocket connected');
            setIsConnected(true);
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                setStatus(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
            setIsConnected(false);

            // Reconnect after 5 seconds
            setTimeout(() => {
                if (ws Ref.current) {
                connect();
            }
        }, 5000);
};

wsRef.current = ws;

return () => {
    if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
    }
};
  }, [jobId]);

useEffect(() => {
    const cleanup = connect();
    return cleanup;
}, [connect]);

return { status, isConnected };
};
