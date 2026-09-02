import { Sparkles, Terminal } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { cn } from '../utils';

const loadingSteps = [
  'LOADING',
  'CONNECTING',
  'FETCHING PROFILE',
  'LOADING PETS',
  'ALMOST THERE',
];

export const IntroLoading = () => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) return 90;
        const step = Math.random() * 12 + 8;
        return Math.min(90, prev + step);
      });
    }, 150);

    return () => clearInterval(timer);
  }, []);

  const currentStep = useMemo(() => {
    const index = Math.min(
      loadingSteps.length - 1,
      Math.floor((progress / 100) * loadingSteps.length),
    );
    return loadingSteps[index];
  }, [progress]);

  return (
    <div className="fixed inset-0 z-[999] flex flex-col items-center justify-center bg-zinc-950 px-8 select-none">
      <div className="w-full max-w-xs space-y-16 relative z-10">
        {/* Visual Brand - Creative Minimalist Animation */}
        <div className="relative flex flex-col items-center justify-center gap-8">
          <div className="relative w-24 h-24 flex items-center justify-center">
            {/* Outer Ring */}
            <div className="absolute inset-0 rounded-full border border-dashed border-brand-accent/20 animate-[spin_4s_linear_infinite]" />

            {/* Middle Ring */}
            <div className="absolute inset-2 rounded-full border border-white/5 animate-[spin_8s_linear_infinite_reverse]" />

            {/* Core Brand Symbol */}
            <div className="relative w-12 h-12 bg-zinc-900 rounded-lg border border-white/10 flex items-center justify-center shadow-[0_0_20px_rgba(255,255,255,0.02)] animate-[intro-pulse_2s_ease-in-out_infinite]">
              <span className="text-xl font-black text-white tracking-tighter">S</span>
              <div className="absolute inset-0 rounded-lg bg-brand-accent/5 animate-[intro-pulse_2s_ease-in-out_infinite]" />
            </div>

            {/* Orbiting particles */}
            {[0, 120, 240].map((angle, i) => (
              <div
                key={i}
                className="absolute inset-0"
                style={{
                  transform: `rotate(${angle}deg)`,
                  animation: `spin ${3 + i}s linear infinite`,
                }}
              >
                <div
                  className="w-1 h-1 bg-brand-accent rounded-full absolute"
                  style={{
                    top: '0',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    opacity: progress > i * 30 ? 1 : 0.1,
                  }}
                />
              </div>
            ))}
          </div>

          <div className="flex flex-col items-center gap-1">
            <span className="text-2xl font-black text-white tracking-[0.2em] uppercase">SEAL</span>
            <span className="text-[8px] font-bold text-zinc-600 tracking-[0.4em] uppercase">
              Waifu Collector
            </span>
          </div>
        </div>

        {/* Progress & Stats */}
        <div className="space-y-6">
          <div className="space-y-3">
            <div className="flex justify-between items-end px-1">
              <div
                key={currentStep}
                className="flex items-center gap-2 animate-[intro-step_0.3s_ease-out]"
              >
                <Terminal size={10} className="text-brand-accent" />
                <span className="text-[9px] font-bold text-zinc-100 tracking-widest uppercase">
                  {currentStep}
                </span>
              </div>
              <span className="text-[10px] font-mono text-zinc-500 font-bold tabular-nums">
                {Math.round(progress)}%
              </span>
            </div>

            <div className="h-0.5 w-full bg-zinc-900 rounded-full overflow-hidden">
              <div
                className="h-full bg-white transition-[width] duration-300 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-1.5">
              <Sparkles size={8} className="text-zinc-600" />
              <span className="text-[7px] font-bold text-zinc-600 uppercase tracking-widest">
                Signed in via Telegram
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <div
                className={cn(
                  'w-1 h-1 rounded-full transition-colors duration-500',
                  progress === 100 ? 'bg-emerald-500' : 'bg-zinc-800',
                )}
              />
              <span className="text-[7px] font-mono text-zinc-600 uppercase tracking-widest">
                {progress === 100 ? 'READY' : 'SYNCING'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Decorative Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-20">
        <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_50%_50%,rgba(255,255,255,0.02)_0%,transparent_50%)]" />
      </div>
    </div>
  );
};
