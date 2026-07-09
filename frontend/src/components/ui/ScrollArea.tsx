import { type ReactNode } from 'react';

interface ScrollAreaProps {
  children: ReactNode;
  className?: string;
}

/**
 * Horizontal Scroll with Fade Mask
 */
export const ScrollArea = ({ children, className = "" }: ScrollAreaProps) => (
  <div className={`relative ${className}`}>
    <div className="scroll-fade-mask overflow-x-auto no-scrollbar flex space-x-2 py-1">
      {children}
    </div>
  </div>
);
