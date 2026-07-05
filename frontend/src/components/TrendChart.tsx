import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

type TrendChartProps = {
  data: Array<{ name: string; value: number }>;
  darkMode: boolean;
};

export function TrendChart({ data, darkMode }: TrendChartProps) {
  return (
    <div className="mt-4 h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? '#334155' : '#cbd5e1'} />
          <XAxis dataKey="name" stroke={darkMode ? '#cbd5e1' : '#475569'} tick={{ fontSize: 12 }} />
          <YAxis stroke={darkMode ? '#cbd5e1' : '#475569'} />
          <Tooltip />
          <Bar dataKey="value" fill="#22d3ee" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
