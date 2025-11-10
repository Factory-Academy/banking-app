import { useDashboardStats } from '@/hooks/useStats';
import { AlertCircle } from 'lucide-react';
import { Link } from 'react-router-dom';

export function AlertBanner() {
  const { data: stats } = useDashboardStats();

  if (!stats || stats.held_count === 0) {
    return null;
  }

  return (
    <div className="bg-orange-50 border-l-4 border-orange-500 p-4 mb-6">
      <div className="flex items-center">
        <AlertCircle className="w-6 h-6 text-orange-500 mr-3" />
        <div className="flex-1">
          <p className="text-sm font-medium text-orange-900">
            {stats.held_count} HIGH RISK transaction{stats.held_count !== 1 ? 's' : ''} require review
          </p>
        </div>
        <Link
          to="/held"
          className="text-sm font-medium text-orange-700 hover:text-orange-900 underline"
        >
          View Queue →
        </Link>
      </div>
    </div>
  );
}
