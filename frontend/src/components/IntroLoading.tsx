import { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldCheck, Zap, Lock, Database, Heart, Target, Terminal } from 'lucide-react';
import { cn } from '../utils';

const loadingSteps = [
  'INITIALIZING_LINK',
  'SYNC_ARCHIVES',
  'SECURE_PERSONNEL',
  'MAP_BIOMETRICS',
  'AUTHORIZING',
];

const cardFaces = [
  { letter: 'S', icon: ShieldCheck, color: 'text-brand-accent' },
  { letter: 'E', icon: Zap, color: 'text-warning' },
  { letter: 'A', icon: Heart, color: 'text-danger' },
  { letter: 'L', icon: Lock, color: 'text-success' },
];

export const IntroLoading = () => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) return 100;
        const step = Math.random() * 12 + 4;
        return Math.min(100, prev + step);
      });
    }, 150);

    return () => clearInterval(timer);
  }, []);

  const currentStep = useMemo(() => {
    const index = Math.min(
      loadingSteps.length - 1,
      Math.floor((progress / 100) * loadingSteps.length)
    );
    return loadingSteps[index];
  }, [progress]);

  return (
    <div className="fixed inset-0 z-[999] flex flex-col items-center justify-center bg-brand-midnight px-8 select-none tactical-noise">
      <div className="tactical-grid absolute inset-0 opacity-10 pointer-events-none" />

      <div className="w-full max-w-sm space-y-16 relative z-10">
        {/* Visual Brand Animation */}
        <div className="relative h-40 flex items-center justify-center">
            <div className="absolute inset-0 flex items-center justify-center gap-3">
                {cardFaces.map((card, i) => {
                    const isLoaded = progress > (i * 22);
                    return (
                        <motion.div
                            key={card.letter}
                            initial={{ y: 15, opacity: 0 }}
                            animate={{
                                y: isLoaded ? 0 : 15,
                                opacity: isLoaded ? 1 : 0.03,
                                scale: isLoaded ? 1 : 0.9
                            }}
                            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                            className={cn(
                                "w-12 h-16 rounded-xl border flex flex-col items-center justify-center gap-2 shadow-2xl relative overflow-hidden transition-all duration-700",
                                isLoaded ? 'border-white/[0.08] bg-white/[0.02]' : 'border-white/[0.03] bg-transparent'
                            )}
                        >
                            {isLoaded && (
                                <motion.div
                                    initial={{ x: '-100%' }}
                                    animate={{ x: '100%' }}
                                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                                    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.05] to-transparent"
                                />
                            )}
                            <card.icon size={14} className={cn("transition-colors duration-700", isLoaded ? card.color : 'text-neutral-900')} fill={card.letter === 'A' && isLoaded ? 'currentColor' : 'none'} />
                            <span className="text-xl font-black text-white font-mono leading-none tracking-tight">{card.letter}</span>
                        </motion.div>
                    )
                })}
            </div>

            <div className="absolute -bottom-4 flex gap-1.5">
               {[0,1,2,3].map(i => (
                   <motion.div
                     key={i}
                     animate={{ opacity: [0.2, 1, 0.2] }}
                     transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.2 }}
                     className="w-1 h-1 rounded-full bg-brand-accent"
                   />
               ))}
            </div>
        </div>

        {/* Progress System */}
        <div className="space-y-6">
            <div className="space-y-3">
                <div className="flex justify-between items-end px-1">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={currentStep}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 10 }}
                            className="flex items-center gap-2.5"
                        >
                            <Terminal size={12} className="text-brand-accent" />
                            <span className="text-[10px] font-black text-white tracking-[0.3em] uppercase font-mono">
                                {currentStep}
                            </span>
                        </motion.div>
                    </AnimatePresence>
                    <span className="text-[12px] font-mono text-brand-accent font-black tabular-nums drop-shadow-[0_0_8px_rgba(59,130,246,0.3)]">{Math.round(progress)}%</span>
                </div>
                <div className="h-1.5 w-full bg-white/[0.02] rounded-full overflow-hidden border border-white/[0.05] p-[1px]">
                    <motion.div
                        className="h-full bg-brand-accent rounded-full shadow-[0_0_15px_rgba(59,130,246,0.4)] relative overflow-hidden"
                        animate={{ width: `${progress}%` }}
                        transition={{ ease: "easeOut", duration: 0.3 }}
                    >
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent w-full animate-shimmer" />
                    </motion.div>
                </div>
            </div>

            <div className="flex items-center justify-between px-1 opacity-40">
               <div className="flex gap-2">
                  <div className="h-1 w-4 bg-white/20 rounded-full" />
                  <div className="h-1 w-1 bg-white/20 rounded-full" />
                  <div className="h-1 w-1 bg-white/20 rounded-full" />
               </div>
               <span className="text-[7px] font-black text-neutral-500 uppercase tracking-[0.4em]">Node_Secure_Link</span>
            </div>
        </div>

        <div className="text-center pt-8">
            <div className="inline-flex items-center gap-3 px-4 py-2 rounded-xl bg-black/40 border border-white/[0.05] shadow-xl">
                <div className="w-1.5 h-1.5 rounded-full bg-success shadow-[0_0_8px_rgba(16,185,129,0.5)] animate-pulse" />
                <span className="text-[9px] font-black text-neutral-500 uppercase tracking-[0.25em]">PROTOCOL_v2.4_READY</span>
            </div>
        </div>
      </div>

      <div className="absolute bottom-12 flex flex-col items-center gap-4 opacity-10">
         <Target size={24} />
         <p className="text-[8px] font-black uppercase tracking-[1em] pl-4">Syncing_Mainframe</p>
      </div>
    </div>
  );
};
