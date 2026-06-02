import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const ErrorState = ({
  title = 'Could not load this page',
  message = 'Check your connection and try again.',
  actionLabel = 'Try again',
  onAction,
}: ErrorStateProps) => (
  <div className="py-14 px-6 rounded-xl border border-red-500/10 bg-red-500/5 text-center flex flex-col items-center">
    <div className="w-12 h-12 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-5">
      <AlertCircle size={22} className="text-red-500" />
    </div>
    <h3 className="text-sm font-bold text-white mb-2">{title}</h3>
    <p className="text-sm text-neutral-500 font-medium max-w-[260px] leading-relaxed">{message}</p>
    {onAction && (
      <button
        onClick={onAction}
        className="mt-6 px-4 py-2.5 rounded-lg bg-white text-brand-midnight text-sm font-bold active:scale-95 transition-transform inline-flex items-center gap-2"
      >
        <RefreshCw size={15} />
        <span>{actionLabel}</span>
      </button>
    )}
  </div>
);
