import { useDashboardStats } from '@/hooks/useStats';
import { AlertCircle, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

export function StatsCards() {
  const { data: stats, isLoading } = useDashboardStats();

  if (isLoading || !stats) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white p-6 rounded-lg shadow animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-16"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div className="bg-white p-6 rounded-lg shadow border-l-4 border-orange-500">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600 font-medium">Pending Review</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">{stats.held_count}</p>
          </div>
          <AlertCircle className="w-10 h-10 text-orange-500" />
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow border-l-4 border-green-500">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600 font-medium">Approved Today</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">{stats.approved_today}</p>
          </div>
          <CheckCircle className="w-10 h-10 text-green-500" />
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow border-l-4 border-red-500">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600 font-medium">Blocked Today</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">{stats.rejected_today}</p>
          </div>
          <XCircle className="w-10 h-10 text-red-500" />
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow border-l-4 border-purple-500">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600 font-medium">Escalated</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">{stats.escalated_count}</p>
          </div>
          <AlertTriangle className="w-10 h-10 text-purple-500" />
        </div>
      </div>
    </div>
  );
}
