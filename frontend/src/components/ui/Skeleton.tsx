import 'react';
import { cn } from '../../utils';

const isLite = () => localStorage.getItem('sealbot-lite-mode') === 'true';

export const Skeleton = ({ className }: { className?: string }) => (
  <div className={cn(
    "bg-white/5 overflow-hidden relative rounded-xl",
    className
  )}>
    {!isLite() && (
      <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/5 to-transparent" />
    )}
  </div>
);

export const CardSkeleton = () => (
  <div className="rounded-2xl bg-brand-deep border border-white/5 overflow-hidden aspect-[3/4.2] relative">
    <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent" />
    <div className="absolute bottom-0 inset-x-0 p-3 space-y-3">
        <div className="space-y-1.5">
            <Skeleton className="h-3 w-4/5" />
            <Skeleton className="h-2 w-1/2 opacity-50" />
        </div>
      <div className="flex justify-between items-center gap-2">
        <Skeleton className="h-4 w-12 rounded-lg" />
        <Skeleton className="h-4 w-10 rounded-lg" />
      </div>
    </div>
  </div>
);
