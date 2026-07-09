import { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldCheck, Zap, Lock, Database } from 'lucide-react';

const loadingSteps = [
  'INITIALIZING LINK',
  'SYNC ARCHIVES',
  'DECRYPT ASSETS',
  'MAP BIOMETRICS',
  'FINALIZING',
];

const cardFaces = [
  { letter: 'S', icon: ShieldCheck, color: 'text-sky-500' },
  { letter: 'E', icon: Zap, color: 'text-amber-500' },
  { letter: 'A', icon: Database, color: 'text-purple-500' },
  { letter: 'L', icon: Lock, color: 'text-emerald-500' },
];

export const IntroLoading = () => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) return 100;
        const step = Math.random() * 8 + 3;
        return Math.min(100, prev + step);
      });
    }, 120);

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
    <div className="fixed inset-0 z-[999] flex flex-col items-center justify-center bg-[#050506] px-8 select-none">
      <div className="w-full max-w-xs space-y-12">
        {/* Visual Animation */}
        <div className="relative h-32 flex items-center justify-center">
            <div className="absolute inset-0 flex items-center justify-center gap-2">
                {cardFaces.map((card, i) => {
                    const isLoaded = progress > (i * 25);
                    return (
                        <motion.div
                            key={card.letter}
                            initial={{ y: 10, opacity: 0 }}
                            animate={{
                                y: isLoaded ? 0 : 10,
                                opacity: isLoaded ? 1 : 0.05,
                                scale: isLoaded ? 1 : 0.95
                            }}
                            className={`w-10 h-14 rounded-md border ${isLoaded ? 'border-white/10 bg-white/[0.02]' : 'border-white/5 bg-transparent'} flex flex-col items-center justify-center gap-1.5 shadow-xl relative overflow-hidden`}
                        >
                            {isLoaded && (
                                <motion.div
                                    initial={{ x: '-100%' }}
                                    animate={{ x: '100%' }}
                                    transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                                    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.05] to-transparent"
                                />
                            )}
                            <card.icon size={12} className={isLoaded ? card.color : 'text-neutral-800'} />
                            <span className="text-base font-black text-white font-mono">{card.letter}</span>
                        </motion.div>
                    )
                })}
            </div>
        </div>

        {/* Progress Info */}
        <div className="space-y-4">
            <div className="space-y-2">
                <div className="flex justify-between items-end px-0.5">
                    <AnimatePresence mode="wait">
                        <motion.span
                            key={currentStep}
                            initial={{ opacity: 0, x: -5 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 5 }}
                            className="text-[9px] font-black text-white tracking-[0.3em] uppercase"
                        >
                            {currentStep}
                        </motion.span>
                    </AnimatePresence>
                    <span className="text-[10px] font-mono text-brand-accent font-bold tabular-nums">{Math.round(progress)}%</span>
                </div>
                <div className="h-0.5 w-full bg-white/[0.03] rounded-full overflow-hidden border border-white/[0.02]">
                    <motion.div
                        className="h-full bg-brand-accent shadow-[0_0_8px_rgba(59,130,246,0.5)]"
                        animate={{ width: `${progress}%` }}
                        transition={{ ease: "easeOut", duration: 0.2 }}
                    />
                </div>
            </div>
        </div>

        <div className="text-center pt-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-sm bg-white/[0.02] border border-white/[0.05]">
                <div className="w-1 h-1 rounded-full bg-brand-accent animate-pulse" />
                <span className="text-[8px] font-black text-neutral-600 uppercase tracking-widest">Seal Protocol Secured / v2.2.0</span>
            </div>
        </div>
      </div>
    </div>
  );
};
