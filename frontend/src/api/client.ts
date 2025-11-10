import type {
  Transaction,
  TransactionListResponse,
  TransactionFilters,
  ReviewRequest,
  AccountHistoryResponse,
  DashboardStats
} from '@/types/transaction';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const api = {
  async createTransaction(data: Omit<Transaction, 'id' | 'status' | 'risk_level' | 'risk_score' | 'fraud_flags' | 'reviewed_by' | 'reviewed_at' | 'review_notes' | 'created_at' | 'updated_at'>): Promise<Transaction> {
    const response = await fetch(`${API_BASE_URL}/transactions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create transaction');
    return response.json();
  },

  async getTransactions(filters: TransactionFilters = {}): Promise<TransactionListResponse> {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, String(value));
      }
    });
    
    const response = await fetch(`${API_BASE_URL}/transactions?${params}`);
    if (!response.ok) throw new Error('Failed to fetch transactions');
    return response.json();
  },

  async getTransaction(id: string): Promise<Transaction> {
    const response = await fetch(`${API_BASE_URL}/transactions/${id}`);
    if (!response.ok) throw new Error('Failed to fetch transaction');
    return response.json();
  },

  async getAccountHistory(transactionId: string): Promise<AccountHistoryResponse> {
    const response = await fetch(`${API_BASE_URL}/transactions/${transactionId}/history`);
    if (!response.ok) throw new Error('Failed to fetch account history');
    return response.json();
  },

  async reviewTransaction(id: string, review: ReviewRequest): Promise<Transaction> {
    const response = await fetch(`${API_BASE_URL}/transactions/${id}/review`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(review),
    });
    if (!response.ok) throw new Error('Failed to review transaction');
    return response.json();
  },

  async getDashboardStats(): Promise<DashboardStats> {
    const response = await fetch(`${API_BASE_URL}/stats/dashboard`);
    if (!response.ok) throw new Error('Failed to fetch dashboard stats');
    return response.json();
  },
};
