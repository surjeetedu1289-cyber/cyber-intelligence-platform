import { Suspense, lazy, useEffect, useMemo, useState } from 'react';
import { fetchComplianceControlIntelligence, fetchDashboard } from './api';
import { FeedList } from './components/FeedList';
import { MetricCard } from './components/MetricCard';
import { SectionCard } from './components/SectionCard';
import type { ComplianceControlIntelligencePayload, DashboardPayload, ExecutiveSummary, IntelligenceItem } from './types';

const REFRESH_MS = 15 * 60 * 1000;
const UPDATE_MESSAGE = 'Dashboard is currently updating';
const TrendChart = lazy(() => import('./components/TrendChart').then((module) => ({ default: module.TrendChart })));

const EMPTY_SUMMARY: ExecutiveSummary = {
  headline: 'Daily cyber intelligence summary',
  summary: 'Executive summary will appear after backend enrichment completes.',
  key_risks: [],
  top_priorities: [],
  confidence: 'medium',
};

const EMPTY_DASHBOARD: DashboardPayload = {
  summary: EMPTY_SUMMARY,
  articles: [],
  categories: [],
  sources: [],
  trendData: [],
  lastUpdated: null,
  stats: {
    articleCount: 0,
    categoryCount: 0,
    sourceCount: 0,
  },
  widgets: {},
  sourceGroups: [],
  topExecutiveStories: [],
  whatChangedSinceYesterday: [],
};

const EMPTY_COMPLIANCE: ComplianceControlIntelligencePayload = {
  module: 'Compliance & Control Intelligence',
  audience: [],
  prioritization: 'executive_relevance_over_publication_date',
  generatedAt: '',
  monitorScope: {},
  filtersApplied: {},
  availableFilters: {
    country: [],
    framework: [],
    regulator: [],
    control: [],
    industry: [],
    riskLevel: [],
    securityDomain: [],
    identity: [true, false],
    cloud: [true, false],
    ai: [true, false],
    operationalResilience: [true, false],
    privacy: [true, false],
    criticalInfrastructure: [true, false],
  },
  widgets: {},
  dashboard: {
    frameworkUpdates: [],
    regulatorUpdates: [],
    controlsImpacted: [],
    industryImpact: [],
    securityDomains: [],
  },
  boardReport: {},
  count: 0,
  items: [],
};

export default function App() {
  const [activeModule, setActiveModule] = useState<'executive' | 'compliance'>('executive');
  const [dashboard, setDashboard] = useState<DashboardPayload>(EMPTY_DASHBOARD);
  const [compliance, setCompliance] = useState<ComplianceControlIntelligencePayload>(EMPTY_COMPLIANCE);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [complianceFilters, setComplianceFilters] = useState<{
    country?: string;
    framework?: string;
    regulator?: string;
    control?: string;
    industry?: string;
    risk_level?: string;
    security_domain?: string;
    identity?: boolean;
    cloud?: boolean;
    ai?: boolean;
    operational_resilience?: boolean;
    privacy?: boolean;
    critical_infrastructure?: boolean;
  }>({});
  const [darkMode, setDarkMode] = useState(true);
  const [loading, setLoading] = useState(true);
  const [complianceLoading, setComplianceLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [complianceError, setComplianceError] = useState<string | null>(null);

  const items = dashboard.articles;
  const summary = dashboard.summary;

  const categories = useMemo(() => {
    return dashboard.categories.map((entry) => entry.name).filter(Boolean).sort();
  }, [dashboard.categories]);

  const loadDashboardData = async (backgroundRefresh = false) => {
    if (backgroundRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    setError(null);

    try {
      const payload = await fetchDashboard();
      setDashboard(payload);
    } catch (fetchError) {
      const message = fetchError instanceof Error ? fetchError.message : UPDATE_MESSAGE;
      setError(message.includes(UPDATE_MESSAGE) ? UPDATE_MESSAGE : `${UPDATE_MESSAGE}.`);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const loadComplianceData = async (
    filters: Partial<{
      country: string;
      framework: string;
      regulator: string;
      control: string;
      industry: string;
      risk_level: string;
      security_domain: string;
      identity: boolean;
      cloud: boolean;
      ai: boolean;
      operational_resilience: boolean;
      privacy: boolean;
      critical_infrastructure: boolean;
    }> = complianceFilters,
  ) => {
    setComplianceLoading(true);
    setComplianceError(null);

    try {
      const payload = await fetchComplianceControlIntelligence(filters);
      setCompliance(payload);
    } catch (fetchError) {
      const message = fetchError instanceof Error ? fetchError.message : UPDATE_MESSAGE;
      setComplianceError(message.includes(UPDATE_MESSAGE) ? UPDATE_MESSAGE : `${UPDATE_MESSAGE}.`);
    } finally {
      setComplianceLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData(false);
    loadComplianceData({});

    const timer = window.setInterval(() => {
      loadDashboardData(true);
    }, REFRESH_MS);

    return () => window.clearInterval(timer);
  }, []);

  const complianceFeedItems = useMemo<IntelligenceItem[]>(() => {
    return compliance.items.map((item, index) => ({
      id: `${item.title}-${index}`,
      title: item.title,
      summary: item.summary,
      source: item.regulator,
      category: item.framework[0] ?? 'Compliance',
      severity: item.riskLevel,
      url: item.url,
      published_at: item.publishedAt,
      subcategory: item.control[0] ?? 'Control Impact',
      source_group: item.country,
      executive_summary: item.executiveAnalysis.executiveSummary,
      tags: item.securityDomains,
      rankings: {
        credibility: item.ranking.credibility,
        executive_relevance: item.ranking.executiveRelevance,
        business_impact: item.ranking.businessImpact,
        regulatory_importance: item.ranking.regulatoryImportance,
        overall: item.ranking.overall,
      },
    }));
  }, [compliance.items]);

  const filterChoices = useMemo(() => {
    const pick = (key: string) => (compliance.availableFilters[key] ?? []).filter((entry): entry is string => typeof entry === 'string');
    return {
      country: pick('country'),
      framework: pick('framework'),
      regulator: pick('regulator'),
      control: pick('control'),
      industry: pick('industry'),
      riskLevel: pick('riskLevel'),
      securityDomain: pick('securityDomain'),
    };
  }, [compliance.availableFilters]);

  const updateComplianceFilter = (key: string, value: string | boolean | undefined) => {
    setComplianceFilters((current) => ({
      ...current,
      [key]: value,
    }));
  };

  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      const haystack = `${item.title} ${item.summary ?? ''} ${item.source ?? ''}`.toLowerCase();
      const matchesSearch = haystack.includes(search.toLowerCase());
      const matchesCategory = selectedCategory === 'All' || item.category === selectedCategory;
      return matchesSearch && matchesCategory;
    });
  }, [items, search, selectedCategory]);

  const chartData = useMemo(() => {
    return dashboard.trendData;
  }, [dashboard.trendData]);

  const sectionTrendData = useMemo(() => {
    return (dashboard.sourceGroups ?? []).slice(0, 20).map((entry) => ({ name: entry.name, value: entry.count }));
  }, [dashboard.sourceGroups]);

  const executiveWidgets = useMemo(() => {
    const widgetSource = dashboard.widgets ?? {};
    return [
      { key: 'australianRegulatoryUpdates', label: 'Australian Regulatory Updates' },
      { key: 'globalRegulatoryUpdates', label: 'Global Regulatory Updates' },
      { key: 'nistUpdates', label: 'NIST Updates' },
      { key: 'apraUpdates', label: 'APRA Updates' },
      { key: 'asicUpdates', label: 'ASIC Updates' },
      { key: 'asdAcscAdvisories', label: 'ASD / ACSC Advisories' },
      { key: 'identityAndAccessManagement', label: 'Identity & Access Management' },
      { key: 'aiSecurity', label: 'AI Security' },
      { key: 'threatIntelligence', label: 'Threat Intelligence' },
      { key: 'researchPapers', label: 'Research Papers' },
      { key: 'emergingRisks', label: 'Emerging Risks' },
      { key: 'top10ExecutiveStories', label: 'Top 10 Executive Stories' },
      { key: 'whatChangedSinceYesterday', label: 'What Changed Since Yesterday' },
    ].map((entry) => ({ ...entry, value: widgetSource[entry.key] ?? 0 }));
  }, [dashboard.widgets]);

  const lastUpdatedLabel = useMemo(() => {
    if (!dashboard.lastUpdated) {
      return 'Not available';
    }

    const parsed = new Date(dashboard.lastUpdated);
    if (Number.isNaN(parsed.getTime())) {
      return dashboard.lastUpdated;
    }

    return parsed.toLocaleString();
  }, [dashboard.lastUpdated]);

  return (
    <div className={darkMode ? 'min-h-screen bg-slate-950 text-slate-100' : 'min-h-screen bg-slate-50 text-slate-900'}>
      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <header className={darkMode ? 'rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-2xl shadow-black/20' : 'rounded-2xl border border-slate-200 bg-white p-6 shadow-lg'}>
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.35em] text-cyan-400">Cyber Intelligence Platform</p>
              <h1 className="mt-2 text-3xl font-semibold tracking-tight">Executive Intelligence Platform</h1>
              <p className="mt-3 max-w-2xl text-sm text-slate-400">Priority intelligence for CISOs, CIOs, CTOs, and Heads of Identity with emphasis on authoritative regulatory and standards sources.</p>
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  onClick={() => setActiveModule('executive')}
                  className={activeModule === 'executive' ? 'rounded-full border border-cyan-500 bg-cyan-500/20 px-3 py-1 text-xs text-cyan-200' : 'rounded-full border border-slate-600 px-3 py-1 text-xs text-slate-300'}
                >
                  Executive Intelligence
                </button>
                <button
                  onClick={() => setActiveModule('compliance')}
                  className={activeModule === 'compliance' ? 'rounded-full border border-emerald-500 bg-emerald-500/20 px-3 py-1 text-xs text-emerald-200' : 'rounded-full border border-slate-600 px-3 py-1 text-xs text-slate-300'}
                >
                  Compliance & Control Intelligence
                </button>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={darkMode ? 'rounded-full border border-cyan-500/40 bg-cyan-500/10 px-3 py-2 text-xs text-cyan-200' : 'rounded-full border border-cyan-200 bg-cyan-50 px-3 py-2 text-xs text-cyan-700'}>
                Last updated: {lastUpdatedLabel}
              </span>
              <button onClick={() => setDarkMode((value) => !value)} className="rounded-full border border-cyan-500 px-4 py-2 text-sm font-medium text-cyan-400 transition hover:bg-cyan-500/10">
                {darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
              </button>
            </div>
          </div>
        </header>

        {loading ? (
          <div className={darkMode ? 'rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-sm text-slate-300' : 'rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-600'}>
            Loading dashboard data...
          </div>
        ) : null}

        {error ? (
          <div className={darkMode ? 'rounded-2xl border border-rose-500/40 bg-rose-900/30 p-4 text-sm text-rose-200' : 'rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700'}>
            <div className="flex items-center justify-between gap-3">
              <span>{error}</span>
              <button
                onClick={() => loadDashboardData(false)}
                className={darkMode ? 'rounded-lg border border-rose-300/50 px-3 py-1 text-xs text-rose-100 hover:bg-rose-500/20' : 'rounded-lg border border-rose-300 px-3 py-1 text-xs text-rose-700 hover:bg-rose-100'}
              >
                Retry
              </button>
            </div>
          </div>
        ) : null}

        <section className="grid gap-4 md:grid-cols-3">
          {activeModule === 'executive' ? (
            <>
              <MetricCard label="Article count" value={dashboard.stats.articleCount} helper="Live intelligence items for today" darkMode={darkMode} />
              <MetricCard label="Category count" value={dashboard.stats.categoryCount} helper="Distinct intelligence categories" darkMode={darkMode} />
              <MetricCard label="Sources tracked" value={dashboard.stats.sourceCount} helper={refreshing ? 'Refreshing live data...' : 'Auto refresh: every 15 minutes'} darkMode={darkMode} />
            </>
          ) : (
            <>
              <MetricCard label="Compliance items" value={compliance.count} helper="Prioritized by executive relevance" darkMode={darkMode} />
              <MetricCard label="Framework updates" value={compliance.dashboard.frameworkUpdates.length} helper="Distinct frameworks with updates" darkMode={darkMode} />
              <MetricCard label="Regulators tracked" value={compliance.dashboard.regulatorUpdates.length} helper={complianceLoading ? 'Refreshing compliance intelligence...' : 'Filterable by regulator and control'} darkMode={darkMode} />
            </>
          )}
        </section>

        {activeModule === 'executive' ? (
          <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {executiveWidgets.map((widget) => (
              <article key={widget.key} className={darkMode ? 'rounded-xl border border-slate-800 bg-slate-900/70 p-3' : 'rounded-xl border border-slate-200 bg-white p-3'}>
                <p className="text-xs uppercase tracking-[0.18em] text-cyan-400">{widget.label}</p>
                <p className="mt-2 text-2xl font-semibold">{widget.value}</p>
              </article>
            ))}
          </section>
        ) : (
          <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {Object.entries(compliance.widgets).map(([key, value]) => (
              <article key={key} className={darkMode ? 'rounded-xl border border-slate-800 bg-slate-900/70 p-3' : 'rounded-xl border border-slate-200 bg-white p-3'}>
                <p className="text-xs uppercase tracking-[0.18em] text-emerald-400">{key.replace(/([A-Z])/g, ' $1').trim()}</p>
                <p className="mt-2 text-2xl font-semibold">{value}</p>
              </article>
            ))}
          </section>
        )}

        {activeModule === 'executive' ? (
          <>
            <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
              <SectionCard title="Intelligence feed" subtitle="Filtered news, threats, and research" darkMode={darkMode}>
                <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <div className="flex flex-col gap-2 sm:flex-row">
                    <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search intelligence" className={darkMode ? 'rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm' : 'rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm'} />
                    <select value={selectedCategory} onChange={(event) => setSelectedCategory(event.target.value)} className={darkMode ? 'rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm' : 'rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm'}>
                      <option value="All">All categories</option>
                      {categories.map((category) => (
                        <option key={category} value={category}>
                          {category}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <FeedList items={filteredItems} darkMode={darkMode} />
              </SectionCard>

              <SectionCard title="Category trend chart" subtitle="Top categories in today's intelligence" darkMode={darkMode}>
                <Suspense fallback={<p className="text-sm text-slate-400">Loading chart...</p>}>
                  <TrendChart data={chartData} darkMode={darkMode} />
                </Suspense>
              </SectionCard>
            </section>

            <section className="grid gap-6 lg:grid-cols-[1fr_1fr]">
              <SectionCard title="Domain trend chart" subtitle="News, vendors, regulations, threats, and research volumes" darkMode={darkMode}>
                <Suspense fallback={<p className="text-sm text-slate-400">Loading chart...</p>}>
                  <TrendChart data={sectionTrendData} darkMode={darkMode} />
                </Suspense>
              </SectionCard>

              <SectionCard title="Executive summary" subtitle="Daily leadership brief from AI enrichment" darkMode={darkMode}>
                <div className="space-y-3 text-sm">
                  <p className="text-base font-semibold">{summary?.headline ?? EMPTY_SUMMARY.headline}</p>
                  <p className="text-slate-400">{summary?.summary ?? EMPTY_SUMMARY.summary}</p>
                  {summary?.top_priorities?.length ? (
                    <ul className="list-disc space-y-1 pl-5 text-slate-300">
                      {summary.top_priorities.slice(0, 3).map((priority) => (
                        <li key={priority}>{priority}</li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              </SectionCard>
            </section>

            <section className="grid gap-6 lg:grid-cols-[1fr_1fr]">
              <SectionCard title="Top 10 executive stories" subtitle="Ranked by credibility, executive relevance, business impact and regulatory importance" darkMode={darkMode}>
                <FeedList items={dashboard.topExecutiveStories ?? []} darkMode={darkMode} />
              </SectionCard>
              <SectionCard title="What changed since yesterday" subtitle="Newly published items captured in the current cycle" darkMode={darkMode}>
                <FeedList items={dashboard.whatChangedSinceYesterday ?? []} darkMode={darkMode} />
              </SectionCard>
            </section>
          </>
        ) : (
          <>
            {complianceError ? (
              <div className={darkMode ? 'rounded-2xl border border-rose-500/40 bg-rose-900/30 p-4 text-sm text-rose-200' : 'rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700'}>
                <div className="flex items-center justify-between gap-3">
                  <span>{complianceError}</span>
                  <button
                    onClick={() => loadComplianceData(complianceFilters)}
                    className={darkMode ? 'rounded-lg border border-rose-300/50 px-3 py-1 text-xs text-rose-100 hover:bg-rose-500/20' : 'rounded-lg border border-rose-300 px-3 py-1 text-xs text-rose-700 hover:bg-rose-100'}
                  >
                    Retry
                  </button>
                </div>
              </div>
            ) : null}

            <section className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
              <SectionCard title="Compliance Filters" subtitle="Filter by regulator, framework, control, risk, and security domain" darkMode={darkMode}>
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  <select value={complianceFilters.country ?? ''} onChange={(event) => updateComplianceFilter('country', event.target.value || undefined)} className={darkMode ? 'rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm' : 'rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm'}>
                    <option value="">Country</option>
                    {filterChoices.country.map((entry) => <option key={entry} value={entry}>{entry}</option>)}
                  </select>
                  <select value={complianceFilters.framework ?? ''} onChange={(event) => updateComplianceFilter('framework', event.target.value || undefined)} className={darkMode ? 'rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm' : 'rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm'}>
                    <option value="">Framework</option>
                    {filterChoices.framework.map((entry) => <option key={entry} value={entry}>{entry}</option>)}
                  </select>
                  <select value={complianceFilters.regulator ?? ''} onChange={(event) => updateComplianceFilter('regulator', event.target.value || undefined)} className={darkMode ? 'rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm' : 'rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm'}>
                    <option value="">Regulator</option>
                    {filterChoices.regulator.map((entry) => <option key={entry} value={entry}>{entry}</option>)}
                  </select>
                  <select value={complianceFilters.control ?? ''} onChange={(event) => updateComplianceFilter('control', event.target.value || undefined)} className={darkMode ? 'rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm' : 'rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm'}>
                    <option value="">Control</option>
                    {filterChoices.control.map((entry) => <option key={entry} value={entry}>{entry}</option>)}
                  </select>
                  <select value={complianceFilters.industry ?? ''} onChange={(event) => updateComplianceFilter('industry', event.target.value || undefined)} className={darkMode ? 'rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm' : 'rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm'}>
                    <option value="">Industry</option>
                    {filterChoices.industry.map((entry) => <option key={entry} value={entry}>{entry}</option>)}
                  </select>
                  <select value={complianceFilters.risk_level ?? ''} onChange={(event) => updateComplianceFilter('risk_level', event.target.value || undefined)} className={darkMode ? 'rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm' : 'rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm'}>
                    <option value="">Risk Level</option>
                    {filterChoices.riskLevel.map((entry) => <option key={entry} value={entry}>{entry}</option>)}
                  </select>
                  <select value={complianceFilters.security_domain ?? ''} onChange={(event) => updateComplianceFilter('security_domain', event.target.value || undefined)} className={darkMode ? 'rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm' : 'rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm'}>
                    <option value="">Security Domain</option>
                    {filterChoices.securityDomain.map((entry) => <option key={entry} value={entry}>{entry}</option>)}
                  </select>
                </div>
                <div className="mt-4 flex flex-wrap items-center gap-4 text-xs">
                  {[
                    ['identity', 'Identity'],
                    ['cloud', 'Cloud'],
                    ['ai', 'AI'],
                    ['operational_resilience', 'Operational Resilience'],
                    ['privacy', 'Privacy'],
                    ['critical_infrastructure', 'Critical Infrastructure'],
                  ].map(([key, label]) => (
                    <label key={key} className="inline-flex items-center gap-2">
                      <input type="checkbox" checked={Boolean((complianceFilters as Record<string, boolean | undefined>)[key])} onChange={(event) => updateComplianceFilter(key, event.target.checked ? true : undefined)} />
                      <span>{label}</span>
                    </label>
                  ))}
                </div>
                <div className="mt-4 flex items-center gap-3">
                  <button onClick={() => loadComplianceData(complianceFilters)} className="rounded-lg border border-emerald-500 px-3 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-emerald-300 hover:bg-emerald-500/10">Apply filters</button>
                  <button
                    onClick={() => {
                      setComplianceFilters({});
                      loadComplianceData({});
                    }}
                    className="rounded-lg border border-slate-500 px-3 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-slate-300 hover:bg-slate-500/10"
                  >
                    Clear
                  </button>
                </div>
              </SectionCard>

              <SectionCard title="Compliance Trends" subtitle="Framework updates by volume" darkMode={darkMode}>
                <Suspense fallback={<p className="text-sm text-slate-400">Loading chart...</p>}>
                  <TrendChart data={compliance.dashboard.frameworkUpdates.slice(0, 20).map((entry) => ({ name: entry.name, value: entry.count }))} darkMode={darkMode} />
                </Suspense>
              </SectionCard>
            </section>

            <section className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
              <SectionCard title="Compliance Intelligence Feed" subtitle={complianceLoading ? 'Loading compliance intelligence...' : 'Regulatory and control updates prioritized for executives'} darkMode={darkMode}>
                <FeedList items={complianceFeedItems} darkMode={darkMode} />
              </SectionCard>
              <SectionCard title="Weekly Board Report" subtitle="Automated board-ready recommendations" darkMode={darkMode}>
                <div className="space-y-3 text-sm">
                  {Object.entries(compliance.boardReport).slice(0, 6).map(([key, values]) => (
                    <div key={key}>
                      <p className="text-xs uppercase tracking-[0.16em] text-emerald-400">{key.replace(/([A-Z])/g, ' $1').trim()}</p>
                      <ul className="mt-1 list-disc space-y-1 pl-4 text-slate-300">
                        {(values as string[]).slice(0, 3).map((value) => (
                          <li key={value}>{value}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </SectionCard>
            </section>
          </>
        )}
      </div>
    </div>
  );
}
