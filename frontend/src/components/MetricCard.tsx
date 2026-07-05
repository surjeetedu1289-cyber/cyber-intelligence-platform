type MetricCardProps = {
  label: string;
  value: string | number;
  helper?: string;
  darkMode: boolean;
};

export function MetricCard({ label, value, helper, darkMode }: MetricCardProps) {
  return (
    <div className={darkMode ? 'rounded-2xl border border-slate-800 bg-slate-900/70 p-5' : 'rounded-2xl border border-slate-200 bg-white p-5 shadow-sm'}>
      <p className="text-sm text-slate-400">{label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-tight">{value}</p>
      {helper ? <p className="mt-2 text-sm text-slate-500">{helper}</p> : null}
    </div>
  );
}
