import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { SocietyTabData } from '../../types/dashboard';

const COLORS = ['#ef4444', '#22c55e']; // Red for struggling, Green for voluntary
// Colors for Time Allocation: Work, Parenting, SelfDev, Ent, Idle
const TIME_COLORS = {
  WORK: '#ef4444',
  PARENTING: '#22c55e',
  SELF_DEV: '#3b82f6',
  ENTERTAINMENT: '#eab308',
  IDLE: '#94a3b8'
};

interface SocietyTabProps {
  data: SocietyTabData;
}

export default function SocietyTab({ data }: SocietyTabProps) {
  // Safe check for data
  if (!data) return <div className="text-muted-foreground p-4">No data available</div>;

  const unemploymentData = [
    { name: 'Struggling', value: data.unemployment_pie.struggling },
    { name: 'Voluntary', value: data.unemployment_pie.voluntary },
  ];

  // Map Time Allocation Dictionary to Recharts Array
  const timeAllocationData = data.time_allocation ? Object.entries(data.time_allocation).map(([key, value]) => ({
    name: key.replace('_', ' '), // e.g. SELF_DEV -> SELF DEV
    value: value
  })) : [];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full h-full">
      {/* Generation Wealth Distribution */}
      <div className="glass-card p-6 flex flex-col md:col-span-2 lg:col-span-1">
        <h3 className="text-lg font-semibold text-white mb-4">Generation Wealth Distribution</h3>
        <div className="flex-1 min-h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data.generations}>
              <defs>
                <linearGradient id="colorAssets" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="gen" stroke="#888" />
              <YAxis stroke="#888" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1e293b', borderColor: '#333' }}
                itemStyle={{ color: '#fff' }}
              />
              <Area type="monotone" dataKey="avg_assets" stroke="var(--color-primary)" fillOpacity={1} fill="url(#colorAssets)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Time Allocation (Phase 5) */}
      <div className="glass-card p-6 flex flex-col">
        <h3 className="text-lg font-semibold text-white mb-4">Time Allocation</h3>
        <div className="flex-1 min-h-[300px] flex items-center justify-center">
             <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={timeAllocationData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={2}
                dataKey="value"
              >
                {timeAllocationData.map((entry, index) => {
                  const key = entry.name.replace(' ', '_') as keyof typeof TIME_COLORS;
                  return <Cell key={`cell-${index}`} fill={TIME_COLORS[key] || '#888'} />;
                })}
              </Pie>
              <Tooltip
                 contentStyle={{ backgroundColor: '#1e293b', borderColor: '#333' }}
                 itemStyle={{ color: '#fff' }}
                 formatter={(value: any) => [Number(value).toFixed(1) + ' hrs', 'Hours']}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-4 text-center">
            <p className="text-sm text-muted-foreground">Avg Leisure: <span className="text-white font-bold">{data.avg_leisure_hours.toFixed(1)} hrs</span></p>
        </div>
      </div>

      {/* Unemployment Breakdown */}
      <div className="glass-card p-6 flex flex-col">
        <h3 className="text-lg font-semibold text-white mb-4">Unemployment Analysis</h3>
        <div className="flex-1 min-h-[300px] flex items-center justify-center">
             <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={unemploymentData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                fill="#8884d8"
                paddingAngle={5}
                dataKey="value"
              >
                {unemploymentData.map((_entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                 contentStyle={{ backgroundColor: '#1e293b', borderColor: '#333' }}
                 itemStyle={{ color: '#fff' }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-4 text-center">
            <p className="text-sm text-muted-foreground">Mitosis Cost Threshold: <span className="text-white font-bold">{data.mitosis_cost.toFixed(0)}</span></p>
        </div>
      </div>
    </div>
  );
}
