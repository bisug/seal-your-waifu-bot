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
              size={14}
              className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-600 group-focus-within:text-brand-accent transition-colors duration-300"
            />
          )}
          <input
            ref={ref}
            className={cn(
              "w-full bg-[#0a0a0c] border border-white/10 rounded-lg py-3 text-[11px] font-bold transition-all duration-300 placeholder:text-neutral-700 text-white outline-none focus:border-brand-accent/50 focus:ring-4 focus:ring-brand-accent/5 uppercase tracking-[0.1em]",
              Icon ? "pl-11 pr-4" : "px-4",
              error && "border-danger/30 focus:border-danger/50 focus:ring-danger/5",
              className
            )}
            {...props}
          />
        </div>
        {error && <p className="text-[9px] font-black text-danger uppercase tracking-widest pl-1 animate-in">{error}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';
