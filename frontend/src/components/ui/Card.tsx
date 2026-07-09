import React from 'react';
import { cn } from '../../utils';
import { motion, HTMLMotionProps } from 'framer-motion';

type CardVariant = 'default' | 'glass' | 'outline' | 'flat' | 'tactical' | 'accent';

interface CardProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'onAnimationStart' | 'onDrag' | 'onDragStart' | 'onDragEnd'> {
  variant?: CardVariant;
  hover?: boolean;
  withCorners?: boolean;
  isBento?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', hover = false, withCorners = false, isBento = false, children, ...props }, ref) => {
    const variants: Record<CardVariant, string> = {
      default: 'bg-brand-deep border border-white/5 shadow-sm',
      glass: 'glass-panel',
      outline: 'bg-transparent border border-white/10',
      flat: 'bg-brand-surface',
      tactical: 'bg-[#0c0c0e] border border-white/[0.04] shadow-[inset_0_1px_0_rgba(255,255,255,0.02)]',
      accent: 'bg-brand-accent/5 border border-brand-accent/20 shadow-[0_0_30px_rgba(59,130,246,0.05)]',
    };

    return (
      <motion.div
        ref={ref as any}
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn(
          'rounded-xl transition-all relative overflow-hidden',
          variants[variant],
          hover && 'hover:border-white/20 hover:bg-brand-surface/80 hover:shadow-md active:scale-[0.995]',
          withCorners && 'corner-border corner-border-tl corner-border-br',
          isBento && 'p-5 flex flex-col justify-between h-full group',
          className
        )}
        {...(props as HTMLMotionProps<"div">)}
      >
        {isBento && (
          <>
            <div className="absolute inset-0 pointer-events-none bg-scanline opacity-[0.02]" />
            <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent pointer-events-none" />
          </>
        )}
        {children}
      </motion.div>
    );
  }
);

Card.displayName = 'Card';
