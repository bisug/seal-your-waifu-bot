import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { Home, Compass } from 'lucide-react';

export const NotFound = ({ onReset }: { onReset: () => void }) => {
  useEffect(() => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
  }, []);

  return (
    <div className="min-h-[60vh] bg-zinc-950 flex flex-col items-center justify-center p-8 text-center select-none">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-xs flex flex-col items-center"
      >
        <div className="w-16 h-16 rounded-2xl bg-zinc-900 border border-white/5 flex items-center justify-center mb-8">
           <Compass className="text-zinc-500" size={32} strokeWidth={1.5} />
        </div>

        <h1 className="text-4xl font-bold text-white tracking-tighter mb-4">404</h1>
        
        <h2 className="text-base font-bold text-zinc-100 mb-2">Page not found</h2>
        <p className="text-sm font-medium text-zinc-500 leading-relaxed mb-10 max-w-[240px]">
          This section is not available. Return to your profile and keep going.
        </p>

        <button 
          onClick={() => {
            window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
            onReset();
          }}
          className="w-full py-4 rounded-xl bg-white text-zinc-950 font-bold text-sm transition-transform active:scale-[0.98] flex items-center justify-center gap-3"
        >
          <Home size={14} />
          <span>Back to profile</span>
        </button>
      </motion.div>
    </div>
  );
};
