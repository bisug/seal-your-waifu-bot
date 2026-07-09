import React from 'react';
import { cn } from '../../utils';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  icon?: React.ElementType;
  error?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, icon: Icon, error, ...props }, ref) => {
    return (
      <div className="space-y-1.5 w-full">
        <div className="relative group">
          {Icon && (
            <Icon
              size={16}
              className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-500 group-focus-within:text-brand-accent transition-colors"
            />
          )}
          <input
            ref={ref}
            className={cn(
              "w-full bg-brand-deep border border-white/10 rounded-xl py-2.5 text-sm font-medium transition-all placeholder:text-neutral-500 text-white outline-none focus:border-brand-accent/50 focus:ring-1 focus:ring-brand-accent/20",
              Icon ? "pl-10 pr-4" : "px-4",
              error && "border-red-500/50 focus:border-red-500 focus:ring-red-500/20",
              className
            )}
            {...props}
          />
        </div>
        {error && <p className="text-[10px] font-bold text-red-500 uppercase tracking-wider pl-1">{error}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';
