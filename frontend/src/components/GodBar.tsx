import { useState } from 'react';
import {
    Play,
    Pause,
    SkipForward,
    Percent,
    Landmark
} from 'lucide-react';
import { CockpitCommand } from '../types/cockpit';

interface GodBarProps {
    sendCommand: (command: CockpitCommand) => void;
    status: string;
}

export default function GodBar({ sendCommand, status }: GodBarProps) {
    const [baseRate, setBaseRate] = useState<string>("0.05");
    const [taxRate, setTaxRate] = useState<string>("0.1");
    const [taxType, setTaxType] = useState<"income" | "corporate">("income");

    const isPaused = status === "PAUSED" || status === "STOPPED" || status === "IDLE";

    const handleBaseRate = () => {
        const rate = parseFloat(baseRate);
        if (!isNaN(rate)) {
            sendCommand({
                type: "SET_BASE_RATE",
                payload: { rate }
            });
        }
    };

    const handleTaxRate = () => {
        const rate = parseFloat(taxRate);
        if (!isNaN(rate)) {
            sendCommand({
                type: "SET_TAX_RATE",
                payload: {
                    tax_type: taxType,
                    rate
                }
            });
        }
    };

    return (
        <div className="fixed bottom-0 left-0 right-0 p-4 glass-card border-t border-white/10 flex flex-wrap items-center justify-between gap-4 z-50 bg-black/80 backdrop-blur-md">

            {/* Simulation Controls */}
            <div className="flex items-center gap-2">
                {isPaused ? (
                    <button
                        onClick={() => sendCommand({ type: "RESUME", payload: {} })}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 rounded text-white font-bold transition-colors"
                    >
                        <Play size={16} /> RESUME
                    </button>
                ) : (
                    <button
                        onClick={() => sendCommand({ type: "PAUSE", payload: {} })}
                        className="flex items-center gap-2 px-4 py-2 bg-yellow-600 hover:bg-yellow-500 rounded text-white font-bold transition-colors"
                    >
                        <Pause size={16} /> PAUSE
                    </button>
                )}

                <button
                    onClick={() => sendCommand({ type: "STEP", payload: {} })}
                    className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-500 rounded text-white font-bold transition-colors disabled:opacity-50"
                    disabled={!isPaused}
                >
                    <SkipForward size={16} /> STEP
                </button>
            </div>

            {/* Central Bank Controls */}
            <div className="flex items-center gap-2 p-2 bg-white/5 rounded-lg border border-white/10">
                <Landmark size={16} className="text-muted-foreground ml-2" />
                <span className="text-xs font-bold text-muted-foreground uppercase">Base Rate</span>
                <input
                    type="number"
                    step="0.01"
                    value={baseRate}
                    onChange={(e) => setBaseRate(e.target.value)}
                    className="w-16 bg-black/40 border border-white/20 rounded px-2 py-1 text-sm text-white"
                />
                <button
                    onClick={handleBaseRate}
                    className="px-2 py-1 bg-white/10 hover:bg-white/20 rounded text-xs text-white"
                >
                    SET
                </button>
            </div>

            {/* Fiscal Policy Controls */}
            <div className="flex items-center gap-2 p-2 bg-white/5 rounded-lg border border-white/10">
                <Percent size={16} className="text-muted-foreground ml-2" />
                <select
                    value={taxType}
                    onChange={(e) => setTaxType(e.target.value as "income" | "corporate")}
                    className="bg-black/40 border border-white/20 rounded px-2 py-1 text-sm text-white"
                >
                    <option value="income">Income Tax</option>
                    <option value="corporate">Corp Tax</option>
                </select>
                <input
                    type="number"
                    step="0.01"
                    value={taxRate}
                    onChange={(e) => setTaxRate(e.target.value)}
                    className="w-16 bg-black/40 border border-white/20 rounded px-2 py-1 text-sm text-white"
                />
                <button
                    onClick={handleTaxRate}
                    className="px-2 py-1 bg-white/10 hover:bg-white/20 rounded text-xs text-white"
                >
                    SET
                </button>
            </div>

        </div>
    );
}
