import 'react';
import { cn } from '../../utils';

export const Skeleton = ({ className }: { className?: string }) => (
  <div className={cn(
    "bg-white/[0.03] overflow-hidden relative rounded-xl shimmer",
    className
  )} />
);

export const CardSkeleton = () => (
  <div className="rounded-xl bg-brand-deep border border-white/[0.04] overflow-hidden aspect-[3/4.2] relative">
    <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-60" />
    <div className="absolute bottom-0 inset-x-0 p-4 space-y-3">
        <div className="space-y-2">
            <Skeleton className="h-3 w-4/5 rounded-sm" />
            <Skeleton className="h-2 w-1/2 rounded-sm opacity-50" />
        </div>
      <div className="flex justify-between items-center gap-2 pt-1">
        <Skeleton className="h-4 w-12 rounded-md" />
        <Skeleton className="h-4 w-10 rounded-md" />
      </div>
    </div>
  </div>
);
