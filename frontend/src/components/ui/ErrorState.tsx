import 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './Button';
import { Card } from './Card';

interface ErrorStateProps {
  title?: string;
  message?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const ErrorState = ({
  title = 'SYSTEM ERROR: LINK FAILURE',
  message = 'Failed to establish connection with the central registry.',
  actionLabel = 'RETRY LINK',
  onAction,
}: ErrorStateProps) => (
  <Card variant="tactical" className="py-10 px-6 border-red-500/10 bg-red-500/[0.02] text-center flex flex-col items-center">
    <div className="w-12 h-12 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-5">
      <AlertCircle size={20} className="text-red-500" />
    </div>
    <h3 className="text-[10px] font-black text-white uppercase tracking-[0.2em] mb-2">{title}</h3>
    <p className="text-[9px] text-neutral-600 font-bold uppercase tracking-widest max-w-[240px] leading-relaxed">{message}</p>
    {onAction && (
      <Button
        variant="outline"
        size="sm"
        onClick={onAction}
        className="mt-6 border-red-500/20 text-red-500 hover:bg-red-500/10 px-6 py-2"
      >
        <RefreshCw size={12} className="mr-2" />
        {actionLabel}
      </Button>
    )}
  </Card>
);
