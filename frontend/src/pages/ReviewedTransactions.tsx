import { useState } from 'react';
import { useTransactions } from '@/hooks/useTransactions';
import { Transaction } from '@/types/transaction';
import { formatCurrency, formatDateTime, getStatusColor } from '@/utils/formatters';
import { CheckCircle } from 'lucide-react';

export function ReviewedTransactions() {
  const [statusFilter, setStatusFilter] = useState<'APPROVED' | 'REJECTED' | ''>('');
  
  // Fetch approved transactions
  const { data: approvedData, isLoading: approvedLoading } = useTransactions({
    status: 'APPROVED',
    limit: 100,
  });
  
  // Fetch rejected transactions
  const { data: rejectedData, isLoading: rejectedLoading } = useTransactions({
    status: 'REJECTED',
    limit: 100,
  });

  const isLoading = approvedLoading || rejectedLoading;

  // Merge and filter based on selection
  let reviewedTransactions: Transaction[] = [];
  
  if (statusFilter === 'APPROVED') {
    reviewedTransactions = approvedData?.transactions || [];
  } else if (statusFilter === 'REJECTED') {
    reviewedTransactions = rejectedData?.transactions || [];
  } else {
    // Show all: merge both arrays and sort by reviewed_at descending
    const approved = approvedData?.transactions || [];
    const rejected = rejectedData?.transactions || [];
    reviewedTransactions = [...approved, ...rejected].sort((a, b) => {
      const dateA = a.reviewed_at ? new Date(a.reviewed_at).getTime() : 0;
      const dateB = b.reviewed_at ? new Date(b.reviewed_at).getTime() : 0;
      return dateB - dateA; // Most recent first
    });
  }

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Reviewed Transactions</h2>
        
        <div className="flex gap-4 bg-white p-4 rounded-lg shadow">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Decision
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as 'APPROVED' | 'REJECTED' | '')}
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Decisions</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>
        </div>
      </div>

      {reviewedTransactions.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <CheckCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No Reviewed Transactions</h3>
          <p className="text-gray-500">Start reviewing transactions to see them here</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Transaction
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Decision
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reviewed By
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Notes
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {reviewedTransactions.map((transaction) => {
                const statusColors = getStatusColor(transaction.status);
                return (
                  <tr key={transaction.id}>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">{transaction.id}</div>
                      <div className="text-sm text-gray-500">{transaction.account_holder_name}</div>
                      <div className="text-xs text-gray-400">{transaction.merchant_name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-bold text-gray-900">
                        {formatCurrency(transaction.amount)}
                      </div>
                      <div className="text-xs text-gray-500">
                        {formatDateTime(transaction.timestamp)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-3 py-1 text-xs font-semibold rounded ${statusColors.bg} ${statusColors.text}`}>
                        {transaction.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900">{transaction.reviewed_by}</div>
                      <div className="text-xs text-gray-500">
                        {transaction.reviewed_at && formatDateTime(transaction.reviewed_at)}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-700 max-w-xs truncate">
                        {transaction.review_notes}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
