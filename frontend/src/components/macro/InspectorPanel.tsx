import React, { useEffect, useState } from 'react';
import { AgentDetailDTO } from '../../types/agents';

interface InspectorPanelProps {
    agentId: number | null;
}

const InspectorPanel: React.FC<InspectorPanelProps> = ({ agentId }) => {
    const [detail, setDetail] = useState<AgentDetailDTO | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!agentId) {
            setDetail(null);
            return;
        }

        const fetchDetail = async () => {
            setLoading(true);
            setError(null);
            try {
                // Updated to match API contract /api/v1/inspector/{agentId}
                const res = await fetch(`/api/v1/inspector/${agentId}`);
                if (!res.ok) {
                    throw new Error(`Failed to fetch agent ${agentId}: ${res.statusText}`);
                }
                const data = await res.json();
                setDetail(data);
            } catch (err: any) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchDetail();
    }, [agentId]);

    if (!agentId) {
        return (
            <div className="h-full bg-card/50 rounded-xl p-6 border border-border/50 flex items-center justify-center text-muted-foreground">
                Select an agent from the scatter plot to inspect.
            </div>
        );
    }

    if (loading) {
        return (
            <div className="h-full bg-card/50 rounded-xl p-6 border border-border/50 flex items-center justify-center">
                <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="h-full bg-card/50 rounded-xl p-6 border border-border/50 flex flex-col items-center justify-center text-destructive">
                <p>Error loading agent details</p>
                <p className="text-sm opacity-75">{error}</p>
            </div>
        );
    }

    if (!detail) return null;

    const formatMoney = (val: number | undefined) => (val !== undefined ? `$${(val / 100).toFixed(2)}` : '-');

    return (
        <div className="h-full bg-card/50 rounded-xl p-6 border border-border/50 overflow-y-auto">
            <div className="flex justify-between items-center mb-4 border-b border-border/50 pb-2">
                <h3 className="text-xl font-bold">{detail.type.toUpperCase()} #{detail.id}</h3>
                <span className={`px-2 py-1 rounded text-xs font-mono ${detail.is_active ? 'bg-green-500/20 text-green-500' : 'bg-red-500/20 text-red-500'}`}>
                    {detail.is_active ? 'ACTIVE' : 'INACTIVE'}
                </span>
            </div>

            <div className="space-y-4 text-sm">
                <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-background/50 rounded border border-border/30">
                        <div className="text-xs text-muted-foreground">Total Wealth</div>
                        <div className="font-semibold text-lg">{formatMoney(detail.wealth)}</div>
                    </div>
                    <div className="p-3 bg-background/50 rounded border border-border/30">
                        <div className="text-xs text-muted-foreground">Income (Tick)</div>
                        <div className="font-semibold text-lg text-green-400">{formatMoney(detail.income)}</div>
                    </div>
                </div>

                {detail.type === 'household' && (
                    <div className="space-y-2">
                        <h4 className="font-semibold text-muted-foreground uppercase text-xs tracking-wider">Demographics</h4>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                            <div className="flex justify-between">
                                <span>Age:</span>
                                <span>{detail.age?.toFixed(1)}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>Employer ID:</span>
                                <span>{detail.employer_id ?? 'Unemployed'}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>Wage:</span>
                                <span>{formatMoney(detail.current_wage)}</span>
                            </div>
                        </div>

                        {detail.needs && (
                            <div className="mt-2">
                                <h4 className="font-semibold text-muted-foreground uppercase text-xs tracking-wider mb-1">Needs</h4>
                                <div className="grid grid-cols-2 gap-2">
                                    {Object.entries(detail.needs).map(([key, val]) => (
                                        <div key={key} className="flex flex-col">
                                            <div className="flex justify-between text-xs mb-0.5">
                                                <span>{key}</span>
                                                <span>{(val * 100).toFixed(0)}%</span>
                                            </div>
                                            <div className="h-1.5 bg-background rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full ${val > 0.5 ? 'bg-green-500' : val > 0.2 ? 'bg-yellow-500' : 'bg-red-500'}`}
                                                    style={{ width: `${Math.min(100, val * 100)}%` }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                         {detail.inventory && (
                            <div className="mt-2">
                                <h4 className="font-semibold text-muted-foreground uppercase text-xs tracking-wider mb-1">Inventory</h4>
                                <div className="flex flex-wrap gap-2">
                                    {Object.entries(detail.inventory).map(([key, val]) => (
                                        <div key={key} className="px-2 py-1 bg-background rounded text-xs border border-border/20">
                                            {key}: {val.toFixed(1)}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {detail.type === 'firm' && (
                    <div className="space-y-2">
                        <h4 className="font-semibold text-muted-foreground uppercase text-xs tracking-wider">Production</h4>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                             <div className="flex justify-between">
                                <span>Sector:</span>
                                <span>{detail.sector}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>Employees:</span>
                                <span>{detail.employees_count}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>Production:</span>
                                <span>{detail.production?.toFixed(1)}</span>
                            </div>
                        </div>

                        {detail.revenue_this_turn && (
                            <div className="mt-2">
                                <h4 className="font-semibold text-muted-foreground uppercase text-xs tracking-wider mb-1">Revenue Sources</h4>
                                <div className="space-y-1">
                                    {Object.entries(detail.revenue_this_turn).map(([key, val]) => (
                                        <div key={key} className="flex justify-between text-xs">
                                            <span>{key}</span>
                                            <span>{formatMoney(val)}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default InspectorPanel;
