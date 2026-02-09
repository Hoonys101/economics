import { create } from 'zustand';
import { WatchtowerSnapshot } from '../types/contract';

interface WatchtowerState {
  snapshot: WatchtowerSnapshot | null;
  isConnected: boolean;
  commandConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  setSnapshot: (snapshot: WatchtowerSnapshot) => void;
  endpoint: string;
  sendCommand: (type: string, payload?: any) => void;
}

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/live';
const CMD_WS_URL = process.env.NEXT_PUBLIC_CMD_WS_URL || 'ws://localhost:8000/ws/command';
const INITIAL_RECONNECT_DELAY = 1000;
const MAX_RECONNECT_DELAY = 30000;

let ws: WebSocket | null = null;
let commandWs: WebSocket | null = null;
let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
let commandReconnectTimeout: ReturnType<typeof setTimeout> | null = null;

export const useWatchtowerStore = create<WatchtowerState>((set) => ({
  snapshot: null,
  isConnected: false,
  commandConnected: false,
  endpoint: WS_URL,

  setSnapshot: (snapshot) => set({ snapshot }),

  connect: () => {
    // --- Live Data Connection ---
    if (!ws || ws.readyState === WebSocket.CLOSED) {
        const attemptConnect = (delay: number) => {
            if (reconnectTimeout) {
                clearTimeout(reconnectTimeout);
                reconnectTimeout = null;
            }

            console.log(`Connecting to ${WS_URL}...`);
            ws = new WebSocket(WS_URL);

            ws.onopen = () => {
                console.log('Connected to Watchtower Live');
                set({ isConnected: true });
            };

            ws.onmessage = (event) => {
                try {
                    const data: WatchtowerSnapshot = JSON.parse(event.data);
                    set({ snapshot: data });
                } catch (error) {
                    console.error('Failed to parse snapshot:', error);
                }
            };

            ws.onclose = (event) => {
                console.log(`Disconnected from Watchtower Live. Code: ${event.code}`);
                set({ isConnected: false });
                ws = null;
                const nextDelay = Math.min(delay * 2, MAX_RECONNECT_DELAY);
                reconnectTimeout = setTimeout(() => attemptConnect(nextDelay), delay);
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        };
        attemptConnect(INITIAL_RECONNECT_DELAY);
    }

    // --- Command Connection ---
    if (!commandWs || commandWs.readyState === WebSocket.CLOSED) {
        const attemptCommandConnect = (delay: number) => {
            if (commandReconnectTimeout) {
                clearTimeout(commandReconnectTimeout);
                commandReconnectTimeout = null;
            }

            console.log(`Connecting to ${CMD_WS_URL}...`);
            commandWs = new WebSocket(CMD_WS_URL);

            commandWs.onopen = () => {
                console.log('Connected to Watchtower Command');
                set({ commandConnected: true });
            };

            commandWs.onclose = (event) => {
                console.log(`Disconnected from Watchtower Command. Code: ${event.code}`);
                set({ commandConnected: false });
                commandWs = null;
                const nextDelay = Math.min(delay * 2, MAX_RECONNECT_DELAY);
                commandReconnectTimeout = setTimeout(() => attemptCommandConnect(nextDelay), delay);
            };

             commandWs.onerror = (error) => {
                console.error('Command WebSocket error:', error);
            };
        };
        attemptCommandConnect(INITIAL_RECONNECT_DELAY);
    }
  },

  disconnect: () => {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }
    if (commandReconnectTimeout) {
        clearTimeout(commandReconnectTimeout);
        commandReconnectTimeout = null;
    }

    if (ws) {
      ws.onclose = null;
      ws.close();
      ws = null;
    }
    if (commandWs) {
        commandWs.onclose = null;
        commandWs.close();
        commandWs = null;
    }
    set({ isConnected: false, commandConnected: false });
  },

  sendCommand: (type: string, payload: any = {}) => {
      if (commandWs && commandWs.readyState === WebSocket.OPEN) {
          const message = JSON.stringify({ type, payload });
          commandWs.send(message);
      } else {
          console.warn("Command WebSocket not connected. Cannot send command:", type);
      }
  }
}));
