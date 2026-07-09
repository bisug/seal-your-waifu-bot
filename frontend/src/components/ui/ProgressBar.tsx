import 'react';
import { motion } from 'framer-motion';
import { formatNumber, cn } from '../../utils';

interface ProgressBarProps {
  current: number;
  total: number;
  color?: string;
  label?: string;
  compact?: boolean;
  showValue?: boolean;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'premium' | 'epic';
}

export const ProgressBar = ({
  current,
  total,
  color,
  label,
  compact,
  showValue = true,
  variant = 'default'
}: ProgressBarProps) => {
  const percentage = total > 0 ? Math.min(100, Math.max(0, (current / total) * 100)) : 0;

  const variants = {
    default: 'bg-brand-accent shadow-[0_0_12px_rgba(59,130,246,0.3)]',
    success: 'bg-success shadow-[0_0_12px_rgba(16,185,129,0.3)]',
    warning: 'bg-warning shadow-[0_0_12px_rgba(245,158,11,0.3)]',
    danger: 'bg-danger shadow-[0_0_12px_rgba(239,68,68,0.3)]',
    premium: 'bg-premium shadow-[0_0_12px_rgba(250,204,21,0.3)]',
    epic: 'bg-epic shadow-[0_0_12px_rgba(168,85,247,0.3)]',
  };

  return (
    <div className={`w-full ${compact ? 'space-y-1.5' : 'space-y-2.5'}`}>
      {(label || showValue) && (
        <div className="flex justify-between items-end px-0.5">
          {label && <span className="text-[9px] font-black uppercase tracking-[0.2em] text-neutral-600 leading-none">{label}</span>}
          {showValue && (
            <span className="text-[10px] font-mono font-bold text-neutral-500 tabular-nums leading-none">
              {formatNumber(current)}<span className="mx-0.5 opacity-30">/</span>{formatNumber(total)}
            </span>
          )}
        </div>
      )}
      <div className={cn(
        'w-full bg-black/60 rounded-full overflow-hidden border border-white/[0.03] relative p-[1px]',
        compact ? 'h-2' : 'h-3'
      )}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
          className={cn(
            'h-full rounded-full relative',
            color || variants[variant]
          )}
        >
          {/* Animated gradient sheen */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent w-full animate-[shimmer_2s_infinite]" />
          <div className="absolute inset-0 bg-gradient-to-b from-white/10 to-transparent pointer-events-none" />
        </motion.div>
      </div>
    </div>
  );
};
