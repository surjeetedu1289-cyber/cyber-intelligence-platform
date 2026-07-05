import type { ComplianceControlIntelligencePayload, DashboardPayload, ExecutiveSummary, IntelligenceItem, PaginatedResponse } from './types';

const REQUEST_TIMEOUT_MS = 15000;
const MAX_RETRIES = 1;

function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, '');
}

function resolveApiBaseUrl(): string {
  const configuredBaseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
  if (configuredBaseUrl) {
    return trimTrailingSlash(configuredBaseUrl);
  }

  return '';
}

function normalizeBaseUrl(baseUrl: string): string {
  if (!baseUrl) {
    return '';
  }
  return baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`;
}

function resolveStaticDataBaseUrl(): string {
  const baseUrl = normalizeBaseUrl(import.meta.env.BASE_URL as string);
  return `${baseUrl}data`;
}

const API_BASE_URL = resolveApiBaseUrl();
const STATIC_DATA_BASE_URL = resolveStaticDataBaseUrl();
const USE_STATIC_DATA = API_BASE_URL.length === 0;

function buildApiUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}

function buildStaticUrl(fileName: string): string {
  return `${STATIC_DATA_BASE_URL}/${fileName}`;
}

function buildError(message: string): Error {
  return new Error(`Dashboard is currently updating. ${message}`);
}

function toPaginatedResponse(items: IntelligenceItem[]): PaginatedResponse<IntelligenceItem> {
  return {
    items,
    page: 1,
    page_size: items.length,
    total: items.length,
    pages: 1,
  };
}

function filterByCategory(items: IntelligenceItem[], category: string): IntelligenceItem[] {
  return items.filter((item) => String(item.category ?? '').toLowerCase() === category.toLowerCase());
}

async function fetchRawJson<T>(url: string): Promise<T> {
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt += 1) {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
      const response = await fetch(url, {
        signal: controller.signal,
        cache: 'no-store',
      });
      if (!response.ok) {
        const body = await response.text();
        const details = body ? `: ${body}` : '';
        throw new Error(`Request failed (${response.status}) for ${url}${details}`);
      }
      return (await response.json()) as T;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unexpected network error.';
      const isLastAttempt = attempt >= MAX_RETRIES;
      if (isLastAttempt) {
        throw buildError(message);
      }
    } finally {
      window.clearTimeout(timeoutId);
    }
  }

  throw buildError(`Unable to load ${url}`);
}

async function fetchApiJson<T>(path: string): Promise<T> {
  return fetchRawJson<T>(buildApiUrl(path));
}

async function fetchStaticJson<T>(fileName: string): Promise<T> {
  return fetchRawJson<T>(buildStaticUrl(fileName));
}

async function fetchJson<T>(apiPath: string, staticFileName: string): Promise<T> {
  if (USE_STATIC_DATA) {
    return fetchStaticJson<T>(staticFileName);
  }

  return fetchApiJson<T>(apiPath);
}

async function fetchStaticItems(fileName: string): Promise<IntelligenceItem[]> {
  const payload = await fetchStaticJson<unknown>(fileName);
  if (Array.isArray(payload)) {
    return payload as IntelligenceItem[];
  }

  if (payload && typeof payload === 'object' && Array.isArray((payload as { items?: unknown }).items)) {
    return (payload as { items: IntelligenceItem[] }).items;
  }

  return [];
}

export async function fetchNews(): Promise<PaginatedResponse<IntelligenceItem>> {
  if (USE_STATIC_DATA) {
    return toPaginatedResponse(await fetchStaticItems('news.json'));
  }

  return fetchApiJson<PaginatedResponse<IntelligenceItem>>('/news');
}

export async function fetchDashboard(): Promise<DashboardPayload> {
  return fetchJson<DashboardPayload>('/dashboard', 'dashboard.json');
}

export async function fetchSummary(): Promise<ExecutiveSummary> {
  return fetchJson<ExecutiveSummary>('/summary', 'executive-summary.json');
}

export async function fetchVendors(): Promise<PaginatedResponse<IntelligenceItem>> {
  if (USE_STATIC_DATA) {
    const allItems = await fetchStaticItems('news.json');
    return toPaginatedResponse(filterByCategory(allItems, 'Vendor'));
  }

  return fetchApiJson<PaginatedResponse<IntelligenceItem>>('/vendors');
}

export async function fetchRegulations(): Promise<PaginatedResponse<IntelligenceItem>> {
  if (USE_STATIC_DATA) {
    return toPaginatedResponse(await fetchStaticItems('regulations.json'));
  }

  return fetchApiJson<PaginatedResponse<IntelligenceItem>>('/regulations');
}

export async function fetchThreats(): Promise<PaginatedResponse<IntelligenceItem>> {
  if (USE_STATIC_DATA) {
    return toPaginatedResponse(await fetchStaticItems('threats.json'));
  }

  return fetchApiJson<PaginatedResponse<IntelligenceItem>>('/threats');
}

export async function fetchResearch(): Promise<PaginatedResponse<IntelligenceItem>> {
  if (USE_STATIC_DATA) {
    return toPaginatedResponse(await fetchStaticItems('research.json'));
  }

  return fetchApiJson<PaginatedResponse<IntelligenceItem>>('/research');
}

export async function fetchComplianceControlIntelligence(
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
  }> = {},
): Promise<ComplianceControlIntelligencePayload> {
  if (USE_STATIC_DATA) {
    return fetchStaticJson<ComplianceControlIntelligencePayload>('regulations.json');
  }

  const params = new URLSearchParams();

  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === null || value === '') {
      continue;
    }
    params.set(key, String(value));
  }

  const query = params.toString();
  return fetchApiJson<ComplianceControlIntelligencePayload>(`/compliance-control-intelligence${query ? `?${query}` : ''}`);
}
