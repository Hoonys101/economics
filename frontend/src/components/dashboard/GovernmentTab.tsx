import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid, AreaChart, Area } from 'recharts';
import { GovernmentTabData } from '../../types/dashboard';

const TAX_COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ec4899'];

interface GovernmentTabProps {
  data: GovernmentTabData;
}

export default function GovernmentTab({ data }: GovernmentTabProps) {
  if (!data) return <div className="text-muted-foreground p-4">No data available</div>;

  const balanceData = [
    { name: 'Revenue', amount: data.fiscal_balance.revenue, fill: '#10b981' },
    { name: 'Expense', amount: data.fiscal_balance.expense, fill: '#ef4444' }
  ];

  // Process History Data for Stacked Bar
  const historyData = data.tax_revenue_history?.map(item => {
      // Flatten the item for Recharts: { tick: 1, income_tax: 10, ... }
      return {
          tick: item.tick,
          ...item
      };
  }) || [];

  // Get keys for stacked bar (exclude 'tick' and 'total')
  const taxKeys = historyData.length > 0
      ? Object.keys(historyData[0]).filter(k => k !== 'tick' && k !== 'total')
      : [];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full h-full">
      {/* Fiscal Balance (Summary) */}
      <div className="glass-card p-6 flex flex-col">
        <h3 className="text-lg font-semibold text-white mb-4">Fiscal Balance</h3>
        <div className="flex-1 min-h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={balanceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
              <XAxis dataKey="name" stroke="#888" />
              <YAxis stroke="#888" />
              <Tooltip 
                  cursor={{fill: 'rgba(255,255,255,0.05)'}}
                  contentStyle={{ backgroundColor: '#1e293b', borderColor: '#333' }}
                  itemStyle={{ color: '#fff' }}
              />
              <Bar dataKey="amount" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

       {/* Tax Revenue History (Stacked Bar) - Phase 5 */}
       <div className="glass-card p-6 flex flex-col md:col-span-2">
        <h3 className="text-lg font-semibold text-white mb-4">Tax Revenue History</h3>
        <div className="flex-1 min-h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={historyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="tick" stroke="#888" />
              <YAxis stroke="#888" />
              <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', borderColor: '#333' }}
                  itemStyle={{ color: '#fff' }}
              />
              <Legend />
              {taxKeys.map((key, index) => (
                  <Bar
                    key={key}
                    dataKey={key}
                    stackId="a"
                    fill={TAX_COLORS[index % TAX_COLORS.length]}
                  />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Welfare Spending Trend (Phase 5) */}
      <div className="glass-card p-6 flex flex-col md:col-span-3">
        <h3 className="text-lg font-semibold text-white mb-4">Welfare & Stimulus Trend</h3>
         <div className="flex-1 min-h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data.welfare_history}>
              <defs>
                <linearGradient id="colorWelfare" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorStimulus" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="tick" stroke="#888" />
              <YAxis stroke="#888" />
              <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', borderColor: '#333' }}
                  itemStyle={{ color: '#fff' }}
              />
              <Legend />
              <Area type="monotone" dataKey="welfare" stroke="#3b82f6" fillOpacity={1} fill="url(#colorWelfare)" />
              <Area type="monotone" dataKey="stimulus" stroke="#ef4444" fillOpacity={1} fill="url(#colorStimulus)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
