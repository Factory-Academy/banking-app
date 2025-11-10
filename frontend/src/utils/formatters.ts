export function formatCurrency(amount: string | number): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(num);
}

export function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date);
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(date);
}

export function formatFlagName(flag: string): string {
  return flag
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export function getRiskLevelColor(riskLevel: string): {
  bg: string;
  text: string;
  border: string;
} {
  switch (riskLevel) {
    case 'HIGH':
      return {
        bg: 'bg-red-100',
        text: 'text-red-800',
        border: 'border-red-500',
      };
    case 'MEDIUM':
      return {
        bg: 'bg-yellow-100',
        text: 'text-yellow-800',
        border: 'border-yellow-500',
      };
    case 'LOW':
      return {
        bg: 'bg-green-100',
        text: 'text-green-800',
        border: 'border-green-500',
      };
    default:
      return {
        bg: 'bg-gray-100',
        text: 'text-gray-800',
        border: 'border-gray-500',
      };
  }
}

export function getStatusColor(status: string): {
  bg: string;
  text: string;
} {
  switch (status) {
    case 'HELD':
      return { bg: 'bg-orange-100', text: 'text-orange-800' };
    case 'APPROVED':
      return { bg: 'bg-green-100', text: 'text-green-800' };
    case 'REJECTED':
      return { bg: 'bg-red-100', text: 'text-red-800' };
    case 'ESCALATED':
      return { bg: 'bg-purple-100', text: 'text-purple-800' };
    case 'CLEARED':
      return { bg: 'bg-blue-100', text: 'text-blue-800' };
    default:
      return { bg: 'bg-gray-100', text: 'text-gray-800' };
  }
}
