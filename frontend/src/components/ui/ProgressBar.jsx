import React from 'react';
import { motion } from 'framer-motion';
import { formatNumber } from '../../utils';

export const ProgressBar = ({ current, total, color = "bg-brand-accent", label }) => {
  const percentage = total > 0 ? Math.min(100, Math.max(0, (current / total) * 100)) : 0;

  return (
    <div className="w-full space-y-1.5">
      {label && (
        <div className="flex justify-between items-end text-[10px] font-black text-slate-400 px-0.5 uppercase tracking-widest">
          <span className="opacity-70">{label}</span>
          <span className="text-white/80 tabular-nums">{formatNumber(current)} / {formatNumber(total)}</span>
        </div>
      )}
      <div className="h-2 w-full bg-slate-900/50 rounded-full overflow-hidden border border-white/10 p-[1px]">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1.5, ease: [0.34, 1.56, 0.64, 1] }}
          className={`h-full ${color} rounded-full neon-shadow shadow-current relative`}
        >
            <div className="absolute inset-0 bg-white/20 rounded-full" />
        </motion.div>
      </div>
    </div>
  );
};
