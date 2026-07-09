import React from 'react';
import { cn } from '../../utils';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  icon?: React.ElementType;
  error?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, icon: Icon, error, ...props }, ref) => {
    return (
      <div className="space-y-1 w-full">
        <div className="relative group">
          {Icon && (
            <Icon
              size={14}
              className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-600 group-focus-within:text-brand-accent transition-colors"
            />
          )}
          <input
            ref={ref}
            className={cn(
              "w-full bg-[#0a0a0c] border border-white/10 rounded-md py-2 text-xs font-bold transition-all placeholder:text-neutral-700 text-white outline-none focus:border-brand-accent/40 focus:ring-1 focus:ring-brand-accent/10 uppercase tracking-widest",
              Icon ? "pl-9 pr-3" : "px-3",
              error && "border-red-500/30 focus:border-red-500/50 focus:ring-red-500/5",
              className
            )}
            {...props}
          />
        </div>
        {error && <p className="text-[9px] font-black text-red-500 uppercase tracking-widest pl-1">{error}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';
