import { useMemo, useState, type CSSProperties, type ElementType, type PointerEvent } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { cn } from '../utils';
import {
  Egg,
  PawPrint,
  Send,
  Sparkles,
  Trophy,
  Zap,
  ShieldCheck,
  Heart,
  Target,
  Database,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';

interface LandingProps {
  error?: string | null;
  onRetry?: () => void;
}

interface ScenePointer {
  x: number;
  y: number;
}

interface FeatureCardProps {
  icon: ElementType;
  title: string;
  description: string;
  variant: 'primary' | 'success' | 'warning' | 'epic';
}

const sceneCards = [
  {
    id: 'mythic',
    badge: 'CLASS SSR',
    title: 'VALKYRIE 01',
    meta: 'SYNC LVL 100',
    className: 'left-[10%] top-[18%] hidden sm:block',
    rotate: -12,
    speed: -0.45,
    variant: 'primary',
  },
  {
    id: 'pet',
    badge: 'UNIT COMP',
    title: 'NOVA LYNX',
    meta: 'LUCK AURA ON',
    className: 'right-[8%] top-[15%]',
    rotate: 10,
    speed: 0.5,
    variant: 'success',
  },
  {
    id: 'egg',
    badge: 'BIO CONT',
    title: 'ARC EGG X',
    meta: 'READY',
    className: 'left-[15%] bottom-[15%]',
    rotate: 8,
    speed: 0.35,
    variant: 'warning',
  },
  {
    id: 'rank',
    badge: 'TOP ELITE',
    title: 'RANK ALPHA',
    meta: 'SEASON 01',
    className: 'right-[18%] bottom-[12%] hidden md:block',
    rotate: -9,
    speed: -0.38,
    variant: 'epic',
  },
];

const featureCards: FeatureCardProps[] = [
  {
    icon: Sparkles,
    title: 'Personnel Summoning',
    description: 'Advanced recruitment system with instant asset verification and ownership.',
    variant: 'primary',
  },
  {
    icon: Egg,
    title: 'Biological Sync',
    description: 'Incubate secure biological containers to unlock classified personnel records.',
    variant: 'success',
  },
  {
    icon: PawPrint,
    title: 'Support Units',
    description: 'Deploy companions with specialized perks and strategic evolution paths.',
    variant: 'warning',
  },
  {
    icon: Trophy,
    title: 'Global Rankings',
    description: 'Compete for network dominance on global leaderboards and seasonal tracks.',
    variant: 'epic',
  },
];

const SceneCard = ({
  badge,
  title,
  meta,
  className,
  rotate,
  speed,
  variant,
  pointer,
  reduceMotion,
}: (typeof sceneCards)[number] & { pointer: ScenePointer; reduceMotion: boolean }) => {
  const wrapperStyle: CSSProperties = {
    transform: `translate3d(${pointer.x * speed}px, ${pointer.y * speed}px, 0)`,
  };

  return (
    <div className={`absolute z-10 ${className}`} style={wrapperStyle} aria-hidden="true">
      <motion.div
        className={cn(
            "h-40 w-28 rounded-xl border p-4 shadow-2xl backdrop-blur-md relative",
            variant === 'primary' && "bg-brand-accent/10 border-brand-accent/20",
            variant === 'success' && "bg-emerald-500/10 border-emerald-500/20",
            variant === 'warning' && "bg-amber-500/10 border-amber-500/20",
            variant === 'epic' && "bg-purple-500/10 border-purple-500/20"
        )}
        {...(reduceMotion ? {} : { animate: { y: [0, -8, 0], rotate: [rotate, rotate + 1, rotate] } })}
        transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
        {...(reduceMotion ? { style: { transform: `rotate(${rotate}deg)` } } : {})}
      >
        <div className="mb-8 flex items-center justify-between">
            <div className="w-5 h-5 rounded bg-white/5 border border-white/10 flex items-center justify-center">
               <ShieldCheck size={10} className="opacity-40" />
            </div>
        </div>
        <div className="space-y-3">
            <div className="h-1 w-6 bg-white/10 rounded-full" />
            <div className="space-y-1">
                <p className="text-[9px] font-bold leading-none text-white uppercase truncate">{title}</p>
                <p className="text-[7px] font-bold uppercase text-zinc-500 tracking-widest">{badge}</p>
            </div>
        </div>
        <div className="absolute bottom-4 inset-x-4">
           <p className="text-[7px] font-mono font-bold text-white/30 uppercase">{meta}</p>
        </div>
      </motion.div>
    </div>
  );
};

const FeatureCard = ({ icon: Icon, title, description, variant }: FeatureCardProps) => (
  <Card variant="default" className="p-6 transition-all group">
    <div className={cn(
        "mb-4 flex h-10 w-10 items-center justify-center rounded-md border transition-transform group-hover:scale-105",
        variant === 'primary' && "text-brand-accent border-brand-accent/20 bg-brand-accent/5",
        variant === 'success' && "text-emerald-500 border-emerald-500/20 bg-emerald-500/5",
        variant === 'warning' && "text-amber-500 border-amber-500/20 bg-amber-500/5",
        variant === 'epic' && "text-purple-500 border-purple-500/20 bg-purple-500/5"
    )}>
      <Icon size={20} />
    </div>
    <h3 className="text-sm font-bold text-zinc-100 uppercase tracking-tight mb-2">{title}</h3>
    <p className="text-[11px] font-medium text-zinc-500 uppercase tracking-widest leading-relaxed">{description}</p>
  </Card>
);

export const Landing = ({ error, onRetry }: LandingProps) => {
  const reduceMotion = Boolean(useReducedMotion());
  const [pointer, setPointer] = useState<ScenePointer>({ x: 0, y: 0 });

  const botUsername = useMemo(
    () => (import.meta.env.VITE_BOT_USERNAME || 'SealYourWaifuBot').replace(/^@/, ''),
    [],
  );
  const telegramUrl = `https://t.me/${botUsername}`;

  const handlePointerMove = (event: PointerEvent<HTMLElement>) => {
    if (reduceMotion) return;
    const rect = event.currentTarget.getBoundingClientRect();
    setPointer({
      x: ((event.clientX - rect.left) / rect.width - 0.5) * 40,
      y: ((event.clientY - rect.top) / rect.height - 0.5) * 40,
    });
  };

  return (
    <div className="h-svh min-h-svh overflow-x-hidden overflow-y-auto bg-zinc-950 text-white select-none">
      <section
        className="relative min-h-svh overflow-hidden px-8 pb-16 pt-28 sm:px-12"
        onPointerMove={handlePointerMove}
        onPointerLeave={() => setPointer({ x: 0, y: 0 })}
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.03),transparent_70%)] pointer-events-none" />

        <div className="pointer-events-none absolute inset-0" aria-hidden="true">
          {sceneCards.map((card) => (
            <SceneCard key={card.id} {...card} pointer={pointer} reduceMotion={reduceMotion} />
          ))}

          <div className="absolute left-1/2 top-[45%] z-10 flex h-32 w-32 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-3xl border border-white/5 bg-zinc-950/40 backdrop-blur-xl shadow-2xl">
             <Heart size={48} className="text-white opacity-80" strokeWidth={1} fill="currentColor" />
          </div>
        </div>

        <header className="absolute left-0 right-0 top-0 z-40">
          <nav className="mx-auto flex h-20 w-full max-w-7xl items-center justify-between px-8 sm:px-12">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-md border border-white/10 bg-zinc-900 shadow-xl">
                <Heart size={18} className="text-white" fill="currentColor" />
              </div>
              <div className="flex flex-col">
                 <span className="text-[10px] font-bold text-white tracking-widest uppercase leading-none">SEAL</span>
                 <span className="text-[8px] font-mono text-zinc-600 uppercase mt-0.5">V2.4</span>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.open(telegramUrl, '_blank')}
              className="h-9 px-4 rounded-md text-[10px]"
            >
              Nexus
            </Button>
          </nav>
        </header>

        <div className="relative z-30 mx-auto flex max-w-7xl flex-col justify-center h-full min-h-[60svh]">
          <div className="w-full max-w-2xl space-y-8">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-accent/10 border border-brand-accent/20 text-[9px] font-bold uppercase tracking-widest text-brand-accent">
              <Zap size={12} className="animate-pulse" />
              Network Online
            </div>

            <h1 className="text-5xl font-bold leading-tight tracking-tight text-zinc-100 sm:text-7xl uppercase">
                Summon.<br />
                Archive.<br />
                Dominate.
            </h1>

            <p className="max-w-md text-xs font-medium leading-relaxed text-zinc-500 uppercase tracking-widest sm:text-sm">
              The definitive Telegram character management system. Secure units, expand your archive, and compete for network dominance.
            </p>

            <div className="flex flex-col gap-3 sm:flex-row pt-4">
              <Button
                onClick={() => window.open(telegramUrl, '_blank')}
                className="h-14 px-10 rounded-md text-[11px] font-bold uppercase tracking-widest"
                variant="accent"
              >
                Initialize Sync
              </Button>
              <Button
                variant="secondary"
                className="h-14 px-8 rounded-md text-[11px] font-bold uppercase tracking-widest"
                onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
              >
                Access Logs
              </Button>
            </div>

            {error && (
              <div className="mt-8 p-4 rounded-md border border-red-500/20 bg-red-500/5 flex flex-col sm:flex-row items-center justify-between gap-4">
                <p className="text-[10px] font-bold uppercase tracking-widest text-red-500/80">{error}</p>
                {onRetry && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={onRetry}
                    className="border-red-500/30 text-red-500 h-8 px-4 text-[9px]"
                  >
                    Retry
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>
      </section>

      <main id="features" className="space-y-32 py-32">
        <section className="px-8 sm:px-12">
          <div className="mx-auto grid max-w-7xl gap-16 lg:grid-cols-2 items-center">
            <div className="space-y-6">
              <div className="space-y-4">
                 <h2 className="text-4xl font-bold uppercase tracking-tight sm:text-5xl">
                   Tactical<br />Summoning.
                 </h2>
                 <p className="text-xs font-medium leading-relaxed text-zinc-500 uppercase tracking-widest max-w-sm">
                   Engineered for elite collectors. Every interaction is optimized for high-frequency unit summoning within the Telegram ecosystem.
                 </p>
              </div>
              <div className="flex gap-2">
                 <div className="h-1 w-10 bg-brand-accent rounded-full" />
                 <div className="h-1 w-2 bg-zinc-800 rounded-full" />
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {featureCards.map((feature) => (
                <FeatureCard key={feature.title} {...feature} />
              ))}
            </div>
          </div>
        </section>

        <section className="px-8 sm:px-12">
          <div className="mx-auto max-w-7xl text-center space-y-16">
            <div className="space-y-4">
              <Badge variant="primary" className="px-4 py-1">Hierarchy</Badge>
              <h2 className="text-4xl font-bold uppercase tracking-tight sm:text-6xl">Unit Classes</h2>
              <p className="text-xs font-medium text-zinc-500 uppercase tracking-widest">Master the probability fields and secure high-value characters.</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                    { label: 'Class SR', variant: 'primary', rate: 40 },
                    { label: 'Class SSR', variant: 'warning', rate: 25 },
                    { label: 'Class UR', variant: 'danger', rate: 10 },
                    { label: 'Class EX', variant: 'epic', rate: 5 },
                ].map((tier, i) => (
                    <Card key={i} variant="default" className="p-8 space-y-6">
                        <Badge variant={tier.variant as any} className="px-3 py-1 font-bold">{tier.label}</Badge>
                        <div className="h-32 flex items-center justify-center">
                           <Heart size={40} className="text-zinc-900" fill="currentColor" />
                        </div>
                        <div className="space-y-2">
                            <div className="flex justify-between text-[9px] font-bold uppercase text-zinc-600">
                                <span>Summon Rate</span>
                                <span className="text-zinc-400">{tier.rate}%</span>
                            </div>
                            <div className="h-1 w-full bg-zinc-900 rounded-full overflow-hidden">
                                <motion.div
                                    initial={{ width: 0 }}
                                    whileInView={{ width: `${tier.rate}%` }}
                                    transition={{ duration: 1, delay: i * 0.1 }}
                                    className={cn(
                                        "h-full rounded-full",
                                        tier.variant === 'primary' && "bg-brand-accent",
                                        tier.variant === 'warning' && "bg-amber-500",
                                        tier.variant === 'danger' && "bg-red-500",
                                        tier.variant === 'epic' && "bg-purple-500"
                                    )}
                                />
                            </div>
                        </div>
                    </Card>
                ))}
            </div>
          </div>
        </section>

        <section className="px-8 sm:px-12">
          <Card variant="surface" className="mx-auto max-w-5xl p-12 sm:p-20 flex flex-col md:flex-row items-center justify-between gap-12 text-center md:text-left">
            <div className="space-y-4">
              <h2 className="text-4xl font-bold uppercase tracking-tight sm:text-6xl">Ready?</h2>
              <p className="text-xs font-medium text-zinc-500 uppercase tracking-widest max-w-sm">
                 Connect your Telegram ID and initialize the summoning nexus immediately.
              </p>
            </div>

            <Button
                onClick={() => window.open(telegramUrl, '_blank')}
                className="h-16 px-12 rounded-md text-xs font-bold uppercase tracking-widest"
                variant="accent"
                leftIcon={<Database size={18} />}
            >
                Initialize Sync
            </Button>
          </Card>
        </section>
      </main>

      <footer className="px-8 py-12 border-t border-white/5 bg-zinc-950 text-center">
        <div className="flex flex-col items-center gap-4">
           <Heart size={16} className="text-zinc-800" fill="currentColor" />
           <p className="text-[10px] font-bold text-zinc-700 uppercase tracking-widest">© 2025 SEAL. ALL RIGHTS RESERVED.</p>
        </div>
      </footer>
    </div>
  );
};
