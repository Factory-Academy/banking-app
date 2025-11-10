import { useState } from 'react';
import { useTransactions } from '@/hooks/useTransactions';
import { TransactionCard } from '@/components/TransactionCard';
import { ReviewModal } from '@/components/ReviewModal';
import { Transaction } from '@/types/transaction';
import { AlertTriangle } from 'lucide-react';

export function EscalatedTransactions() {
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  
  const { data, isLoading } = useTransactions({
    status: 'ESCALATED',
    limit: 100,
  });

  const transactions = data?.transactions || [];

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (transactions.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-lg shadow">
        <AlertTriangle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-gray-700 mb-2">No Escalated Transactions</h3>
        <p className="text-gray-500">No transactions require senior review at this time</p>
      </div>
    );
  }

  return (
    <>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">
          Escalated Transactions ({transactions.length})
        </h2>
        <p className="text-gray-600 mt-1">
          Transactions requiring senior analyst review
        </p>
      </div>

      <div className="grid gap-4">
        {transactions.map((transaction) => (
          <TransactionCard
            key={transaction.id}
            transaction={transaction}
            onViewDetails={setSelectedTransaction}
            showQuickActions
          />
        ))}
      </div>

      {selectedTransaction && (
        <ReviewModal
          transaction={selectedTransaction}
          onClose={() => setSelectedTransaction(null)}
        />
      )}
    </>
  );
}
