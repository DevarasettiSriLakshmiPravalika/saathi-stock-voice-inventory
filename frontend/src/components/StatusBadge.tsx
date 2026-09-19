import React from 'react';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const normalized = status.toUpperCase();

  let colorClasses = 'bg-slate-100 text-slate-700 border-slate-200';

  switch (normalized) {
    case 'CONFIRMED':
    case 'APPROVED':
    case 'ENROLLED':
    case 'ACTIVE':
    case 'HEALTHY':
    case 'IN':
      colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200';
      break;
    case 'FLAGGED':
    case 'PENDING':
    case 'REQUIRES_REVIEW':
    case 'LOW_QUALITY':
    case 'LOW_CONFIDENCE':
      colorClasses = 'bg-amber-50 text-amber-700 border-amber-200';
      break;
    case 'REJECTED':
    case 'FAILED':
    case 'INACTIVE':
    case 'OUT':
      colorClasses = 'bg-rose-50 text-rose-700 border-rose-200';
      break;
    case 'PROCESSING':
      colorClasses = 'bg-sky-50 text-sky-700 border-sky-200';
      break;
    case 'OWNER':
      colorClasses = 'bg-indigo-50 text-indigo-700 border-indigo-200';
      break;
    case 'STAFF':
      colorClasses = 'bg-blue-50 text-blue-700 border-blue-200';
      break;
    case 'OUTSIDER':
      colorClasses = 'bg-purple-50 text-purple-700 border-purple-200';
      break;
  }

  const sizeClasses = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-xs font-semibold px-2.5 py-1';

  return (
    <span className={`inline-flex items-center rounded-full border ${colorClasses} ${sizeClasses}`}>
      {normalized}
    </span>
  );
};
