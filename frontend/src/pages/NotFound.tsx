import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { Home, Compass } from 'lucide-react';

export const NotFound = ({ onReset }: { onReset: () => void }) => {
  useEffect(() => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
  }, []);

  return (
    <div className="absolute inset-0 z-[500] bg-zinc-950 flex flex-col items-center justify-center p-8 text-center select-none">
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
        
        <h2 className="text-sm font-bold text-zinc-100 uppercase tracking-widest mb-2">Endpoint Not Found</h2>
        <p className="text-[11px] font-medium text-zinc-500 uppercase tracking-widest leading-relaxed mb-10 max-w-[200px]">
          The requested coordinate does not exist in the current sector.
        </p>

        <button 
          onClick={() => {
            window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
            onReset();
          }}
          className="w-full py-4 rounded-xl bg-white text-zinc-950 font-bold uppercase tracking-[0.2em] text-[10px] transition-transform active:scale-[0.98] flex items-center justify-center gap-3"
        >
          <Home size={14} />
          <span>Return to base</span>
        </button>
      </motion.div>
      
      <div className="absolute bottom-10 opacity-10">
         <span className="text-[8px] font-bold text-white tracking-[0.5em] uppercase">System Error / Null Pointer</span>
      </div>
    </div>
  );
};
