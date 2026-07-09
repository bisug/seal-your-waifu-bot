import { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Gem, Sparkles, ShieldCheck, Zap, Lock, Database } from 'lucide-react';

const loadingSteps = [
  'SYNCHRONIZING ARCHIVES',
  'DECRYPTING ASSET DATA',
  'MAPPING BIOMETRIC SEALS',
  'FINALIZING HANDSHAKE',
];

const cardFaces = [
  { letter: 'S', icon: ShieldCheck, color: 'text-sky-500', bg: 'bg-sky-500/10' },
  { letter: 'E', icon: Zap, color: 'text-amber-500', bg: 'bg-amber-500/10' },
  { letter: 'A', icon: Database, color: 'text-purple-500', bg: 'bg-purple-500/10' },
  { letter: 'L', icon: Lock, color: 'text-emerald-500', bg: 'bg-emerald-500/10' },
];

export const IntroLoading = () => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) return 100;
        const step = Math.random() * 5 + 2;
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
    <div className="fixed inset-0 z-[999] flex flex-col items-center justify-center bg-brand-midnight px-8 select-none">
      <div className="w-full max-w-sm space-y-12">
        {/* Logo Animation */}
        <div className="relative h-48 flex items-center justify-center">
            <AnimatePresence mode="wait">
                <motion.div
                    key={currentStep}
                    initial={{ opacity: 0, scale: 0.9, filter: 'blur(10px)' }}
                    animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
                    exit={{ opacity: 0, scale: 1.1, filter: 'blur(10px)' }}
                    className="absolute inset-0 flex items-center justify-center"
                >
                    <div className="relative">
                        <div className="absolute -inset-8 bg-brand-accent/20 rounded-full blur-3xl opacity-50 animate-pulse" />
                        <ShieldCheck size={80} className="text-white relative z-10 opacity-20" strokeWidth={1} />
                    </div>
                </motion.div>
            </AnimatePresence>

            <div className="absolute inset-0 flex items-center justify-center gap-3">
                {cardFaces.map((card, i) => {
                    const isLoaded = progress > (i * 25);
                    return (
                        <motion.div
                            key={card.letter}
                            initial={{ y: 20, opacity: 0 }}
                            animate={{
                                y: isLoaded ? 0 : 20,
                                opacity: isLoaded ? 1 : 0.1,
                                scale: isLoaded ? 1 : 0.9
                            }}
                            className={`w-12 h-16 rounded-xl border ${isLoaded ? 'border-white/10 bg-white/5' : 'border-white/5 bg-transparent'} flex flex-col items-center justify-center gap-2 shadow-2xl`}
                        >
                            <card.icon size={14} className={isLoaded ? card.color : 'text-neutral-600'} />
                            <span className="text-xl font-black text-white">{card.letter}</span>
                        </motion.div>
                    )
                })}
            </div>
        </div>

        {/* Progress Info */}
        <div className="space-y-6">
            <div className="space-y-2">
                <div className="flex justify-between items-end">
                    <span className="text-[10px] font-black text-white tracking-[0.3em] uppercase">{currentStep}</span>
                    <span className="text-xs font-mono text-brand-accent font-bold tabular-nums">{Math.round(progress)}%</span>
                </div>
                <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                    <motion.div
                        className="h-full bg-brand-accent"
                        animate={{ width: `${progress}%` }}
                        transition={{ ease: "circOut" }}
                    />
                </div>
            </div>

            <div className="flex justify-center gap-1.5">
                {[...Array(4)].map((_, i) => (
                    <div
                        key={i}
                        className={`h-1 w-8 rounded-full transition-colors duration-500 ${progress > (i * 25) ? 'bg-brand-accent' : 'bg-white/5'}`}
                    />
                ))}
            </div>
        </div>

        <div className="text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[9px] font-black text-neutral-500 uppercase tracking-widest">System Operational / v2.1-BETA</span>
            </div>
        </div>
      </div>
    </div>
  );
};
