import React from 'react';
import { cn } from '../../utils';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'outline' | 'success' | 'warning' | 'danger' | 'purple';
  size?: 'xs' | 'sm';
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
  const variants = {
    primary: 'bg-brand-accent/10 text-brand-accent border-brand-accent/20',
    secondary: 'bg-white/5 text-neutral-300 border-white/10',
    outline: 'bg-transparent text-neutral-400 border-white/10',
    success: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
    warning: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
    danger: 'bg-red-500/10 text-red-500 border-red-500/20',
    purple: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
  };

  const sizes = {
    xs: 'px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-tight',
    sm: 'px-2 py-0.5 text-[10px] font-semibold',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-md border whitespace-nowrap',
        variants[variant],
        sizes[size],
        className
      )}
    >
      {Icon && <Icon size={size === 'xs' ? 10 : 12} className="shrink-0" />}
      {children}
    </span>
  );
};
