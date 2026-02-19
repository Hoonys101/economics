import {
    Activity,
    Users,
    TrendingUp,
    DollarSign,
    Percent,
    ThumbsUp,
    AlertTriangle
} from 'lucide-react';
import { WatchtowerSnapshotDTO } from '../types/watchtower';

interface HUDProps {
    data: WatchtowerSnapshotDTO;
}

const Indicator = ({
    label,
    value,
    unit = '',
    icon: Icon,
    color = 'text-white'
}: {
    label: string;
    value: string | number;
    unit?: string;
    icon?: any;
    color?: string;
}) => (
    <div className="glass-card flex flex-col items-center justify-center p-2 min-w-[100px] flex-1">
        <div className="flex items-center gap-1 mb-1">
            {Icon && <Icon size={14} className="text-muted-foreground" />}
            <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">{label}</span>
        </div>
        <div className={`text-xl font-bold ${color}`}>
            {value}<span className="text-xs text-muted-foreground ml-0.5">{unit}</span>
        </div>
    </div>
);

export default function HUD({ data }: HUDProps) {
    const {
        tick,
        macro,
        integrity,
        population,
        politics
    } = data;

    // Formatting helpers
    const fmtPct = (val: number) => (val * 100).toFixed(1);
    const fmtInt = (val: number) => val.toLocaleString();
    const fmtFloat = (val: number) => val.toFixed(2);

    return (
        <header className="flex flex-col gap-2 w-full">
            {/* Top Bar: Integrity & Status */}
            <div className="flex justify-between items-center px-4 py-2 bg-black/20 rounded-lg text-xs">
                <div className="flex gap-4">
                    <span className="text-muted-foreground">TICK: <span className="text-white font-mono">{tick}</span></span>
                    <span className="text-muted-foreground">FPS: <span className="text-green-400 font-mono">{integrity.fps.toFixed(1)}</span></span>
                    {integrity.m2_leak !== 0 && (
                        <span className="text-red-500 font-bold flex items-center gap-1">
                            <AlertTriangle size={12} />
                            LEAK: {integrity.m2_leak}
                        </span>
                    )}
                </div>
                <div className="flex gap-4">
                    <span className="text-muted-foreground">STATUS: <span className="text-blue-400 font-bold">{data.status}</span></span>
                </div>
            </div>

            {/* Main HUD Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-2">
                <Indicator
                    label="GDP"
                    value={fmtInt(macro.gdp)}
                    icon={DollarSign}
                    color="text-yellow-400"
                />
                <Indicator
                    label="CPI"
                    value={fmtFloat(macro.cpi)}
                    icon={TrendingUp}
                    color={macro.cpi > 105 ? 'text-red-400' : 'text-emerald-400'}
                />
                <Indicator
                    label="Unemployment"
                    value={fmtPct(macro.unemploy)}
                    unit="%"
                    icon={Users}
                    color={macro.unemploy > 0.1 ? 'text-red-400' : 'text-blue-400'}
                />
                 <Indicator
                    label="Gini"
                    value={fmtFloat(macro.gini)}
                    icon={Percent}
                    color={macro.gini > 0.4 ? 'text-orange-400' : 'text-purple-400'}
                />
                <Indicator
                    label="Population"
                    value={fmtInt(population.active_count)}
                    icon={Users}
                    color="text-white"
                />
                <Indicator
                    label="Approval"
                    value={fmtPct(politics.approval.total)}
                    unit="%"
                    icon={ThumbsUp}
                    color={politics.approval.total < 0.3 ? 'text-red-400' : 'text-green-400'}
                />
                 <Indicator
                    label="Births"
                    value={fmtFloat(population.metrics.birth)}
                    icon={Activity}
                    color="text-pink-400"
                />
                 <Indicator
                    label="Deaths"
                    value={fmtFloat(population.metrics.death)}
                    icon={Activity}
                    color="text-gray-400"
                />
            </div>
        </header>
    );
}
