import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Cpu, Sparkles } from 'lucide-react';

export const IntroLoading = () => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) return 100;
        const next = prev + Math.random() * 8; // Faster, smoother loading
        return next > 100 ? 100 : next;
      });
    }, 150);

    try {
        window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
    } catch (e) {}

    return () => clearInterval(progressInterval);
  }, []);

  return (
    <div className="fixed inset-0 bg-[#040908] flex flex-col items-center justify-center p-8 overflow-hidden z-[999] selection:bg-transparent">
      {/* Premium Aurora Swells */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[120%] h-[60%] bg-brand-neon/5 blur-[120px] rounded-[100%] animate-aurora mix-blend-screen" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[100%] h-[70%] bg-brand-accent/5 blur-[150px] rounded-[100%] animate-aurora mix-blend-screen" style={{ animationDelay: '-4s' }} />
        <div className="absolute inset-0 bg-mesh opacity-30" />
      </div>

      {/* Main Branding Core */}
      <div className="relative z-10 flex flex-col items-center">
        <div className="relative w-48 h-48 mb-16 flex items-center justify-center">
          {/* Breathing Rings */}
          <div className="absolute inset-0 rounded-full border border-white/5 animate-pulse-ring" />
          <div className="absolute inset-4 rounded-full border border-brand-neon/10 animate-pulse-ring" style={{ animationDelay: '1s' }} />
          <div className="absolute inset-8 rounded-[2rem] bg-brand-midnight/40 backdrop-blur-3xl border border-white/10 shadow-2xl flex items-center justify-center overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-tr from-brand-neon/10 via-transparent to-transparent opacity-50" />
            <motion.div
              animate={{ 
                scale: [1, 1.15, 1],
                filter: ["drop-shadow(0 0 0px #34d39900)", "drop-shadow(0 0 15px #34d39966)", "drop-shadow(0 0 0px #34d39900)"]
              }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
            >
              <Cpu className="text-brand-neon" size={44} strokeWidth={1.5} />
            </motion.div>
          </div>
          
          {/* Rotating Data Bits */}
          <motion.div 
            animate={{ rotate: 360 }}
            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            className="absolute inset-0 border-t border-brand-neon/20 rounded-full"
          />
        </div>

        {/* Minimalist Info */}
        <div className="text-center">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="space-y-6"
          >
            <div className="space-y-1">
              <h1 className="text-2xl font-black text-white uppercase tracking-[0.4em] leading-none">Seal<span className="text-brand-neon">Bot</span></h1>
              <div className="flex items-center justify-center space-x-2 text-slate-500">
                <span className="w-1.5 h-1.5 rounded-full bg-brand-neon animate-pulse" />
                <p className="text-[10px] font-bold uppercase tracking-[0.3em] opacity-60">Neural Network Active</p>
              </div>
            </div>

            <div className="flex flex-col items-center space-y-3">
              <div className="relative w-40 h-[2px] bg-white/5 rounded-full overflow-hidden">
                <motion.div 
                  className="absolute inset-y-0 left-0 bg-brand-neon shadow-[0_0_10px_#34d399]"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-[8px] font-mono text-slate-600 uppercase tracking-[1em] tabular-nums">{Math.floor(progress)}%</p>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Branded Metadata */}
      <div className="absolute bottom-12 inset-x-0 flex flex-col items-center opacity-20 hover:opacity-100 transition-opacity duration-700 cursor-default">
        <Sparkles size={12} className="text-brand-neon mb-2" />
        <p className="text-[7px] font-mono text-white uppercase tracking-[0.5em]">Protocol Est. 2024 • Phase 2.0</p>
      </div>
    </div>
  );
};
