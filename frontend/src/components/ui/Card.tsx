import React from 'react';
import { cn } from '../../utils';
import { motion } from 'framer-motion';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'outline' | 'flat' | 'tactical';
  hover?: boolean;
  withCorners?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', hover = false, withCorners = false, children, onAnimationStart, onDrag, onDragStart, onDragEnd, ...props }, ref) => {
    const variants = {
      default: 'bg-brand-deep border border-white/5',
      glass: 'bg-brand-glass backdrop-blur-xl border border-brand-glass-border',
      outline: 'bg-transparent border border-white/10',
      flat: 'bg-brand-surface',
      tactical: 'bg-[#0c0c0e] border border-white/[0.03] shadow-[inset_0_1px_1px_rgba(255,255,255,0.02)]',
    };

    return (
      <motion.div
        ref={ref as any}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn(
          'rounded-lg transition-all relative overflow-hidden',
          variants[variant],
          hover && 'hover:border-white/10 hover:bg-brand-surface/80 active:scale-[0.995]',
          withCorners && 'corner-border corner-border-tl corner-border-br',
          className
        )}
        {...props}
      >
        {children}
      </motion.div>
    );
  }
);

Card.displayName = 'Card';
