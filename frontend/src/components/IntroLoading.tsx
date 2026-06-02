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
  { letter: 'S', tone: 'from-sky-500/65 to-zinc-900', x: -78, rotate: -13 },
  { letter: 'E', tone: 'from-cyan-500/60 to-zinc-900', x: -26, rotate: -4 },
  { letter: 'A', tone: 'from-violet-500/60 to-zinc-900', x: 26, rotate: 4 },
  { letter: 'L', tone: 'from-fuchsia-500/60 to-zinc-900', x: 78, rotate: 13 },
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

  const completedCards = Math.min(4, Math.max(1, Math.ceil(progress / 25)));
  const isReady = progress >= 99;

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

          {cardFaces.map((card, index) => {
            const cardProgress = Math.min(1, Math.max(0, (progress - index * 25) / 25));
            const unlocked = cardProgress > 0;
            const complete = cardProgress >= 1;
            const finalX = [-72, -24, 24, 72][index];

            return (
              <motion.div
                key={card.letter}
                className={`absolute h-36 w-20 rounded-xl border bg-gradient-to-br ${card.tone} overflow-hidden`}
                initial={{ opacity: 0, y: 24, rotate: 0 }}
                animate={{
                  opacity: unlocked ? 1 : 0.34,
                  y: unlocked ? [0, index % 2 === 0 ? -8 : -5, 0] : 10,
                  rotate: isReady ? 0 : [card.rotate, card.rotate * 0.65, card.rotate],
                  x: isReady ? finalX : card.x,
                  scale: 0.95 + cardProgress * 0.07,
                  filter: unlocked
                    ? `saturate(${0.65 + cardProgress * 0.55}) brightness(${0.82 + cardProgress * 0.22})`
                    : 'saturate(0.15) brightness(0.55)',
                  borderColor: complete ? 'rgba(59, 130, 246, 0.45)' : 'rgba(255, 255, 255, 0.10)',
                  boxShadow: complete
                    ? '0 22px 50px rgba(59, 130, 246, 0.24)'
                    : unlocked
                      ? '0 18px 40px rgba(0, 0, 0, 0.42)'
                      : '0 10px 24px rgba(0, 0, 0, 0.28)',
                }}
                transition={{
                  opacity: { delay: 0.1 * index, duration: 0.35 },
                  scale: { duration: 0.28, ease: 'easeOut' },
                  filter: { duration: 0.28, ease: 'easeOut' },
                  borderColor: { duration: 0.28, ease: 'easeOut' },
                  boxShadow: { duration: 0.28, ease: 'easeOut' },
                  y: unlocked
                    ? { repeat: Infinity, duration: 2.4, delay: index * 0.18, ease: 'easeInOut' }
                    : { duration: 0.28, ease: 'easeOut' },
                  rotate: isReady
                    ? { duration: 0.45, ease: 'easeOut' }
                    : { repeat: Infinity, duration: 2.4, delay: index * 0.18, ease: 'easeInOut' },
                  x: { duration: 0.45, ease: 'easeOut' },
                }}
              >
                <div className="absolute inset-x-3 top-3 h-1.5 rounded-full bg-white/15" />
                <div className="absolute inset-x-3 bottom-3 flex items-center justify-between">
                  <span className="text-[10px] font-black text-white/70">{complete ? 'DONE' : 'SEAL'}</span>
                  <Sparkles size={14} className={complete ? 'text-brand-accent' : 'text-white/40'} />
                </div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="h-16 w-14 rounded-xl border border-white/10 bg-black/20 flex flex-col items-center justify-center gap-1">
                    <Gem size={18} className={complete ? 'text-brand-accent' : 'text-white/70'} />
                    <span className="text-3xl font-black tracking-tight text-white">{card.letter}</span>
                  </div>
                </div>
              </motion.div>
            );
          })}

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

        <div className="flex items-center justify-center gap-2">
          {cardFaces.map((card, index) => {
            const active = index < completedCards;
            return (
              <div
                key={`step-${card.letter}`}
                className={`h-2.5 w-2.5 rounded-full transition-colors ${
                  active ? 'bg-brand-accent' : 'bg-brand-deep border border-white/10'
                }`}
                aria-label={`${card.letter} ${active ? 'loaded' : 'waiting'}`}
              />
            );
          })}
          <span className="ml-2 text-xs font-semibold text-neutral-500">{completedCards}/4 cards ready</span>
        </div>
      </div>
    </div>
  );
};
