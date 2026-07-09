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
  title = "DATA ARCHIVE EMPTY",
  message = "No records found in the current sector.",
  className = ""
}: EmptyStateProps) => (
  <Card variant="tactical" className={`py-12 px-6 bg-[#08080a]/50 text-center flex flex-col items-center select-none border-dashed border-white/5 ${className}`}>
    <div className="w-12 h-12 rounded-lg bg-white/[0.02] border border-white/[0.05] flex items-center justify-center mb-5">
       <Icon size={20} className="text-neutral-800" />
    </div>
    <h3 className="text-[10px] font-black text-neutral-400 uppercase tracking-[0.3em] mb-2">{title}</h3>
    <p className="text-[9px] text-neutral-600 font-bold uppercase tracking-widest max-w-[200px] leading-relaxed">
      {message}
    </p>
  </Card>
);
