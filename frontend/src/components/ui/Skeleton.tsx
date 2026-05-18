import React from 'react';

/**
 * Cinematic Skeleton Loaders
 */
export const Skeleton = ({ className }) => (
  <div className={`bg-white/[0.03] overflow-hidden relative ${className}`}>
    <div className="absolute inset-0 animate-shimmer opacity-40" />
  </div>
);

export const CardSkeleton = () => (
  <div className="rounded-[1.5rem] glass-panel border border-white/5 overflow-hidden aspect-[3/4]">
    <div className="h-full p-4 flex flex-col justify-end space-y-3">
      <Skeleton className="h-2.5 w-1/3 rounded-full" />
      <Skeleton className="h-3.5 w-2/3 rounded-full" />
    </div>
  </div>
);
