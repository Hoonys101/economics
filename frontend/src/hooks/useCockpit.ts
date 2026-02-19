import { useState, useEffect } from 'react';
import { socketService } from '../services/socket';
import { WatchtowerSnapshotDTO } from '../types/watchtower';
import { CockpitCommand } from '../types/cockpit';

export const useCockpit = () => {
    const [snapshot, setSnapshot] = useState<WatchtowerSnapshotDTO | null>(null);
    const [connected, setConnected] = useState<boolean>(false);

    useEffect(() => {
        const unsubscribeSnapshot = socketService.subscribe((data) => {
            setSnapshot(data);
        });

        const unsubscribeStatus = socketService.onStatusChange((status) => {
            setConnected(status);
        });

        return () => {
            unsubscribeSnapshot();
            unsubscribeStatus();
        };
    }, []);

    const sendCommand = (command: CockpitCommand) => {
        socketService.sendCommand(command);
    };

    return { snapshot, connected, sendCommand };
};
