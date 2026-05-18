import React from 'react';

/**
 * Horizontal Scroll with Fade Mask
 */
export const ScrollArea = ({ children, className = "" }) => (
  <div className={`relative ${className}`}>
    <div className="scroll-fade-mask overflow-x-auto no-scrollbar flex space-x-2 py-1">
      {children}
    </div>
  </div>
);
