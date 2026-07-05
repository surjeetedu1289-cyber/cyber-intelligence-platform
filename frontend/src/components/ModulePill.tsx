type ModulePillProps = {
  label: string;
  darkMode: boolean;
};

export function ModulePill({ label, darkMode }: ModulePillProps) {
  return (
    <span className={darkMode ? 'rounded-full border border-slate-700 bg-slate-800 px-3 py-1 text-sm text-slate-300' : 'rounded-full border border-slate-200 bg-slate-100 px-3 py-1 text-sm text-slate-700'}>
      {label}
    </span>
  );
}
