import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';

export function useDashboardStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: () => api.getDashboardStats(),
    refetchInterval: 30000, // Auto-refresh every 30s
  });
}
