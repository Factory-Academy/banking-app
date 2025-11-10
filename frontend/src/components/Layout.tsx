import { Link, useLocation } from 'react-router-dom';
import { Shield } from 'lucide-react';
import { AlertBanner } from './AlertBanner';
import { StatsCards } from './StatsCards';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation();

  const tabs = [
    { path: '/held', label: 'Held Transactions', badge: true },
    { path: '/all', label: 'All Transactions' },
    { path: '/escalated', label: 'Escalated' },
    { path: '/reviewed', label: 'Reviewed' },
  ];

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900">
              Transaction Monitoring System
            </h1>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-1">
            {tabs.map((tab) => (
              <Link
                key={tab.path}
                to={tab.path}
                className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors ${
                  location.pathname === tab.path
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab.label}
              </Link>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <AlertBanner />
        <StatsCards />
        {children}
      </main>
    </div>
  );
}
