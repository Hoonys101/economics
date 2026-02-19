import React from 'react';
import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, Legend, CartesianGrid } from 'recharts';
import { AgentBasicDTO } from '../../types/agents';

interface ScatterPlotProps {
    agents: AgentBasicDTO[];
    onSelectAgent: (agentId: number) => void;
}

const ScatterPlot: React.FC<ScatterPlotProps> = ({ agents, onSelectAgent }) => {
    // Separate data for visualization
    const households = agents.filter(a => a.type === 'household');
    const firms = agents.filter(a => a.type === 'firm');

    // Customize Tooltip
    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div className="bg-background border border-border p-2 rounded shadow-md text-xs">
                    <p className="font-bold">{data.type.toUpperCase()} #{data.id}</p>
                    <p>Wealth: {(data.wealth / 100).toFixed(2)}</p>
                    <p>Income: {(data.income / 100).toFixed(2)}</p>
                    <p>Expense: {(data.expense / 100).toFixed(2)}</p>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="w-full h-[500px] bg-card/50 rounded-xl p-4 border border-border/50 flex flex-col">
            <h3 className="text-lg font-semibold mb-2">Agent Distribution (Wealth vs Income)</h3>
            <div className="flex-1 min-h-0 w-full h-[400px]">
                <ResponsiveContainer width="100%" height={400}>
                    <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                        <XAxis
                            type="number"
                            dataKey="wealth"
                            name="Wealth"
                            unit=""
                            tickFormatter={(value) => (value / 100).toFixed(0)}
                            label={{ value: 'Wealth ($)', position: 'insideBottomRight', offset: -10 }}
                        />
                        <YAxis
                            type="number"
                            dataKey="income"
                            name="Income"
                            unit=""
                            tickFormatter={(value) => (value / 100).toFixed(0)}
                            label={{ value: 'Income ($)', angle: -90, position: 'insideLeft' }}
                        />
                        <ZAxis type="number" dataKey="id" range={[50, 400]} name="ID" />
                        <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
                        <Legend />
                        <Scatter
                            name="Households"
                            data={households}
                            fill="#3b82f6"
                            shape="circle"
                            onClick={(data) => onSelectAgent(data.id)}
                            cursor="pointer"
                        />
                        <Scatter
                            name="Firms"
                            data={firms}
                            fill="#ef4444"
                            shape="triangle"
                            onClick={(data) => onSelectAgent(data.id)}
                            cursor="pointer"
                        />
                    </ScatterChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default ScatterPlot;
