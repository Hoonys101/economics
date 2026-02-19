import { useState, useEffect } from 'react';
import { AgentBasicDTO } from '../types/agents';

export const useAgents = () => {
    const [agents, setAgents] = useState<AgentBasicDTO[]>([]);
    const [connected, setConnected] = useState(false);

    useEffect(() => {
        let ws: WebSocket | null = null;
        let timeoutId: number | null = null;

        const connect = () => {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.host;
            // Use window.location.host directly which includes port if any
            // If running via Vite proxy, it handles it.
            // If running via static file server, it assumes backend is same host/port?
            // Usually Vite dev server proxies /ws/agents to backend 8000.
            // So connecting to `ws://localhost:5173/ws/agents` (Vite) proxies to `ws://localhost:8000/ws/agents`.
            const url = `${protocol}//${host}/ws/agents`;

            console.log(`Connecting to Agents WS: ${url}`);
            ws = new WebSocket(url);

            ws.onopen = () => {
                console.log('Agents WS Connected');
                setConnected(true);
            };

            ws.onmessage = (event) => {
                try {
                    const data: AgentBasicDTO[] = JSON.parse(event.data);
                    setAgents(data);
                } catch (e) {
                    console.error('Error parsing agents data:', e);
                }
            };

            ws.onclose = () => {
                console.log('Agents WS Disconnected');
                setConnected(false);
                // Reconnect after 2s
                timeoutId = window.setTimeout(connect, 2000);
            };

            ws.onerror = (error) => {
                console.error('Agents WS Error:', error);
                ws?.close();
            };
        };

        connect();

        return () => {
            if (ws) {
                // Remove listener to prevent reconnection loop on unmount
                ws.onclose = null;
                ws.close();
            }
            if (timeoutId) {
                clearTimeout(timeoutId);
            }
        };
    }, []);

    return { agents, connected };
};
