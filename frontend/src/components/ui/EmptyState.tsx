import 'react';
import { PackageOpen, type LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon?: LucideIcon;
  title?: string;
  message?: string;
  className?: string;
}

export const EmptyState = ({
  icon: Icon = PackageOpen,
  title = "No data available",
  message = "Try adjusting your filters or come back later.",
  className = ""
}: EmptyStateProps) => (
  <div className={`py-16 px-6 rounded-xl border border-white/5 bg-zinc-900/20 text-center flex flex-col items-center select-none ${className}`}>
    <div className="w-12 h-12 rounded-xl bg-zinc-900 border border-white/5 flex items-center justify-center mb-6">
       <Icon size={20} className="text-zinc-700" />
    </div>
    <h3 className="text-sm font-bold text-zinc-400 mb-2">{title}</h3>
    <p className="text-sm text-zinc-600 font-medium max-w-[240px] leading-relaxed">
      {message}
    </p>
  </div>
);
