import { useState } from 'react';
import { Transaction } from '@/types/transaction';
import { useAccountHistory, useReviewTransaction } from '@/hooks/useTransactions';
import { formatCurrency, formatDateTime, getRiskLevelColor, formatFlagName } from '@/utils/formatters';
import { X, MapPin, Calendar, AlertTriangle, TrendingUp } from 'lucide-react';

interface ReviewModalProps {
  transaction: Transaction;
  onClose: () => void;
}

export function ReviewModal({ transaction, onClose }: ReviewModalProps) {
  const [decision, setDecision] = useState<'APPROVED' | 'REJECTED' | 'ESCALATED'>('APPROVED');
  const [notes, setNotes] = useState('');
  const [analystName, setAnalystName] = useState('Sarah Johnson');

  const { data: history, isLoading: historyLoading } = useAccountHistory(transaction.id);
  const reviewMutation = useReviewTransaction();

  const riskColors = getRiskLevelColor(transaction.risk_level);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!notes.trim()) {
      alert('Please add review notes');
      return;
    }

    try {
      await reviewMutation.mutateAsync({
        id: transaction.id,
        review: {
          decision,
          notes: notes.trim(),
          reviewed_by: analystName,
        },
      });
      onClose();
    } catch (error) {
      alert('Failed to submit review');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Review Transaction</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6">
          {/* Transaction Details */}
          <div className="bg-gray-50 rounded-lg p-6 mb-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm font-mono text-gray-500">{transaction.id}</span>
                  <span className={`px-3 py-1 text-sm font-semibold rounded ${riskColors.bg} ${riskColors.text}`}>
                    {transaction.risk_level} RISK
                  </span>
                </div>
                <h3 className="text-3xl font-bold text-gray-900 mb-2">
                  {formatCurrency(transaction.amount)}
                </h3>
                <p className="text-lg text-gray-700 mb-1">{transaction.merchant_name}</p>
                <p className="text-sm text-gray-500">{transaction.merchant_category}</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-700 mb-1">
                  {transaction.account_holder_name}
                </p>
                <p className="text-sm text-gray-500">{transaction.account_number}</p>
                <p className="text-sm text-gray-500 mt-2">{transaction.transaction_type}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Calendar className="w-4 h-4" />
                <span>{formatDateTime(transaction.timestamp)}</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <MapPin className="w-4 h-4" />
                <span>{transaction.location_city}, {transaction.location_country}</span>
              </div>
            </div>

            {transaction.fraud_flags.length > 0 && (
              <div className="border-t pt-4">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="w-5 h-5 text-red-500" />
                  <span className="font-semibold text-gray-900">Fraud Flags Triggered:</span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {transaction.fraud_flags.map((flag) => (
                    <div
                      key={flag}
                      className="px-3 py-2 bg-red-50 text-red-800 rounded border border-red-200 text-sm font-medium"
                    >
                      {formatFlagName(flag)}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Account History */}
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-5 h-5 text-blue-600" />
              <h3 className="text-lg font-bold text-gray-900">Account History</h3>
            </div>

            {historyLoading ? (
              <div className="text-center py-8 text-gray-500">Loading history...</div>
            ) : history ? (
              <>
                <div className="bg-blue-50 rounded-lg p-4 mb-4">
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">Average Transaction</p>
                      <p className="text-lg font-bold text-gray-900">
                        {formatCurrency(history.stats.average_amount)}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-600">Total Transactions</p>
                      <p className="text-lg font-bold text-gray-900">
                        {history.stats.transaction_count}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-600">Common Locations</p>
                      <p className="text-sm font-medium text-gray-900">
                        {history.stats.common_locations.slice(0, 2).join(', ')}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Contextual Transactions (around the flagged transaction time) */}
                <div className="mb-6">
                  <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    Transactions Around This Time (±7 days)
                  </h4>
                  <div className="max-h-64 overflow-y-auto border rounded">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50 sticky top-0">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Date
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Amount
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Merchant
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Location
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {history.contextual_transactions.map((txn) => (
                          <tr
                            key={txn.id}
                            className={txn.id === transaction.id ? 'bg-yellow-100 font-semibold' : ''}
                          >
                            <td className="px-4 py-2 text-sm text-gray-600">
                              {formatDateTime(txn.timestamp)}
                            </td>
                            <td className="px-4 py-2 text-sm font-medium text-gray-900">
                              {formatCurrency(txn.amount)}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-600">
                              {txn.merchant_name}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-600">
                              {txn.location_city}, {txn.location_country}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Recent Transactions */}
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4" />
                    Recent Account Activity
                  </h4>
                  <div className="max-h-48 overflow-y-auto border rounded">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50 sticky top-0">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Date
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Amount
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Merchant
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Location
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {history.recent_transactions.map((txn) => (
                          <tr
                            key={txn.id}
                            className={txn.id === transaction.id ? 'bg-yellow-100 font-semibold' : ''}
                          >
                            <td className="px-4 py-2 text-sm text-gray-600">
                              {formatDateTime(txn.timestamp)}
                            </td>
                            <td className="px-4 py-2 text-sm font-medium text-gray-900">
                              {formatCurrency(txn.amount)}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-600">
                              {txn.merchant_name}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-600">
                              {txn.location_city}, {txn.location_country}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            ) : null}
          </div>

          {/* Review Form */}
          <form onSubmit={handleSubmit} className="border-t pt-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Your Decision</h3>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Analyst Name
              </label>
              <input
                type="text"
                value={analystName}
                onChange={(e) => setAnalystName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Decision
              </label>
              <div className="grid grid-cols-3 gap-3">
                <button
                  type="button"
                  onClick={() => setDecision('APPROVED')}
                  className={`px-4 py-3 rounded-lg font-medium transition-colors ${
                    decision === 'APPROVED'
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Approve & Release
                </button>
                <button
                  type="button"
                  onClick={() => setDecision('REJECTED')}
                  className={`px-4 py-3 rounded-lg font-medium transition-colors ${
                    decision === 'REJECTED'
                      ? 'bg-red-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Reject & Block
                </button>
                <button
                  type="button"
                  onClick={() => setDecision('ESCALATED')}
                  className={`px-4 py-3 rounded-lg font-medium transition-colors ${
                    decision === 'ESCALATED'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Escalate
                </button>
              </div>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Investigation Notes (Required)
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={4}
                placeholder="Explain your decision..."
                required
              />
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                disabled={reviewMutation.isPending}
                className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {reviewMutation.isPending ? 'Submitting...' : 'Submit Review'}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
