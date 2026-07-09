import 'react';
import { PackageOpen, type LucideIcon } from 'lucide-react';
import { Card } from './Card';

interface EmptyStateProps {
  icon?: LucideIcon;
  title?: string;
  message?: string;
  className?: string;
}

export const EmptyState = ({
  icon: Icon = PackageOpen,
  title = "No data detected",
  message = "Try adjusting your parameters or check back later.",
  className = ""
}: EmptyStateProps) => (
  <Card className={`py-16 px-6 border-dashed bg-brand-deep/30 text-center flex flex-col items-center select-none ${className}`}>
    <div className="w-14 h-14 rounded-2xl bg-brand-surface border border-white/5 flex items-center justify-center mb-6">
       <Icon size={24} className="text-neutral-700" />
    </div>
    <h3 className="text-sm font-black text-white uppercase tracking-widest mb-2">{title}</h3>
    <p className="text-[11px] text-neutral-500 font-bold uppercase tracking-wider max-w-[240px] leading-relaxed">
      {message}
    </p>
  </Card>
);
