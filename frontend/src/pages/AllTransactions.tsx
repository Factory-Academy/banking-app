import { useState } from 'react';
import { useTransactions } from '@/hooks/useTransactions';
import { TransactionCard } from '@/components/TransactionCard';
import { ReviewModal } from '@/components/ReviewModal';
import { Transaction, TransactionStatus, RiskLevel } from '@/types/transaction';

export function AllTransactions() {
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [statusFilter, setStatusFilter] = useState<TransactionStatus | ''>('');
  const [riskFilter, setRiskFilter] = useState<RiskLevel | ''>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(0);
  const limit = 50;
  
  const { data, isLoading } = useTransactions({
    status: statusFilter || undefined,
    risk_level: riskFilter || undefined,
    account_number: searchQuery || undefined,
    limit: limit,
    offset: page * limit,
  });

  const transactions = data?.transactions || [];
  const totalPages = Math.ceil((data?.total || 0) / limit);

  return (
    <>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">All Transactions</h2>
        
        {/* Filters */}
        <div className="flex gap-4 bg-white p-4 rounded-lg shadow flex-wrap">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Account Number
            </label>
            <input
              type="text"
              placeholder="Search by account..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(0); // Reset to first page on search
              }}
              className="px-3 py-2 border border-gray-300 rounded-md w-64 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as TransactionStatus | '');
                setPage(0);
              }}
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Statuses</option>
              <option value="HELD">Held</option>
              <option value="CLEARED">Cleared</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
              <option value="ESCALATED">Escalated</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Risk Level
            </label>
            <select
              value={riskFilter}
              onChange={(e) => {
                setRiskFilter(e.target.value as RiskLevel | '');
                setPage(0);
              }}
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Risk Levels</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>
          
          <div className="flex items-end">
            <button
              onClick={() => {
                setStatusFilter('');
                setRiskFilter('');
                setSearchQuery('');
                setPage(0);
              }}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <>
          <div className="mb-4 text-sm text-gray-600">
            Showing {page * limit + 1}-{Math.min((page + 1) * limit, data?.total || 0)} of {data?.total || 0} transactions
          </div>
          
          <div className="grid gap-4">
            {transactions.map((transaction) => (
              <TransactionCard
                key={transaction.id}
                transaction={transaction}
                onViewDetails={setSelectedTransaction}
              />
            ))}
          </div>
          
          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex justify-between items-center mt-6 bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-600">
                Page {page + 1} of {totalPages}
              </div>
              
              <div className="flex gap-2">
                <button
                  disabled={page === 0}
                  onClick={() => setPage(page - 1)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>
                
                <button
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage(page + 1)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {selectedTransaction && (
        <ReviewModal
          transaction={selectedTransaction}
          onClose={() => setSelectedTransaction(null)}
        />
      )}
    </>
  );
}
