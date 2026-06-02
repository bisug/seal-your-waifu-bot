import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Gem, Sparkles } from 'lucide-react';

const loadingSteps = [
  'Preparing your collection',
  'Checking daily shop',
  'Loading pets and eggs',
  'Almost ready',
];

const cardFaces = [
  { label: 'C', tone: 'from-zinc-700/70 to-zinc-900' },
  { label: 'R', tone: 'from-sky-500/60 to-zinc-900' },
  { label: 'E', tone: 'from-violet-500/60 to-zinc-900' },
];

export const IntroLoading = () => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) return 100;
        const next = prev + Math.max(1.2, (100 - prev) / 14);
        return Math.min(100, next);
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
    <div className="fixed inset-0 z-[999] flex items-center justify-center bg-brand-midnight px-6 select-none">
      <div className="w-full max-w-sm">
        <div className="relative h-64 mb-10 flex items-center justify-center">
          <motion.div
            className="absolute h-40 w-40 rounded-full border border-white/5"
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 18, ease: 'linear' }}
          />
          <motion.div
            className="absolute h-56 w-56 rounded-full border border-brand-accent/10"
            animate={{ rotate: -360 }}
            transition={{ repeat: Infinity, duration: 26, ease: 'linear' }}
          />

          {cardFaces.map((card, index) => (
            <motion.div
              key={card.label}
              className={`absolute h-36 w-24 rounded-xl border border-white/10 bg-gradient-to-br ${card.tone} shadow-2xl overflow-hidden`}
              initial={{ opacity: 0, y: 24, rotate: 0 }}
              animate={{
                opacity: 1,
                y: [0, -8, 0],
                rotate: [-12 + index * 12, -8 + index * 10, -12 + index * 12],
                x: (index - 1) * 44,
              }}
              transition={{
                opacity: { delay: 0.12 * index, duration: 0.35 },
                y: { repeat: Infinity, duration: 2.4, delay: index * 0.18, ease: 'easeInOut' },
                rotate: { repeat: Infinity, duration: 2.4, delay: index * 0.18, ease: 'easeInOut' },
              }}
            >
              <div className="absolute inset-x-3 top-3 h-1.5 rounded-full bg-white/15" />
              <div className="absolute inset-x-3 bottom-3 flex items-center justify-between">
                <span className="text-xs font-black text-white/70">{card.label}</span>
                <Sparkles size={14} className="text-white/50" />
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="h-14 w-14 rounded-xl border border-white/10 bg-black/20 flex items-center justify-center">
                  <Gem size={26} className="text-white" />
                </div>
              </div>
            </motion.div>
          ))}

          <motion.div
            className="absolute bottom-2 rounded-full border border-brand-accent/20 bg-brand-accent/10 px-3 py-1 text-xs font-semibold text-brand-accent"
            animate={{ opacity: [0.55, 1, 0.55] }}
            transition={{ repeat: Infinity, duration: 1.8, ease: 'easeInOut' }}
          >
            Seal Bot
          </motion.div>
        </div>

        <div className="text-center mb-7">
          <h1 className="text-2xl font-bold tracking-tight text-white mb-2">Opening your collection</h1>
          <p className="text-sm font-medium text-neutral-500">{currentStep}</p>
        </div>

        <div className="space-y-3">
          <div className="h-2 w-full rounded-full bg-brand-deep border border-white/5 overflow-hidden">
            <motion.div
              className="h-full rounded-full bg-brand-accent"
              animate={{ width: `${progress}%` }}
              transition={{ ease: 'easeOut', duration: 0.25 }}
            />
          </div>
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="text-neutral-500">Loading</span>
            <span className="text-brand-accent tabular-nums">{Math.floor(progress)}%</span>
          </div>
        </div>
      </div>
    </div>
  );
};
