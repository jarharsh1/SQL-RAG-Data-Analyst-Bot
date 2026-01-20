export interface MetricDefinition {
  name: string;
  formula: string;
  source_table: string;
  grain: string;
  filters?: string[];
  citation?: Citation;
}

export interface Citation {
  source: string;
  location?: string;
  content: string;
  relevance_score: number;
}

export interface TransparencyInfo {
  sql_executed: string;
  definitions_used: MetricDefinition[];
  tables_accessed: Record<string, any>;
  assumptions: string[];
  citations: Citation[];
  business_rules_applied: string[];
}

export interface QueryData {
  data: Array<Record<string, any>>;
  columns: string[];
  row_count: number;
  execution_time_ms: number;
  truncated: boolean;
  error?: string;
}

export interface QueryMetadata {
  execution_time_ms: number;
  rows_returned: number;
  timestamp: string;
  agent_state_history: string[];
}

export interface SuggestedAction {
  type: string;
  label: string;
  description?: string;
  requires_confirmation: boolean;
}

export interface QueryResponse {
  answer: string;
  transparency?: TransparencyInfo;
  data?: QueryData;
  metadata: QueryMetadata;
  suggested_actions: SuggestedAction[];
  error?: string;
}
