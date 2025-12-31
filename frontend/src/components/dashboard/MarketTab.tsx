import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { MarketTabData } from '../../types/dashboard';

interface MarketTabProps {
  data: MarketTabData;
}

export default function MarketTab({ data }: MarketTabProps) {
  if (!data) return <div className="text-muted-foreground p-4">No data available</div>;

  // Prepare time-series data
  // cpi and maslow_fulfillment are just arrays of numbers (history)
  // We need to map them to objects for Recharts
  const historyData = data.cpi.map((val, index) => ({
    tick: index, // Relative index
    cpi: val,
    maslow: data.maslow_fulfillment[index] || 0
  }));

  const volumeData = Object.entries(data.commodity_volumes).map(([key, value]) => ({
    name: key,
    volume: value
  }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full h-full">
      {/* CPI & Maslow History */}
      <div className="glass-card p-6 flex flex-col lg:col-span-2">
        <div className="flex justify-between items-center mb-4">
             <h3 className="text-lg font-semibold text-white">Market Trends (Recent 50 Ticks)</h3>
             <div className="flex gap-4 text-sm">
                 <div className="flex items-center gap-2"><div className="w-3 h-3 bg-purple-500 rounded-full"></div>CPI</div>
                 <div className="flex items-center gap-2"><div className="w-3 h-3 bg-yellow-500 rounded-full"></div>Maslow</div>
             </div>
        </div>
        <div className="flex-1 min-h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={historyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="tick" stroke="#888" tick={false} />
              <YAxis yAxisId="left" stroke="#d8b4fe" />
              <YAxis yAxisId="right" orientation="right" stroke="#fde047" domain={[0, 100]} />
              <Tooltip 
                 contentStyle={{ backgroundColor: '#1e293b', borderColor: '#333' }}
                 itemStyle={{ color: '#fff' }}
              />
              <Line yAxisId="left" type="monotone" dataKey="cpi" stroke="#d8b4fe" strokeWidth={2} dot={false} />
              <Line yAxisId="right" type="monotone" dataKey="maslow" stroke="#fde047" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Commodity Volumes */}
      <div className="glass-card p-6 flex flex-col lg:col-span-2">
        <h3 className="text-lg font-semibold text-white mb-4">Commodity Trading Volumes</h3>
        <div className="flex-1 min-h-[200px]">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={volumeData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#333" horizontal={false} />
              <XAxis type="number" stroke="#888" />
              <YAxis dataKey="name" type="category" stroke="#888" width={100} />
              <Tooltip 
                  cursor={{fill: 'rgba(255,255,255,0.05)'}}
                  contentStyle={{ backgroundColor: '#1e293b', borderColor: '#333' }}
                  itemStyle={{ color: '#fff' }}
              />
              <Bar dataKey="volume" fill="var(--color-primary)" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
