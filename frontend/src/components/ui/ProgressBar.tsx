import 'react';
import { motion } from 'framer-motion';
import { formatNumber } from '../../utils';

interface ProgressBarProps {
  current: number;
  total: number;
  color?: string;
  label?: string;
  compact?: boolean;
}

export const ProgressBar = ({ current, total, color = "bg-brand-accent", label, compact }: ProgressBarProps) => {
  const percentage = total > 0 ? Math.min(100, Math.max(0, (current / total) * 100)) : 0;

  return (
    <div className={`w-full ${compact ? 'space-y-1.5' : 'space-y-2'}`}>
      {label && (
        <div className="flex justify-between items-end text-xs font-semibold text-zinc-600 px-0.5">
          <span>{label}</span>
          <span className="text-zinc-400 tabular-nums">{formatNumber(current)} / {formatNumber(total)}</span>
        </div>
      )}
      <div className={`${compact ? 'h-1.5' : 'h-2.5'} w-full bg-zinc-900 rounded-full overflow-hidden border border-white/5`}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
          className={`h-full ${color} rounded-full relative`}
        />
      </div>
    </div>
  );
};
