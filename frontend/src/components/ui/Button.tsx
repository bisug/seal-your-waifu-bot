import React from 'react';
import { cn } from '../../utils';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, disabled, ...props }, ref) => {
    const variants = {
      primary: 'bg-white text-black hover:bg-neutral-200 active:scale-[0.97]',
      secondary: 'bg-brand-surface text-white hover:bg-neutral-800 active:scale-[0.97] border border-white/5',
      outline: 'bg-transparent border border-white/10 text-white hover:bg-white/5 active:scale-[0.97]',
      ghost: 'bg-transparent text-neutral-400 hover:text-white hover:bg-white/5 active:scale-[0.97]',
      danger: 'bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500/20 active:scale-[0.97]',
    };

    const sizes = {
      xs: 'px-2 py-1 text-[10px] font-bold uppercase tracking-wider rounded-sm',
      sm: 'px-3 py-1.5 text-xs font-semibold rounded-md',
      md: 'px-4 py-2 text-sm font-semibold rounded-md',
      lg: 'px-6 py-3 text-base font-bold rounded-lg',
      xl: 'px-8 py-4 text-lg font-bold rounded-xl',
    };

    return (
      <button
        ref={ref}
        disabled={isLoading || disabled}
        className={cn(
          'inline-flex items-center justify-center transition-all focus:outline-none focus:ring-2 focus:ring-brand-accent focus:ring-offset-2 focus:ring-offset-background disabled:opacity-50 disabled:pointer-events-none whitespace-nowrap',
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {isLoading ? (
          <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
        ) : null}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
