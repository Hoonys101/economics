import React, { useState } from 'react';
import ScatterPlot from './ScatterPlot';
import InspectorPanel from './InspectorPanel';
import { useAgents } from '../../hooks/useAgents';

const MacroCanvas: React.FC = () => {
    const { agents, connected } = useAgents();
    const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);

    return (
        <div className="h-full flex gap-4">
            {/* Main Canvas Area */}
            <div className="flex-1 flex flex-col gap-4">
                <div className="flex justify-between items-center bg-card/50 px-4 py-2 rounded-xl border border-border/50">
                    <h2 className="text-xl font-bold">Macro Canvas</h2>
                    <div className="flex items-center gap-2 text-sm">
                        <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
                        {connected ? `${agents.length} Agents Live` : 'Disconnected'}
                    </div>
                </div>

                <div className="flex-1 min-h-0 relative">
                     <ScatterPlot agents={agents} onSelectAgent={setSelectedAgentId} />
                </div>
            </div>

            {/* Inspector Panel Sidebar */}
            <div className="w-80 flex-shrink-0">
                <InspectorPanel agentId={selectedAgentId} />
            </div>
        </div>
    );
};

export default MacroCanvas;
