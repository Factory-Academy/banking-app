import { useState } from 'react';
import { useTransactions } from '@/hooks/useTransactions';
import { TransactionCard } from '@/components/TransactionCard';
import { ReviewModal } from '@/components/ReviewModal';
import { Transaction } from '@/types/transaction';
import { AlertCircle } from 'lucide-react';

export function HeldTransactions() {
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  
  const { data, isLoading, error } = useTransactions({
    status: 'HELD',
    limit: 100,
  });

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <p className="mt-4 text-gray-600">Loading transactions...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <p className="text-red-600">Failed to load transactions</p>
      </div>
    );
  }

  const transactions = data?.transactions || [];

  if (transactions.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-lg shadow">
        <AlertCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-gray-700 mb-2">No Transactions on Hold</h3>
        <p className="text-gray-500">All high-risk transactions have been reviewed!</p>
      </div>
    );
  }

  return (
    <>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">
          Transactions Awaiting Review ({transactions.length})
        </h2>
        <p className="text-gray-600 mt-1">
          These transactions are frozen and require your decision
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
