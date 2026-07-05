import type { ReactNode } from 'react';

type SectionCardProps = {
  title: string;
  subtitle?: string;
  children: ReactNode;
  darkMode: boolean;
};

export function SectionCard({ title, subtitle, children, darkMode }: SectionCardProps) {
  return (
    <section className={darkMode ? 'rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-2xl shadow-black/20' : 'rounded-2xl border border-slate-200 bg-white p-5 shadow-sm'}>
      <div className="mb-4">
        <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
        {subtitle ? <p className="mt-1 text-sm text-slate-400">{subtitle}</p> : null}
      </div>
      {children}
    </section>
  );
}
