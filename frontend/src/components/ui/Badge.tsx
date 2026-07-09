import React from 'react';
import { cn } from '../../utils';

type BadgeVariant = 'primary' | 'secondary' | 'outline' | 'success' | 'warning' | 'danger' | 'premium' | 'rare' | 'epic' | 'tactical';
type BadgeSize = 'xs' | 'sm' | 'md';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: BadgeSize;
  className?: string;
  icon?: React.ElementType;
}

export const Badge = ({
  children,
  variant = 'primary',
  size = 'sm',
  className,
  icon: Icon,
}: BadgeProps) => {
  const variants: Record<BadgeVariant, string> = {
    primary: 'bg-brand-accent/10 text-brand-accent border-brand-accent/20',
    secondary: 'bg-white/5 text-neutral-400 border-white/10',
    outline: 'bg-transparent text-neutral-500 border-white/10',
    success: 'bg-success/10 text-success border-success/20',
    warning: 'bg-warning/10 text-warning border-warning/20',
    danger: 'bg-danger/10 text-danger border-danger/20',
    premium: 'bg-premium/10 text-premium border-premium/20',
    rare: 'bg-rare/10 text-rare border-rare/20',
    epic: 'bg-epic/10 text-epic border-epic/20',
    tactical: 'bg-black text-white border-white/20 font-mono font-bold',
  };

  const sizes: Record<BadgeSize, string> = {
    xs: 'px-1.5 py-0.5 text-[8px] font-black uppercase tracking-[0.15em] leading-none rounded-[2px]',
    sm: 'px-2 py-1 text-[9px] font-black uppercase tracking-[0.12em] leading-none rounded-sm',
    md: 'px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.15em] leading-none rounded-md',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 border whitespace-nowrap select-none transition-all duration-200',
        variants[variant],
        sizes[size],
        className
      )}
    >
      {Icon && <Icon size={size === 'xs' ? 9 : size === 'sm' ? 10 : 12} strokeWidth={2.5} className="shrink-0" />}
      <span className="translate-y-[0.5px]">{children}</span>
    </span>
  );
};
