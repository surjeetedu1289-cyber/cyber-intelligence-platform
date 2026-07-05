export type IntelligenceItem = {
  id?: number | string;
  title: string;
  summary?: string;
  source?: string;
  category?: string;
  severity?: string;
  url?: string;
  tags?: string[];
  published_at?: string;
  subcategory?: string;
  source_group?: string;
  official_url?: string;
  executive_summary?: string;
  affected_industries?: string[];
  affected_iam_domains?: string[];
  control_mappings?: string[];
  recommended_actions?: string[];
  board_impact?: string;
  ciso_action_items?: string[];
  rankings?: {
    credibility: number;
    executive_relevance: number;
    business_impact: number;
    regulatory_importance: number;
    overall: number;
  };
};

export type PaginatedResponse<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
};

export type DashboardCount = {
  category?: string;
  source?: string;
  tag?: string;
  count: number;
};

export type AgentInsight = {
  agent: string;
  article_count: number;
  executive_summary: string;
  business_impact: string;
  iam_impact: string;
  risk_level: 'critical' | 'high' | 'medium' | 'low' | string;
  recommended_actions: string[];
  confidence_score: number;
  tags: string[];
};

export type ExecutiveSummary = {
  headline: string;
  summary: string;
  key_risks: string[];
  top_priorities: string[];
  confidence: string;
};

export type DashboardStats = {
  date: string;
  generated_at?: string | null;
  article_count: number;
  section_counts: Record<string, number>;
  top_categories: DashboardCount[];
  top_sources: DashboardCount[];
  top_tags: DashboardCount[];
  agents: AgentInsight[];
  executive_summary?: ExecutiveSummary | ExecutiveSummary[];
};

export type DashboardDimension = {
  name: string;
  count: number;
};

export type DashboardTrendPoint = {
  name: string;
  value: number;
};

export type DashboardPayload = {
  summary: ExecutiveSummary;
  articles: IntelligenceItem[];
  categories: DashboardDimension[];
  sources: DashboardDimension[];
  trendData: DashboardTrendPoint[];
  lastUpdated?: string | null;
  stats: {
    articleCount: number;
    categoryCount: number;
    sourceCount: number;
  };
  widgets?: Record<string, number>;
  sourceGroups?: DashboardDimension[];
  topExecutiveStories?: IntelligenceItem[];
  whatChangedSinceYesterday?: IntelligenceItem[];
};

export type ComplianceRecord = {
  title: string;
  summary?: string;
  url?: string;
  publishedAt?: string;
  country: string;
  regulator: string;
  framework: string[];
  control: string[];
  riskLevel: string;
  securityDomains: string[];
  affectedIndustries: string[];
  affectedTechnologies: string[];
  controlMapping: {
    frameworks: string[];
    controls: string[];
    introducesNewControl: boolean;
    changesExistingGuidance: boolean;
    impactsRegulatedFinancialInstitutions: boolean;
    impactsIAM: boolean;
    impactsAIGovernance: boolean;
    impactsCloudSecurity: boolean;
    impactsOperationalResilience: boolean;
    impactsThirdPartyRisk: boolean;
  };
  controlCrossReference: string[];
  executiveAnalysis: {
    executiveSummary: string;
    technicalSummary: string;
    businessImpact: string;
    operationalImpact: string;
    riskRating: string;
    likelihood: string;
    potentialFinancialImpact: string;
    affectedIndustries: string[];
    affectedTechnologies: string[];
    affectedControls: string[];
    affectedSecurityDomains: string[];
    recommendedActions: string[];
    priority: string;
    boardSummary: string;
  };
  smartImpactAnalysis: {
    whatChanged: string;
    whyItMatters: string;
    organisationsAffected: string[];
    businessUnitsAffected: string[];
    securityTeamsAffected: string[];
    iamControlsAffected: string[];
    apraCpsControlsAffected: string[];
    nistControlsAffected: string[];
    policiesToReview: string[];
    standardsToUpdate: string[];
    cisoWeeklyActions: string[];
    cioKeyTakeaway: string;
    boardKeyTakeaway: string;
  };
  ranking: {
    credibility: number;
    executiveRelevance: number;
    businessImpact: number;
    regulatoryImportance: number;
    overall: number;
  };
};

export type ComplianceControlIntelligencePayload = {
  module: string;
  audience: string[];
  prioritization: string;
  generatedAt: string;
  monitorScope: Record<string, Record<string, string[]>>;
  filtersApplied: Record<string, string | boolean | null>;
  availableFilters: Record<string, Array<string | boolean>>;
  widgets: Record<string, number>;
  dashboard: {
    frameworkUpdates: DashboardDimension[];
    regulatorUpdates: DashboardDimension[];
    controlsImpacted: DashboardDimension[];
    industryImpact: DashboardDimension[];
    securityDomains: DashboardDimension[];
  };
  boardReport: Record<string, string[]>;
  count: number;
  items: ComplianceRecord[];
};
