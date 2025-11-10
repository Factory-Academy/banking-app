import { Transaction } from '@/types/transaction';
import { formatCurrency, formatDateTime, getRiskLevelColor, getStatusColor, formatFlagName } from '@/utils/formatters';
import { MapPin, Calendar, AlertTriangle } from 'lucide-react';

interface TransactionCardProps {
  transaction: Transaction;
  onViewDetails?: (transaction: Transaction) => void;
  showQuickActions?: boolean;
}

export function TransactionCard({ transaction, onViewDetails, showQuickActions }: TransactionCardProps) {
  const riskColors = getRiskLevelColor(transaction.risk_level);
  const statusColors = getStatusColor(transaction.status);

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 border-l-4 ${riskColors.border} hover:shadow-lg transition-shadow`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-mono text-gray-500">{transaction.id}</span>
            <span className={`px-2 py-1 text-xs font-semibold rounded ${riskColors.bg} ${riskColors.text}`}>
              {transaction.risk_level}
            </span>
            <span className={`px-2 py-1 text-xs font-semibold rounded ${statusColors.bg} ${statusColors.text}`}>
              {transaction.status}
            </span>
          </div>
          <h3 className="text-xl font-bold text-gray-900 mb-1">
            {formatCurrency(transaction.amount)}
          </h3>
          <p className="text-sm text-gray-600">
            {transaction.account_holder_name} • {transaction.account_number}
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm font-medium text-gray-700">{transaction.merchant_name}</p>
          <p className="text-xs text-gray-500">{transaction.merchant_category}</p>
        </div>
      </div>

      <div className="flex items-center gap-4 text-sm text-gray-600 mb-4">
        <div className="flex items-center gap-1">
          <Calendar className="w-4 h-4" />
          <span>{formatDateTime(transaction.timestamp)}</span>
        </div>
        <div className="flex items-center gap-1">
          <MapPin className="w-4 h-4" />
          <span>{transaction.location_city}, {transaction.location_country}</span>
        </div>
      </div>

      {transaction.fraud_flags.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-red-500" />
            <span className="text-sm font-semibold text-gray-700">Fraud Flags:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {transaction.fraud_flags.map((flag) => (
              <span
                key={flag}
                className="px-2 py-1 text-xs bg-red-50 text-red-700 rounded border border-red-200"
              >
                {formatFlagName(flag)}
              </span>
            ))}
          </div>
        </div>
      )}

      {transaction.reviewed_by && (
        <div className="mb-4 p-3 bg-blue-50 rounded border border-blue-200">
          <div className="text-sm font-semibold text-blue-900 mb-1">
            Reviewed by {transaction.reviewed_by}
          </div>
          {transaction.reviewed_at && (
            <div className="text-xs text-blue-700 mb-2">
              {formatDateTime(transaction.reviewed_at)}
            </div>
          )}
          {transaction.review_notes && (
            <div className="text-sm text-gray-700 italic">
              "{transaction.review_notes}"
            </div>
          )}
        </div>
      )}

      {showQuickActions && transaction.status === 'HELD' && (
        <div className="flex gap-2">
          <button
            onClick={() => onViewDetails?.(transaction)}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors font-medium"
          >
            Review Transaction
          </button>
        </div>
      )}

      {!showQuickActions && (
        <button
          onClick={() => onViewDetails?.(transaction)}
          className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors font-medium"
        >
          View Details →
        </button>
      )}
    </div>
  );
}
