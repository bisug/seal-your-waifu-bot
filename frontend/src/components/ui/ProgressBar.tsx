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
}

export const ProgressBar = ({
  current,
  total,
  color = "bg-brand-accent",
  label,
  compact,
  showValue = true
}: ProgressBarProps) => {
  const percentage = total > 0 ? Math.min(100, Math.max(0, (current / total) * 100)) : 0;

  return (
    <div className={`w-full ${compact ? 'space-y-1' : 'space-y-2'}`}>
      {(label || showValue) && (
        <div className="flex justify-between items-end px-0.5">
          {label && <span className="text-[9px] font-black uppercase tracking-widest text-neutral-500">{label}</span>}
          {showValue && (
            <span className="text-[10px] font-mono font-bold text-neutral-400 tabular-nums">
              {formatNumber(current)}<span className="mx-0.5 opacity-30">/</span>{formatNumber(total)}
            </span>
          )}
        </div>
      )}
      <div className={cn(
        'w-full bg-black/40 rounded-full overflow-hidden border border-white/5 relative',
        compact ? 'h-1.5' : 'h-2.5'
      )}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className={`h-full ${color} rounded-full relative shadow-[0_0_10px_rgba(0,0,0,0.5)]`}
        >
          {/* Subtle sheen */}
          <div className="absolute inset-0 bg-gradient-to-b from-white/20 to-transparent pointer-events-none" />
        </motion.div>
      </div>
    </div>
  );
};
