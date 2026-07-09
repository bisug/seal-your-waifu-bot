import React from 'react';
import { cn } from '../../utils';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'outline' | 'flat';
  hover?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', hover = false, children, ...props }, ref) => {
    const variants = {
      default: 'bg-brand-deep border border-white/5',
      glass: 'bg-brand-glass backdrop-blur-md border border-brand-glass-border',
      outline: 'bg-transparent border border-white/10',
      flat: 'bg-brand-surface',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'rounded-xl transition-all overflow-hidden',
          variants[variant],
          hover && 'hover:border-white/10 hover:bg-brand-surface active:scale-[0.99]',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';
