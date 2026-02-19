import { WatchtowerSnapshotDTO } from '../types/watchtower';
import { CockpitCommand } from '../types/cockpit';

type SnapshotCallback = (data: WatchtowerSnapshotDTO) => void;
type StatusCallback = (connected: boolean) => void;

class SocketService {
    private liveSocket: WebSocket | null = null;
    private commandSocket: WebSocket | null = null;
    private snapshotCallbacks: SnapshotCallback[] = [];
    private statusCallbacks: StatusCallback[] = [];
    private reconnectInterval: number = 2000;
    private token: string = import.meta.env.VITE_GOD_MODE_TOKEN || "default-god-token";

    constructor() {
        // Auto-connect on instantiation
        this.connect();
    }

    private connect() {
        this.connectLive();
        this.connectCommand();
    }

    private getWsUrl(path: string, params: Record<string, string> = {}): string {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        let url = `${protocol}//${host}${path}`;

        const queryString = new URLSearchParams(params).toString();
        if (queryString) {
            url += `?${queryString}`;
        }

        return url;
    }

    private connectLive() {
        if (this.liveSocket && (this.liveSocket.readyState === WebSocket.OPEN || this.liveSocket.readyState === WebSocket.CONNECTING)) return;

        const url = this.getWsUrl('/ws/live');
        console.log(`Connecting to Live WS: ${url}`);

        this.liveSocket = new WebSocket(url);

        this.liveSocket.onopen = () => {
            console.log('Live WS Connected');
            this.notifyStatus(true);
        };

        this.liveSocket.onmessage = (event) => {
            try {
                const data: WatchtowerSnapshotDTO = JSON.parse(event.data);
                this.notifySnapshot(data);
            } catch (e) {
                console.error('Error parsing snapshot:', e);
            }
        };

        this.liveSocket.onclose = () => {
            console.log('Live WS Disconnected');
            this.notifyStatus(false);
            setTimeout(() => this.connectLive(), this.reconnectInterval);
        };

        this.liveSocket.onerror = (error) => {
            console.error('Live WS Error:', error);
            this.liveSocket?.close();
        };
    }

    private connectCommand() {
        if (this.commandSocket && (this.commandSocket.readyState === WebSocket.OPEN || this.commandSocket.readyState === WebSocket.CONNECTING)) return;

        const url = this.getWsUrl('/ws/command', { token: this.token });
        console.log(`Connecting to Command WS: ${url}`);

        this.commandSocket = new WebSocket(url);

        this.commandSocket.onopen = () => {
            console.log('Command WS Connected');
        };

        this.commandSocket.onclose = () => {
            console.log('Command WS Disconnected');
            setTimeout(() => this.connectCommand(), this.reconnectInterval);
        };

        this.commandSocket.onerror = (error) => {
            console.error('Command WS Error:', error);
            this.commandSocket?.close();
        };
    }

    public subscribe(callback: SnapshotCallback): () => void {
        this.snapshotCallbacks.push(callback);
        return () => {
            this.snapshotCallbacks = this.snapshotCallbacks.filter(cb => cb !== callback);
        };
    }

    public onStatusChange(callback: StatusCallback): () => void {
        this.statusCallbacks.push(callback);
        // Immediately notify current status
        callback(this.liveSocket?.readyState === WebSocket.OPEN);
        return () => {
            this.statusCallbacks = this.statusCallbacks.filter(cb => cb !== callback);
        };
    }

    private notifySnapshot(data: WatchtowerSnapshotDTO) {
        this.snapshotCallbacks.forEach(cb => cb(data));
    }

    private notifyStatus(connected: boolean) {
        this.statusCallbacks.forEach(cb => cb(connected));
    }

    public sendCommand(command: CockpitCommand) {
        if (this.commandSocket && this.commandSocket.readyState === WebSocket.OPEN) {
            this.commandSocket.send(JSON.stringify(command));
        } else {
            console.warn('Command Socket not ready');
        }
    }
}

export const socketService = new SocketService();
