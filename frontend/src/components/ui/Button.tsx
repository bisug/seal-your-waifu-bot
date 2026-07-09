import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'tactical';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, disabled, onAnimationStart, onDrag, onDragStart, onDragEnd, ...props }, ref) => {
    const variants = {
      primary: 'bg-white text-black hover:bg-neutral-200 active:scale-[0.98] shadow-[0_0_20px_rgba(255,255,255,0.1)]',
      secondary: 'bg-brand-surface text-white hover:bg-neutral-800 active:scale-[0.98] border border-white/10',
      outline: 'bg-transparent border border-white/20 text-white hover:bg-white/5 active:scale-[0.98]',
      ghost: 'bg-transparent text-neutral-400 hover:text-white hover:bg-white/5 active:scale-[0.98]',
      danger: 'bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500/20 active:scale-[0.98]',
      tactical: 'bg-brand-accent/10 text-brand-accent border border-brand-accent/30 hover:bg-brand-accent/20 active:scale-[0.98] shadow-[0_0_15px_rgba(59,130,246,0.1)]',
    };

    const sizes = {
      xs: 'px-2 py-1 text-[9px] font-black uppercase tracking-widest rounded-xs',
      sm: 'px-3 py-1.5 text-[11px] font-extrabold uppercase tracking-wider rounded-sm',
      md: 'px-4 py-2.5 text-xs font-black uppercase tracking-widest rounded-md',
      lg: 'px-6 py-3.5 text-sm font-black uppercase tracking-[0.15em] rounded-lg',
      xl: 'px-8 py-4.5 text-base font-black uppercase tracking-[0.2em] rounded-xl',
    };

    return (
      <motion.button
        ref={ref as any}
        whileTap={{ scale: 0.98 }}
        disabled={isLoading || disabled}
        className={cn(
          'inline-flex items-center justify-center transition-all focus:outline-none focus:ring-1 focus:ring-brand-accent/50 disabled:opacity-40 disabled:pointer-events-none whitespace-nowrap overflow-hidden relative group',
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        <span className={cn(
          "flex items-center justify-center transition-transform duration-200",
          isLoading ? "opacity-0 scale-90" : "opacity-100 scale-100"
        )}>
          {children}
        </span>

        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
          </div>
        )}

        {/* Subtle hover overlay */}
        <div className="absolute inset-0 bg-white/0 group-hover:bg-white/5 transition-colors pointer-events-none" />
      </motion.button>
    );
  }
);

Button.displayName = 'Button';
