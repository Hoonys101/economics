import { create } from 'zustand';
import { WatchtowerSnapshot } from '../types/contract';

interface WatchtowerState {
  snapshot: WatchtowerSnapshot | null;
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  setSnapshot: (snapshot: WatchtowerSnapshot) => void;
  endpoint: string;
}

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/live';
const INITIAL_RECONNECT_DELAY = 1000;
const MAX_RECONNECT_DELAY = 30000;

let ws: WebSocket | null = null;
let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;

export const useWatchtowerStore = create<WatchtowerState>((set) => ({
  snapshot: null,
  isConnected: false,
  endpoint: WS_URL,

  setSnapshot: (snapshot) => set({ snapshot }),

  connect: () => {
    // If already connected or connecting, do nothing
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const attemptConnect = (delay: number) => {
      // Clear any existing timeout to avoid multiple attempts
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
        reconnectTimeout = null;
      }

      console.log(`Connecting to ${WS_URL}...`);
      ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        console.log('Connected to Watchtower');
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

      ws.onclose = () => {
        console.log('Disconnected from Watchtower');
        set({ isConnected: false });
        ws = null;

        // Exponential backoff
        const nextDelay = Math.min(delay * 2, MAX_RECONNECT_DELAY);
        console.log(`Reconnecting in ${nextDelay}ms...`);
        reconnectTimeout = setTimeout(() => attemptConnect(nextDelay), delay);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        // Error usually leads to close, which handles reconnection
      };
    };

    attemptConnect(INITIAL_RECONNECT_DELAY);
  },

  disconnect: () => {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }
    if (ws) {
      // Remove onclose handler to prevent reconnection loop when manually disconnecting
      ws.onclose = null;
      ws.close();
      ws = null;
    }
    set({ isConnected: false });
  },
}));
