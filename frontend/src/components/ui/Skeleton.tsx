import 'react';
import { cn } from '../../utils';

const isLite = () => localStorage.getItem('sealbot-lite-mode') === 'true';

export const Skeleton = ({ className }: { className?: string }) => (
  <div className={cn(
    "bg-white/5 overflow-hidden relative rounded-md",
    className
  )}>
    {!isLite() && (
      <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-white/5 to-transparent" />
    )}
  </div>
);

export const CardSkeleton = () => (
  <div className="rounded-xl bg-brand-deep border border-white/5 overflow-hidden aspect-[3/4] relative">
    <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-black/40 to-transparent" />
    <div className="absolute bottom-0 inset-x-0 p-2 space-y-1.5">
      <Skeleton className="h-3 w-2/3" />
      <div className="flex gap-1">
        <Skeleton className="h-4 flex-1 rounded" />
        <Skeleton className="h-4 w-8 rounded" />
      </div>
    </div>
  </div>
);
