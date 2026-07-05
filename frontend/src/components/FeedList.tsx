import type { IntelligenceItem } from '../types';

type FeedListProps = {
  items: IntelligenceItem[];
  darkMode: boolean;
};

export function FeedList({ items, darkMode }: FeedListProps) {
  if (!items.length) {
    return <p className="text-sm text-slate-500">No items match the current filters.</p>;
  }

  return (
    <div className="space-y-3">
      {items.map((item, index) => (
        <article key={item.id ?? `${item.title}-${index}`} className={darkMode ? 'rounded-xl border border-slate-800 bg-slate-950/50 p-4' : 'rounded-xl border border-slate-200 bg-slate-50 p-4'}>
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs uppercase tracking-[0.2em] text-cyan-400">{item.category ?? 'Intelligence'}{item.subcategory ? ` / ${item.subcategory}` : ''}</p>
            <span className="text-xs text-slate-500">{item.source ?? 'Source'}</span>
          </div>
          <h3 className="mt-2 font-semibold">{item.title}</h3>
          <p className="mt-2 text-sm text-slate-400">{item.executive_summary ?? item.summary}</p>
          <div className="mt-3 flex items-center gap-4 text-xs text-slate-500">
            <span>{item.source_group ?? 'General Sources'}</span>
            {typeof item.rankings?.overall === 'number' ? <span>Rank: {item.rankings.overall.toFixed(2)}</span> : null}
          </div>
          <div className="mt-3 flex items-center gap-3">
            {item.url ? (
              <a
                href={item.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex text-xs font-medium uppercase tracking-[0.18em] text-cyan-400 transition hover:text-cyan-300"
              >
                Read details
              </a>
            ) : null}
            {item.official_url ? (
              <a
                href={item.official_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex text-xs font-medium uppercase tracking-[0.18em] text-emerald-400 transition hover:text-emerald-300"
              >
                Source link
              </a>
            ) : null}
          </div>
          {item.tags?.length ? (
            <div className="mt-3 flex flex-wrap gap-2">
              {item.tags.map((tag) => (
                <span key={tag} className={darkMode ? 'rounded-full border border-slate-700 px-2 py-1 text-xs text-slate-400' : 'rounded-full border border-slate-200 px-2 py-1 text-xs text-slate-600'}>
                  {tag}
                </span>
              ))}
            </div>
          ) : null}
        </article>
      ))}
    </div>
  );
}
