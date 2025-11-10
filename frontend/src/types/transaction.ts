export type TransactionStatus = "CLEARED" | "HELD" | "APPROVED" | "REJECTED" | "ESCALATED";
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";

export interface Transaction {
  id: string;
  account_number: string;
  account_holder_name: string;
  amount: string;
  merchant_name: string;
  merchant_category: string | null;
  transaction_type: string;
  location_city: string;
  location_country: string;
  latitude: number | null;
  longitude: number | null;
  timestamp: string;
  status: TransactionStatus;
  risk_level: RiskLevel;
  risk_score: number;
  fraud_flags: string[];
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface TransactionListResponse {
  transactions: Transaction[];
  total: number;
  limit: number;
  offset: number;
}

export interface TransactionFilters {
  status?: TransactionStatus;
  risk_level?: RiskLevel;
  account_number?: string;
  merchant_name?: string;
  date_from?: string;
  date_to?: string;
  min_amount?: number;
  max_amount?: number;
  limit?: number;
  offset?: number;
}

export interface ReviewRequest {
  decision: "APPROVED" | "REJECTED" | "ESCALATED";
  notes: string;
  reviewed_by: string;
}

export interface AccountStats {
  average_amount: string;
  transaction_count: number;
  common_locations: string[];
  first_transaction_date: string | null;
}

export interface AccountHistoryResponse {
  account_number: string;
  account_holder_name: string;
  contextual_transactions: Transaction[];
  recent_transactions: Transaction[];
  reviewed_transaction_time: string;
  stats: AccountStats;
}

export interface DashboardStats {
  held_count: number;
  approved_today: number;
  rejected_today: number;
  escalated_count: number;
  avg_review_time_minutes: number;
  transactions_by_risk: Record<string, number>;
}
