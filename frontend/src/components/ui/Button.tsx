import React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { cn } from '../../utils';

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'tactical' | 'glass';
type ButtonSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

interface ButtonProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'onAnimationStart' | 'onDrag' | 'onDragStart' | 'onDragEnd'> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, disabled, leftIcon, rightIcon, ...props }, ref) => {
    const variants: Record<ButtonVariant, string> = {
      primary: 'bg-white text-black hover:bg-neutral-200 shadow-[0_8px_16px_rgba(255,255,255,0.05)]',
      secondary: 'bg-brand-surface text-white hover:bg-neutral-800 border border-white/5',
      outline: 'bg-transparent border border-white/10 text-white hover:bg-white/5',
      ghost: 'bg-transparent text-neutral-400 hover:text-white hover:bg-white/5',
      danger: 'bg-danger/10 text-danger border border-danger/20 hover:bg-danger/20',
      tactical: 'bg-brand-accent/10 text-brand-accent border border-brand-accent/30 hover:bg-brand-accent/20 shadow-[0_0_20px_rgba(59,130,246,0.1)]',
      glass: 'glass-panel text-white hover:bg-white/10',
    };

    const sizes: Record<ButtonSize, string> = {
      xs: 'px-2.5 py-1 text-[9px] font-bold uppercase tracking-widest rounded-sm',
      sm: 'px-3.5 py-1.5 text-[10px] font-extrabold uppercase tracking-widest rounded-md',
      md: 'px-5 py-2.5 text-[11px] font-black uppercase tracking-[0.15em] rounded-lg',
      lg: 'px-7 py-3.5 text-xs font-black uppercase tracking-[0.2em] rounded-xl',
      xl: 'px-9 py-4.5 text-sm font-black uppercase tracking-[0.25em] rounded-2xl',
    };

    return (
      <motion.button
        ref={ref as any}
        whileTap={{ scale: 0.97 }}
        disabled={isLoading || disabled}
        className={cn(
          'inline-flex items-center justify-center gap-2 transition-all focus:outline-none focus:ring-2 focus:ring-brand-accent/50 disabled:opacity-30 disabled:pointer-events-none whitespace-nowrap overflow-hidden relative group',
          variants[variant],
          sizes[size],
          className
        )}
        {...(props as HTMLMotionProps<"button">)}
      >
        <div className={cn(
          "flex items-center justify-center gap-2 transition-all duration-300",
          isLoading ? "opacity-0 scale-90 blur-sm" : "opacity-100 scale-100 blur-0"
        )}>
          {leftIcon && <span className="shrink-0">{leftIcon}</span>}
          {children}
          {rightIcon && <span className="shrink-0">{rightIcon}</span>}
        </div>

        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent opacity-60" />
          </div>
        )}

        {/* Tactical Hover Effect */}
        <div className="absolute inset-0 bg-white/0 group-hover:bg-white/5 transition-colors pointer-events-none" />
      </motion.button>
    );
  }
);

Button.displayName = 'Button';
