import { FinanceTabData } from '../../types/dashboard';

interface FinanceTabProps {
  data: FinanceTabData;
}

const FinanceCard = ({ label, value, subtext }: { label: string, value: string, subtext?: string }) => (
    <div className="glass-card p-6 flex flex-col items-center justify-center text-center hover:bg-white/5 transition-colors">
        <div className="text-muted-foreground uppercase text-xs font-bold tracking-widest mb-2">{label}</div>
        <div className="text-3xl lg:text-4xl font-mono text-white mb-1">{value}</div>
        {subtext && <div className="text-emerald-400 text-sm">{subtext}</div>}
    </div>
);

export default function FinanceTab({ data }: FinanceTabProps) {
  if (!data) return <div className="text-muted-foreground p-4">No data available</div>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 w-full h-full content-start">
        <FinanceCard 
            label="Total Market Cap" 
            value={`$${(data.market_cap / 1000000).toFixed(2)}M`} 
            subtext="+1.2% vs prev"
        />
        <FinanceCard 
            label="Daily Volume" 
            value={`$${(data.volume / 1000).toFixed(1)}K`} 
        />
        <FinanceCard 
            label="Turnover" 
            value={`${data.turnover.toFixed(2)}%`}
        />
        <FinanceCard 
            label="Dividend Yield" 
            value={`${data.dividend_yield.toFixed(2)}%`}
             subtext="Avg. Market Yield"
        />

        <div className="glass-card p-6 md:col-span-2 lg:col-span-4 min-h-[200px] flex flex-col justify-center items-center text-muted-foreground">
            <p>Advanced Financial Charts (Candlestick / Depth) - Coming Soon</p>
        </div>
    </div>
  );
}
