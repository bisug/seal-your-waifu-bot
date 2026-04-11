import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Cpu } from 'lucide-react';

const BOOT_LOGS = [
  "Initializing Harem System...",
  "Loading Character Database...",
  "Syncing Collection Data...",
  "Gathering Waifus...",
  "Establishing Secure Link...",
  "Calibrating Interface...",
  "Seal Bot Ready.",
];

export const IntroLoading = () => {
  const [logIndex, setLogIndex] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const logInterval = setInterval(() => {
      setLogIndex((prev) => (prev < BOOT_LOGS.length - 1 ? prev + 1 : prev));
    }, 600);

    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) return 100;
        const next = prev + Math.random() * 5;
        return next > 100 ? 100 : next;
      });
    }, 100);

    // Haptic on start
    try {
        window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
    } catch (e) {
        // Silently ignore
    }

    return () => {
      clearInterval(logInterval);
      clearInterval(progressInterval);
    };
  }, []);

  return (
    <div className="fixed inset-0 bg-brand-midnight flex flex-col items-center justify-center p-8 overflow-hidden z-[999]">
      {/* Cinematic Background Mesh */}
      <div className="absolute inset-0 bg-mesh opacity-50" />
      <div className="absolute top-[-20%] left-[-20%] w-[80%] h-[80%] bg-brand-neon/10 blur-[150px] rounded-full animate-pulse" />
      <div className="absolute bottom-[-20%] right-[-20%] w-[80%] h-[80%] bg-brand-accent/5 blur-[150px] rounded-full animate-pulse" style={{ animationDelay: '1s' }} />

      {/* Main Core Section */}
      <div className="relative z-10 flex flex-col items-center">
        {/* The Neural Seal / Core */}
        <div className="relative w-40 h-40 mb-12">
            {/* Outer Rings */}
            <motion.div 
                animate={{ rotate: 360 }}
                transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
                className="absolute inset-0 border-[0.5px] border-brand-neon/20 rounded-full"
            />
            <motion.div 
                animate={{ rotate: -360 }}
                transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
                className="absolute inset-4 border-[1px] border-brand-accent/30 rounded-full border-dashed"
            />
            <motion.div 
                animate={{ rotate: 360 }}
                transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                className="absolute inset-8 border-[2px] border-t-brand-neon rounded-full"
            />

            {/* Inner Glow and Icon */}
            <div className="absolute inset-0 flex items-center justify-center">
                <motion.div 
                    animate={{ 
                        scale: [1, 1.1, 1],
                        opacity: [0.5, 0.8, 0.5]
                    }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="w-20 h-20 bg-brand-neon/20 rounded-full blur-2xl absolute"
                />
                <div className="relative bg-brand-midnight/40 backdrop-blur-xl border border-brand-neon/20 w-16 h-16 rounded-2xl flex items-center justify-center shadow-2xl shadow-brand-neon/40 ring-1 ring-brand-neon/50">
                    <Shield className="text-brand-neon" size={32} />
                </div>
            </div>

            {/* Orbiting Particles */}
            {[...Array(3)].map((_, i) => (
                <motion.div
                    key={i}
                    animate={{ rotate: 360 }}
                    transition={{ duration: 3 + i, repeat: Infinity, ease: "linear" }}
                    className="absolute inset-0"
                >
                    <div 
                        className="w-1.5 h-1.5 bg-brand-neon rounded-full absolute" 
                        style={{ 
                            top: '50%', 
                            left: i === 0 ? '-2px' : i === 1 ? 'auto' : '50%',
                            right: i === 1 ? '-2px' : 'auto',
                            bottom: i === 2 ? '-2px' : 'auto',
                            boxShadow: '0 0 10px #00f2ff'
                        }} 
                    />
                </motion.div>
            ))}
        </div>

        {/* Progress Text */}
        <div className="text-center space-y-4">
            <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col items-center"
            >
                <div className="flex items-center space-x-2 text-brand-neon mb-1">
                    <Cpu size={14} className="animate-pulse" />
                    <span className="text-[10px] font-black uppercase tracking-[0.5em]">Harem Index</span>
                </div>
                <div className="h-[1px] w-48 bg-white/10 relative overflow-hidden">
                    <motion.div 
                        className="absolute inset-y-0 left-0 bg-brand-neon"
                        style={{ width: `${progress}%` }}
                    />
                </div>
                <span className="text-[8px] font-mono text-slate-500 mt-2 tabular-nums">{Math.floor(progress)}% LOADED</span>
            </motion.div>

            {/* Scrolling Logs */}
            <div className="h-4 flex items-center justify-center overflow-hidden">
                <AnimatePresence mode="wait">
                    <motion.p
                        key={logIndex}
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        exit={{ y: -20, opacity: 0 }}
                        className="text-[9px] font-bold text-slate-300 uppercase tracking-widest"
                    >
                        {BOOT_LOGS[logIndex]}
                    </motion.p>
                </AnimatePresence>
            </div>
        </div>
      </div>

      {/* Decorative Matrix-like Lines at corners */}
      <div className="absolute top-8 left-8 border-t border-l border-brand-neon/30 w-8 h-8 rounded-tl-lg" />
      <div className="absolute top-8 right-8 border-t border-r border-brand-neon/30 w-8 h-8 rounded-tr-lg" />
      <div className="absolute bottom-8 left-8 border-b border-l border-brand-neon/30 w-8 h-8 rounded-bl-lg" />
      <div className="absolute bottom-8 right-8 border-b border-r border-brand-neon/30 w-8 h-8 rounded-br-lg" />
      
      {/* Subtle pulsing background tag */}
      <div className="absolute bottom-12 text-[8px] font-mono text-white/10 uppercase tracking-[1em] rotate-90 right-0 origin-bottom-right">
        Seal-Bot Protocol v2.0
      </div>
    </div>
  );
};
