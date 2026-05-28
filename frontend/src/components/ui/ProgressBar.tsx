import React from 'react';
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
    <div className={`w-full ${compact ? 'space-y-1' : 'space-y-1.5'}`}>
      {label && (
        <div className="flex justify-between items-end text-[10px] font-semibold text-zinc-500 px-0.5 uppercase tracking-tight">
          <span>{label}</span>
          <span className="text-zinc-300 tabular-nums">{formatNumber(current)} / {formatNumber(total)}</span>
        </div>
      )}
      <div className={`${compact ? 'h-1.5' : 'h-2'} w-full bg-zinc-950 rounded-full overflow-hidden border border-white/5`}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
          className={`h-full ${color} rounded-full relative`}
        />
      </div>
    </div>
  );
};
