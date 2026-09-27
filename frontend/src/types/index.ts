export type BlockchainType = 'ethereum' | 'tron' | 'bitcoin' | 'solana';

export type FraudType = 
  | 'investment_scam'
  | 'ransomware'
  | 'sextortion'
  | 'phishing'
  | 'task_based_fraud'
  | 'darknet'
  | 'other';

export type CaseStatus = 'active' | 'under_investigation' | 'closed' | 'archived';

export interface Case {
  case_id: string;
  case_number: string;
  title: string;
  reported_wallet_address: string;
  reported_transaction_hash?: string | null;
  blockchain: BlockchainType;
  fraud_type: FraudType;
  reported_amount?: string | number | null;
  reported_asset?: string | null;
  reported_date?: string | null;
  status: CaseStatus;
  investigator_id: string;
  investigator_notes?: string | null;
  demo_data: boolean;
  data_source?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CaseCreatePayload {
  title: string;
  reported_wallet_address: string;
  reported_transaction_hash?: string | null;
  blockchain: BlockchainType;
  fraud_type: FraudType;
  reported_amount?: number | string | null;
  reported_asset?: string | null;
  reported_date?: string | null;
  investigator_notes?: string | null;
}

export interface TraceParameters {
  direction: 'outbound' | 'inbound' | 'both';
  max_hops: number;
  max_branches: number;
  min_amount?: number | string | null;
  asset_filters?: string[] | null;
  time_range_start?: string | null;
  time_range_end?: string | null;
}

export interface TraceRequestPayload {
  start_wallet_address?: string;
  direction?: 'outbound' | 'inbound' | 'both';
  max_hops?: number;
  max_branches?: number;
  min_amount?: number | string | null;
  asset_filters?: string[] | null;
  time_range_start?: string | null;
  time_range_end?: string | null;
}

export interface CanonicalTransaction {
  chain: string;
  transaction_hash: string;
  block_number?: number | null;
  block_timestamp?: string | null;
  from_address: string;
  to_address?: string | null;
  asset?: string | null;
  asset_type: string;
  amount: string | number;
  decimals: number;
  token_contract?: string | null;
  transfer_category: string;
  transaction_type: string;
  status: string;
  gas_used?: number | null;
  max_fee_per_gas?: string | number | null;
  priority_fee_per_gas?: string | number | null;
  total_fee?: string | number | null;
  provider: string;
  provider_reference: string;
  raw_reference?: string | null;
}

export interface GraphNode {
  id: string;
  type: string;
  label?: string | null;
  hop: number;
  metadata?: {
    balance?: string | number;
    transaction_count?: number;
    first_seen?: string;
    last_seen?: string;
    tags?: string[];
    [key: string]: unknown;
  };
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  transaction_hash: string;
  amount: string | number;
  asset?: string | null;
  timestamp?: string | null;
  hop: number;
}

export interface GraphSummary {
  root_wallet_address: string;
  blockchain: string;
  node_count: number;
  edge_count: number;
  max_hop_depth: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface TraceSummary {
  wallet_count: number;
  transaction_count: number;
  edge_count: number;
  max_hop_depth: number;
  assets_transferred: Record<string, string | number>;
  pages_fetched: number;
  provider?: string | null;
}

export interface TraceResponse {
  trace_id: string;
  case_id: string;
  status: string;
  result_status: string;
  start_wallet_address: string;
  blockchain: string;
  direction: string;
  parameters: TraceParameters;
  summary: TraceSummary;
  transactions: CanonicalTransaction[];
  graph?: GraphSummary | null;
  errors: string[];
  provider?: string | null;
  created_at?: string | null;
  completed_at?: string | null;
}

export interface Citation {
  type: string;
  reference_id: string;
  summary: string;
  detail?: string | null;
  confidence: number;
}

export interface CopilotResponse {
  answer: string;
  citations: Citation[];
  confidence: number;
  type: string;
}

export interface CopilotExplainRiskPayload {
  wallet_address: string;
  trace_id?: string;
}

export interface RiskFactorEvidence {
  transaction_hashes: string[];
  pattern_ids: string[];
  attribution_ids: string[];
  entity_ids: string[];
  wallet_addresses: string[];
  additional_data: Record<string, unknown>;
}

export interface RiskFactor {
  factor_type: string;
  weight: number;
  evidence: RiskFactorEvidence;
  description: string;
  confidence: number;
}

export interface RiskScoreResponse {
  risk_score_id: string;
  case_id: string;
  trace_id: string;
  wallet_address: string;
  score: number;
  risk_category: string;
  scoring_version: string;
  factors: RiskFactor[];
  calculated_at: string;
}

export interface RiskExplanationResponse {
  risk_score_id: string;
  wallet_address: string;
  total_score: number;
  risk_category: string;
  scoring_version: string;
  factor_explanations: string[];
  summary: string;
  calculated_at: string;
}

export interface RiskSummaryResponse {
  case_id: string;
  trace_id: string;
  wallet_count: number;
  risk_distribution: Record<string, number>;
  highest_risk_wallet?: string | null;
  highest_risk_score?: number | null;
  average_score?: number | null;
}

export type ReportType = 'summary' | 'detailed' | 'evidence_export';
export type ReportFormat = 'pdf' | 'json' | 'html';

export interface ReportGeneratePayload {
  report_type: ReportType;
  format: ReportFormat;
}

export interface ReportJobResponse {
  job_id: string;
  status: string;
  message?: string;
}

export interface GeneratedReport {
  report_id: string;
  report_type: ReportType;
  format: ReportFormat;
  generated_at: string;
  file_url: string;
}

export interface ReportListResponse {
  reports: GeneratedReport[];
}

export interface PatternItem {
  pattern_id: string;
  trace_id: string;
  wallet_address: string;
  pattern_type: string;
  demo_label?: string | null;
  confidence: number;
  description: string;
  metrics: Record<string, unknown>;
  detected_at: string;
  demo_data: boolean;
  finding_source: string;
}

export interface PatternListResponse {
  patterns: PatternItem[];
}

export interface EvidenceItem {
  evidence_id: string;
  evidence_type: string;
  reference_id: string | null;
  investigator_note: string | null;
  pinned_at: string;
  demo_data: boolean;
  finding_source: string;
}

export interface EvidenceListResponse {
  evidence: EvidenceItem[];
}

export interface AttributionItem {
  attribution_id: string;
  trace_id: string;
  wallet_address: string;
  entity_id: string;
  entity_name: string;
  entity_type?: string | null;
  provenance_level: string;
  confidence: number;
  attribution_method: string;
  source: string;
  attributed_at: string;
  demo_data: boolean;
  finding_source: string;
  disclaimer?: string | null;
}

export interface AttributionListResponse {
  attributions: AttributionItem[];
}
