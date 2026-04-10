import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { Compass, Home, Map } from 'lucide-react';

/**
 * Cinematic 'Lost in the Void' (404) Portal.
 * A high-fidelity fallback for any unknown navigation paths or corrupted states.
 */
export const NotFound = ({ onReset }) => {
  useEffect(() => {
    // Heavy Haptic Impact on entry to signal navigation break
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('heavy');
  }, []);

  const handleReturn = () => {
    window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
    if (onReset) onReset();
  };

  return (
    <div className="fixed inset-0 z-[500] bg-brand-midnight flex flex-col items-center justify-center p-8 text-center overflow-hidden">
      {/* Background Cinematic Shimmer */}
      <div className="absolute inset-0 opacity-20 blur-3xl scale-125 animate-shimmer pointer-events-none" 
           style={{ background: 'radial-gradient(circle at center, var(--color-brand-neon), transparent 70%)' }} />
      
      <motion.div 
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", damping: 12, stiffness: 100 }}
        className="relative z-10"
      >
        <div className="mb-8 relative inline-block">
          <motion.div 
            animate={{ rotate: 360 }}
            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            className="text-brand-neon/20 absolute -inset-10"
          >
            <Compass size={120} strokeWidth={0.5} />
          </motion.div>
          <div className="w-24 h-24 rounded-3xl bg-brand-neon/10 border-2 border-brand-neon flex items-center justify-center neon-shadow">
            <Map size={40} className="text-brand-neon" />
          </div>
        </div>

        <h1 className="text-7xl font-black uppercase tracking-tighter italic mb-2 text-white/5 opacity-10 absolute left-1/2 -top-12 -translate-x-1/2 select-none">
          VOID
        </h1>
        
        <h2 className="text-2xl font-black uppercase tracking-widest mb-4">SIGNAL LOST</h2>
        <p className="text-xs font-bold text-slate-500 uppercase tracking-widest max-w-[240px] leading-relaxed mb-10">
          You have reached a region outside the known sectors of the Seal-bot universe. 
        </p>

        <button 
          onClick={handleReturn}
          className="w-full max-w-[280px] py-5 rounded-2xl bg-white text-brand-midnight font-black uppercase tracking-[0.3em] text-[10px] shadow-2xl hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center space-x-3 group"
        >
          <Home size={16} className="group-hover:animate-bounce" />
          <span>RETURN TO REALITY</span>
        </button>
      </motion.div>
      
      <div className="absolute bottom-10 left-1/2 -translate-x-1/2 flex items-center space-x-4 opacity-20 pointer-events-none">
         <span className="text-[10px] font-black uppercase tracking-[0.5em]">ERROR_404</span>
         <div className="w-1 h-1 rounded-full bg-brand-neon" />
         <span className="text-[10px] font-black uppercase tracking-[0.5em]">VOID_LINK</span>
      </div>
    </div>
  );
};
