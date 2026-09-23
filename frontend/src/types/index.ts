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
