import React from 'react';
import { Shield } from 'lucide-react';

export const EmptyState = ({
  icon: Icon = Shield,
  title = "Nothing here yet",
  message = "Try adjusting your filters or come back later.",
  className = ""
}) => (
  <div className={`p-10 rounded-lg border border-dashed border-zinc-800 bg-zinc-900/20 text-center flex flex-col items-center ${className}`}>
    <Icon size={32} className="text-zinc-800 mb-4" />
    <h3 className="text-sm font-bold text-zinc-500 mb-1">{title}</h3>
    <p className="text-xs text-zinc-600 font-medium max-w-[200px]">
      {message}
    </p>
  </div>
);
