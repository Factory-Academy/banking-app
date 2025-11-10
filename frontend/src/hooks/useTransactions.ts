import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/api/client';
import type { TransactionFilters, ReviewRequest } from '@/types/transaction';

export function useTransactions(filters: TransactionFilters = {}) {
  return useQuery({
    queryKey: ['transactions', filters],
    queryFn: () => api.getTransactions(filters),
    refetchInterval: 30000, // Auto-refresh every 30s
  });
}

export function useTransaction(id: string) {
  return useQuery({
    queryKey: ['transaction', id],
    queryFn: () => api.getTransaction(id),
    enabled: !!id,
  });
}

export function useAccountHistory(transactionId: string) {
  return useQuery({
    queryKey: ['accountHistory', transactionId],
    queryFn: () => api.getAccountHistory(transactionId),
    enabled: !!transactionId,
  });
}

export function useReviewTransaction() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, review }: { id: string; review: ReviewRequest }) =>
      api.reviewTransaction(id, review),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
  });
}
