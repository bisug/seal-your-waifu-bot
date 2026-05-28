import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export const IntroLoading = () => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) return 100;
        const remaining = 100 - prev;
        const increment = Math.max(0.5, Math.random() * (remaining / 10));
        return Math.min(100, prev + increment);
      });
    }, 150);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="fixed inset-0 bg-[#09090b] flex flex-col items-center justify-center p-6 z-[999] select-none">
      <div className="w-full max-w-[280px] flex flex-col items-center">
        {/* Logo/Icon Container */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="relative mb-12"
        >
          <div className="w-20 h-20 rounded-2xl bg-zinc-900 border border-white/10 flex items-center justify-center relative overflow-hidden">
             <div className="absolute inset-0 bg-gradient-to-br from-brand-accent/10 to-transparent opacity-50" />
             <div className="text-brand-accent relative">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                </svg>
             </div>
          </div>
        </motion.div>

        {/* Brand Text */}
        <div className="text-center mb-16">
          <motion.h1
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.8 }}
            className="text-xl font-bold text-white tracking-[0.2em] uppercase mb-2"
          >
            Seal<span className="text-brand-accent">Bot</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.4 }}
            transition={{ delay: 0.4, duration: 1 }}
            className="text-[10px] font-medium text-white tracking-[0.3em] uppercase"
          >
            Digital Collectibles
          </motion.p>
        </div>

        {/* Loading Progress */}
        <div className="w-full space-y-4">
          <div className="h-[2px] w-full bg-zinc-800 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-brand-accent"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ ease: "linear" }}
            />
          </div>
          <div className="flex justify-between items-center px-1">
             <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">
                {progress < 100 ? 'Establishing Link' : 'Ready'}
             </span>
             <span className="text-[9px] font-bold text-brand-accent tabular-nums tracking-widest">
                {Math.floor(progress)}%
             </span>
          </div>
        </div>
      </div>

      {/* Footer Branding */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.2 }}
        transition={{ delay: 1, duration: 1 }}
        className="absolute bottom-10 flex flex-col items-center gap-2"
      >
        <div className="w-1 h-1 rounded-full bg-white/50" />
        <span className="text-[8px] font-bold text-white tracking-[0.4em] uppercase">Production v2.5</span>
      </motion.div>
    </div>
  );
};
