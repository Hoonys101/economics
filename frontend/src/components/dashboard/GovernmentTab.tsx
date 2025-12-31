import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';
import { GovernmentTabData } from '../../types/dashboard';

const TAX_COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b'];

interface GovernmentTabProps {
  data: GovernmentTabData;
}

export default function GovernmentTab({ data }: GovernmentTabProps) {
  if (!data) return <div className="text-muted-foreground p-4">No data available</div>;

  const taxData = Object.entries(data.tax_revenue).map(([key, value]) => ({
    name: key,
    value: value
  }));

  const balanceData = [
    { name: 'Revenue', amount: data.fiscal_balance.revenue, fill: '#10b981' },
    { name: 'Expense', amount: data.fiscal_balance.expense, fill: '#ef4444' }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full h-full">
      {/* Tax Revenue Distribution */}
      <div className="glass-card p-6 flex flex-col">
        <h3 className="text-lg font-semibold text-white mb-4">Tax Revenue Composition</h3>
        <div className="flex-1 min-h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={taxData}
                cx="50%"
                cy="50%"
                labelLine={false}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent ? percent * 100 : 0).toFixed(0)}%`}
              >
                {taxData.map((_entry, index) => (
                  <Cell key={`cell-${index}`} fill={TAX_COLORS[index % TAX_COLORS.length]} />
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
      </div>

      {/* Fiscal Balance */}
      <div className="glass-card p-6 flex flex-col">
        <h3 className="text-lg font-semibold text-white mb-4">Fiscal Balance</h3>
        <div className="flex-1 min-h-[300px]">
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
    </div>
  );
}
