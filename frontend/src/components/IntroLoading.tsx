import { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldCheck, Zap, Lock, Heart, Terminal } from 'lucide-react';
import { cn } from '../utils';

const loadingSteps = [
  'INITIALIZING',
  'SYNC ARCHIVES',
  'SECURE LINK',
  'MAP ASSETS',
  'AUTHORIZING',
];

const cardFaces = [
  { letter: 'S', icon: ShieldCheck, color: 'text-brand-accent' },
  { letter: 'E', icon: Zap, color: 'text-amber-500' },
  { letter: 'A', icon: Heart, color: 'text-red-500' },
  { letter: 'L', icon: Lock, color: 'text-emerald-500' },
];

export const IntroLoading = () => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) return 100;
        const step = Math.random() * 12 + 6;
        return Math.min(100, prev + step);
      });
    }, 180);

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
    <div className="fixed inset-0 z-[999] flex flex-col items-center justify-center bg-zinc-950 px-8 select-none">
      <div className="w-full max-w-xs space-y-12 relative z-10">
        {/* Visual Brand */}
        <div className="relative h-32 flex items-center justify-center">
            <div className="flex items-center justify-center gap-2.5">
                {cardFaces.map((card, i) => {
                    const isLoaded = progress > (i * 22);
                    return (
                        <motion.div
                            key={card.letter}
                            initial={{ y: 8, opacity: 0 }}
                            animate={{
                                y: isLoaded ? 0 : 8,
                                opacity: isLoaded ? 1 : 0.05,
                                scale: isLoaded ? 1 : 0.95
                            }}
                            className={cn(
                                "w-11 h-14 rounded-md border flex flex-col items-center justify-center gap-1.5 transition-all duration-500",
                                isLoaded ? 'border-white/10 bg-zinc-900' : 'border-white/5 bg-transparent'
                            )}
                        >
                            <card.icon size={12} className={cn("transition-colors duration-500", isLoaded ? card.color : 'text-zinc-900')} />
                            <span className="text-lg font-mono font-bold text-zinc-100 leading-none">{card.letter}</span>
                        </motion.div>
                    )
                })}
            </div>
        </div>

        {/* Progress */}
        <div className="space-y-5">
            <div className="space-y-2.5">
                <div className="flex justify-between items-end px-1">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={currentStep}
                            initial={{ opacity: 0, x: -8 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 8 }}
                            className="flex items-center gap-2"
                        >
                            <Terminal size={10} className="text-brand-accent" />
                            <span className="text-[9px] font-bold text-zinc-100 tracking-widest uppercase">
                                {currentStep}
                            </span>
                        </motion.div>
                    </AnimatePresence>
                    <span className="text-[10px] font-mono text-zinc-500 font-bold tabular-nums">{Math.round(progress)}%</span>
                </div>
                <div className="h-1 w-full bg-zinc-900 rounded-full overflow-hidden border border-white/5 p-[1px]">
                    <motion.div
                        className="h-full bg-brand-accent rounded-full"
                        animate={{ width: `${progress}%` }}
                        transition={{ ease: "easeOut", duration: 0.4 }}
                    />
                </div>
            </div>

            <div className="flex items-center justify-between px-1 opacity-20">
               <div className="flex gap-1.5">
                  <div className="h-0.5 w-3 bg-zinc-100 rounded-full" />
                  <div className="h-0.5 w-0.5 bg-zinc-100 rounded-full" />
                  <div className="h-0.5 w-0.5 bg-zinc-100 rounded-full" />
               </div>
               <span className="text-[7px] font-bold text-zinc-600 uppercase tracking-widest">Protocol Link Active</span>
            </div>
        </div>

        <div className="text-center pt-4">
            <div className="inline-flex items-center gap-2.5 px-3 py-1.5 rounded-md bg-zinc-900 border border-white/5">
                <div className="w-1 h-1 rounded-full bg-emerald-500" />
                <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">System Ready</span>
            </div>
        </div>
      </div>
    </div>
  );
};
