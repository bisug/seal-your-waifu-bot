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
  title = 'System Error: Data Access Failed',
  message = 'Failed to establish connection with the central archive.',
  actionLabel = 'Reconnect',
  onAction,
}: ErrorStateProps) => (
  <Card className="py-14 px-6 border-red-500/20 bg-red-500/5 text-center flex flex-col items-center">
    <div className="w-14 h-14 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-6">
      <AlertCircle size={28} className="text-red-500" />
    </div>
    <h3 className="text-sm font-black text-white uppercase tracking-widest mb-2">{title}</h3>
    <p className="text-[11px] text-neutral-500 font-bold uppercase tracking-wider max-w-[280px] leading-relaxed">{message}</p>
    {onAction && (
      <Button
        variant="outline"
        onClick={onAction}
        className="mt-8 border-red-500/30 text-red-400 hover:bg-red-500/10 rounded-xl px-6 py-2.5 uppercase text-[10px] font-black tracking-[0.2em]"
      >
        <RefreshCw size={14} className="mr-2" />
        {actionLabel}
      </Button>
    )}
  </Card>
);
