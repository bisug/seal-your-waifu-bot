import React from 'react';
import { Shield } from 'lucide-react';

export const EmptyState = ({
  icon: Icon = Shield,
  title = "Nothing here yet",
  message = "Try adjusting your filters or come back later.",
  className = ""
}) => (
  <div className={`glass-panel p-10 rounded-3xl border border-white/5 text-center flex flex-col items-center opacity-80 ${className}`}>
    <Icon size={40} className="text-slate-800 mb-4" />
    <p className="text-slate-500 text-[11px] font-bold uppercase tracking-widest italic leading-relaxed">
      {title}<br/>{message}
    </p>
  </div>
);
