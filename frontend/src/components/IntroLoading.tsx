import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Heart } from 'lucide-react';

export const IntroLoading = () => {
  const [progress, setProgress] = useState(0);
  // Read directly from localStorage — this renders before UserContext is ready
  const isLite = localStorage.getItem('sealbot-lite-mode') === 'true' ||
    (() => { const c = navigator.hardwareConcurrency || 4; return c <= 4; })();

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
    } catch {}

    return () => clearInterval(progressInterval);
  }, []);

  return (
    <div className="fixed inset-0 bg-[#040908] flex flex-col items-center justify-center p-8 overflow-hidden z-[999] selection:bg-transparent">
      {/* Aurora Swells — skipped on lite devices */}
      {!isLite && (
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-[-10%] left-[-10%] w-[120%] h-[60%] bg-brand-accent/5 blur-[120px] rounded-[100%] animate-aurora mix-blend-screen" />
          <div className="absolute bottom-[-20%] right-[-10%] w-[100%] h-[70%] bg-brand-accent/5 blur-[150px] rounded-[100%] animate-aurora mix-blend-screen" style={{ animationDelay: '-4s' }} />
          <div className="absolute inset-0 bg-mesh opacity-30" />
        </div>
      )}

      {/* Main Branding Core */}
      <div className="relative z-10 flex flex-col items-center">
        <div className="relative w-48 h-48 mb-16 flex items-center justify-center">
          {/* Breathing Rings */}
          {!isLite && <div className="absolute inset-0 rounded-full border border-white/5 animate-pulse-ring" />}
          {!isLite && <div className="absolute inset-4 rounded-full border border-brand-accent/10 animate-pulse-ring" style={{ animationDelay: '1s' }} />}
          <div className="absolute inset-8 rounded-[2rem] bg-brand-midnight/80 border border-white/10 flex items-center justify-center overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-tr from-brand-accent/10 via-transparent to-transparent opacity-50" />
            <motion.div
              animate={isLite ? undefined : { 
                scale: [1, 1.15, 1],
              }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
            >
              <Sparkles className="text-brand-accent drop-shadow-md" size={44} strokeWidth={2} />
            </motion.div>
          </div>
          
          {/* Rotating Ring */}
          {!isLite && (
            <motion.div 
              animate={{ rotate: 360 }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              className="absolute inset-0 border-t border-brand-accent/20 rounded-full"
            />
          )}
        </div>

        {/* Minimalist Info */}
        <div className="text-center">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="space-y-6"
          >
            <div className="space-y-2">
              <h1 className="text-3xl font-black text-white uppercase tracking-widest leading-none">
                Seal<span className="text-brand-accent text-gradient">Bot</span>
              </h1>
              <div className="flex items-center justify-center space-x-2 text-slate-400">
                <span className="w-2 h-2 rounded-full bg-brand-accent animate-pulse shadow-neon" />
                <p className="text-[11px] font-bold uppercase tracking-widest opacity-80">Opening Summoning Portal...</p>
              </div>
            </div>

            <div className="flex flex-col items-center space-y-4 pt-4">
              <div className="relative w-48 h-1.5 bg-white/10 rounded-full overflow-hidden shadow-inner">
                <motion.div 
                  className="absolute inset-y-0 left-0 bg-gradient-to-r from-brand-accent to-brand-accent-secondary shadow-neon"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-[10px] font-black text-brand-accent uppercase tracking-widest tabular-nums drop-shadow-md">{Math.floor(progress)}%</p>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Branded Metadata */}
      <div className="absolute bottom-12 inset-x-0 flex flex-col items-center opacity-20 hover:opacity-100 transition-opacity duration-700 cursor-default">
        <Heart size={14} className="text-brand-accent mb-2 opacity-50" />
        <p className="text-[9px] font-bold text-white/50 uppercase tracking-widest">Seal Your Waifu • v2.0</p>
      </div>
    </div>
  );
};
