import { useMemo, useState, type CSSProperties, type ElementType, type PointerEvent } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import {
  ArrowRight,
  BookOpen,
  Bot,
  Crown,
  Egg,
  Gem,
  PawPrint,
  Send,
  Sparkles,
  Star,
  Trophy,
  Zap,
  ShieldCheck,
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
  tone: string;
}

const sceneCards = [
  {
    id: 'mythic',
    badge: 'SSR',
    title: 'Mythic',
    meta: 'Level 100',
    className: 'left-[9%] top-[17%] hidden sm:block',
    rotate: -13,
    speed: -0.55,
    tone: 'from-brand-accent/30 via-brand-accent/10 to-brand-midnight',
  },
  {
    id: 'pet',
    badge: 'PET',
    title: 'Nova Lynx',
    meta: 'Luck Aura',
    className: 'right-[8%] top-[16%]',
    rotate: 11,
    speed: 0.48,
    tone: 'from-emerald-500/30 via-emerald-500/10 to-brand-midnight',
  },
  {
    id: 'egg',
    badge: 'EGG',
    title: 'Arc Egg',
    meta: '02:18:40',
    className: 'left-[14%] bottom-[12%]',
    rotate: 9,
    speed: 0.36,
    tone: 'from-amber-500/30 via-amber-500/10 to-brand-midnight',
  },
  {
    id: 'rank',
    badge: 'TOP',
    title: 'Rank 01',
    meta: 'Season 1',
    className: 'right-[17%] bottom-[10%] hidden md:block',
    rotate: -8,
    speed: -0.4,
    tone: 'from-purple-500/30 via-purple-500/10 to-brand-midnight',
  },
];

const featureCards: FeatureCardProps[] = [
  {
    icon: Sparkles,
    title: 'Archive Secured',
    description: 'A complete collection system with rarity reveals and live ownership checks.',
    tone: 'text-brand-accent border-brand-accent/20 bg-brand-accent/5',
  },
  {
    icon: Egg,
    title: 'Biological Sync',
    description: 'Incubate timed eggs and hatch unique characters to expand your roster.',
    tone: 'text-emerald-500 border-emerald-500/20 bg-emerald-500/5',
  },
  {
    icon: PawPrint,
    title: 'Tactical Pets',
    description: 'Deploy companion assets with specialized abilities and leveling paths.',
    tone: 'text-amber-500 border-amber-500/20 bg-amber-500/5',
  },
  {
    icon: Trophy,
    title: 'Global Ladder',
    description: 'Compete for dominance on global leaderboards and complete seasonal tasks.',
    tone: 'text-purple-500 border-purple-500/20 bg-purple-500/5',
  },
];

const metrics = [
  { label: 'Daily Market', value: 'ROTATING' },
  { label: 'Asset Archive', value: 'CATALOG' },
  { label: 'Companion', value: 'ACTIVE' },
  { label: 'Objectives', value: 'LIVE' },
];

const SceneCard = ({
  badge,
  title,
  meta,
  className,
  rotate,
  speed,
  tone,
  pointer,
  reduceMotion,
}: (typeof sceneCards)[number] & { pointer: ScenePointer; reduceMotion: boolean }) => {
  const wrapperStyle: CSSProperties = {
    transform: `translate3d(${pointer.x * speed}px, ${pointer.y * speed}px, 0)`,
  };

  return (
    <div className={`absolute z-10 ${className}`} style={wrapperStyle} aria-hidden="true">
      <motion.div
        className={`landing-holo-card h-40 w-28 overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br ${tone} p-4 shadow-2xl backdrop-blur-md sm:h-44 sm:w-32`}
        animate={reduceMotion ? undefined : { y: [0, -10, 0], rotate: [rotate, rotate + 2, rotate] }}
        transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
        style={reduceMotion ? { transform: `rotate(${rotate}deg)` } : undefined}
      >
        <div className="mb-10 flex items-center justify-between">
            <Badge variant="secondary" className="px-1.5 py-0 rounded-md font-black">{badge}</Badge>
            <ShieldCheck size={14} className="text-white/30" />
        </div>
        <div className="absolute inset-x-3 top-16 h-14 rounded-xl border border-white/5 bg-black/40" />
        <div className="absolute inset-x-3 bottom-3">
          <p className="text-xs font-black leading-tight text-white uppercase truncate">{title}</p>
          <p className="mt-1 text-[9px] font-bold uppercase text-neutral-500 tracking-widest">{meta}</p>
        </div>
      </motion.div>
    </div>
  );
};

const FeatureCard = ({ icon: Icon, title, description, tone }: FeatureCardProps) => (
  <Card className="p-6 border-white/5 bg-white/[0.02]">
    <div className={`mb-5 flex h-10 w-10 items-center justify-center rounded-xl border ${tone}`}>
      <Icon size={20} />
    </div>
    <h3 className="text-sm font-black text-white uppercase tracking-tight">{title}</h3>
    <p className="mt-3 text-xs font-bold leading-6 text-neutral-500 uppercase tracking-widest">{description}</p>
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
      x: ((event.clientX - rect.left) / rect.width - 0.5) * 50,
      y: ((event.clientY - rect.top) / rect.height - 0.5) * 50,
    });
  };

  const sceneStyle = {
    '--scene-x': `${pointer.x}px`,
    '--scene-y': `${pointer.y}px`,
  } as CSSProperties;

  return (
    <div className="landing-page h-svh min-h-svh overflow-x-hidden overflow-y-auto bg-background text-white select-none">
      <section
        className="landing-hero relative min-h-[85svh] overflow-hidden px-6 pb-12 pt-24 sm:px-10"
        onPointerMove={handlePointerMove}
        onPointerLeave={() => setPointer({ x: 0, y: 0 })}
        style={sceneStyle}
      >
        <div className="landing-grid pointer-events-none absolute inset-0" aria-hidden="true" />

        <div className="landing-stage pointer-events-none absolute inset-0 opacity-40 sm:opacity-100" aria-hidden="true">
          <motion.div
            className="absolute left-1/2 top-[46%] h-80 w-80 rounded-full border border-white/5"
            animate={reduceMotion ? undefined : { rotate: 360 }}
            transition={{ duration: 40, repeat: Infinity, ease: 'linear' }}
            style={{ x: '-50%', y: '-50%' }}
          />
          <div className="landing-runway absolute left-1/2 top-[46%] h-[36rem] w-[36rem] -translate-x-1/2 -translate-y-1/2 rounded-full opacity-40" />

          {sceneCards.map((card) => (
            <SceneCard key={card.id} {...card} pointer={pointer} reduceMotion={reduceMotion} />
          ))}

          <div className="absolute left-1/2 top-[47%] z-10 flex h-32 w-32 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-[2.5rem] border border-white/10 bg-brand-midnight/40 shadow-2xl backdrop-blur-2xl">
            <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center border border-white/10">
                <ShieldCheck size={32} className="text-white" strokeWidth={1} />
            </div>
          </div>
        </div>

        <header className="absolute left-0 right-0 top-0 z-30">
          <nav className="mx-auto flex h-20 w-full max-w-7xl items-center justify-between px-6 sm:px-10">
            <div className="flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/5 bg-white/5 shadow-inner">
                <ShieldCheck size={20} className="text-white" strokeWidth={2} />
              </div>
              <span className="text-xs font-black text-white tracking-tighter uppercase">SEAL YOUR WAIFU</span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.open(telegramUrl, '_blank')}
              className="rounded-xl border-white/5 bg-white/5 font-black uppercase text-[10px] tracking-widest h-10"
            >
              <Send size={14} className="mr-2" />
              Telegram
            </Button>
          </nav>
        </header>

        <div className="relative z-20 mx-auto flex max-w-7xl flex-col justify-center">
          <div className="w-full max-w-[24rem] pt-8 sm:max-w-3xl lg:pt-20 space-y-6 sm:space-y-8">
            <div className="inline-flex items-center gap-2 rounded-lg border border-brand-accent/20 bg-brand-accent/10 px-3 py-2 text-[10px] font-black uppercase tracking-[0.2em] text-brand-accent">
              <Zap size={14} />
              Operational Protocol Active
            </div>

            <h1 className="text-4xl font-black leading-[0.9] tracking-tighter text-white sm:text-7xl lg:text-8xl uppercase">
                Secure. <br />
                Archive. <br />
                Deploy.
            </h1>

            <p className="max-w-[22rem] text-sm font-bold leading-7 text-neutral-500 uppercase tracking-widest sm:max-w-xl sm:text-base">
              The definitive Telegram asset collection RPG. <br /> Secure rare cards, synchronize biological assets, and dominate the global leaderboards.
            </p>

            <div className="flex flex-col gap-3 sm:flex-row pt-4">
              <Button
                onClick={() => window.open(telegramUrl, '_blank')}
                className="h-14 px-10 rounded-2xl text-xs font-black uppercase tracking-[0.2em] shadow-[0_10px_40px_rgba(255,255,255,0.1)]"
              >
                Launch Protocol
              </Button>
              <Button
                variant="outline"
                className="h-14 px-8 rounded-2xl text-xs font-black uppercase tracking-[0.2em] border-white/5 bg-white/5"
                onClick={() => document.getElementById('drops')?.scrollIntoView({ behavior: 'smooth' })}
              >
                Archive Access
              </Button>
            </div>

            {error && (
              <div className="mt-8 p-5 rounded-2xl border border-red-500/20 bg-red-500/5 flex flex-col sm:flex-row items-center justify-between gap-4">
                <p className="text-[10px] font-black uppercase tracking-widest text-red-400">{error}</p>
                {onRetry && (
                  <Button
                    variant="outline"
                    size="xs"
                    onClick={onRetry}
                    className="border-red-500/30 text-red-400 font-black uppercase tracking-widest px-4 py-2"
                  >
                    Retry Connection
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="border-y border-white/5 bg-brand-deep">
        <div className="mx-auto grid max-w-7xl grid-cols-2 gap-px bg-white/5 sm:grid-cols-4">
          {metrics.map((metric) => (
            <div key={metric.label} className="bg-brand-deep px-6 py-8 sm:px-10">
              <p className="text-[9px] font-black uppercase tracking-[0.3em] text-neutral-600">{metric.label}</p>
              <p className="mt-3 text-xl font-black text-white tracking-widest">{metric.value}</p>
            </div>
          ))}
        </div>
      </section>

      <main id="drops" className="space-y-32 py-32">
        <section className="px-6 sm:px-10">
          <div className="mx-auto grid max-w-7xl gap-16 lg:grid-cols-[0.85fr_1.15fr] items-center">
            <div className="space-y-6">
              <div className="w-14 h-14 rounded-2xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center">
                <Gem size={28} className="text-brand-accent" />
              </div>
              <h2 className="text-3xl font-black leading-tight uppercase tracking-tighter sm:text-5xl">
                Advanced Tactical <br /> Collection.
              </h2>
              <p className="text-sm font-bold leading-8 text-neutral-500 uppercase tracking-widest max-w-lg">
                Engineered for speed and precision. Every interaction is optimized for high-frequency gameplay directly within Telegram.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {featureCards.map((feature) => (
                <FeatureCard key={feature.title} {...feature} />
              ))}
            </div>
          </div>
        </section>

        <section className="px-6 sm:px-10">
          <div className="mx-auto max-w-7xl flex flex-col items-center text-center space-y-16">
            <div className="space-y-4 max-w-2xl">
              <Badge variant="primary" className="rounded-full px-4 py-1 font-black tracking-widest text-[9px] uppercase">Asset Hierarchy</Badge>
              <h2 className="text-3xl font-black uppercase tracking-tighter sm:text-6xl">Rare Tier Archives</h2>
              <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest">Master the probability fields and secure high-value assets for your collection.</p>
            </div>

            <div className="w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {['SR', 'SSR', 'UR', 'EX'].map((rarity, i) => (
                    <Card key={rarity} className="p-6 bg-white/[0.02] border-white/5 space-y-6">
                        <div className="flex justify-between items-center">
                            <Badge variant={i === 3 ? 'purple' : i === 2 ? 'danger' : i === 1 ? 'warning' : 'primary'} className="font-black px-2 py-0.5 rounded-lg">{rarity}</Badge>
                            <ShieldCheck size={16} className="text-neutral-700" />
                        </div>
                        <div className="h-32 w-full rounded-2xl bg-black/40 border border-white/5 flex items-center justify-center">
                            <Gem size={32} className="text-neutral-800" />
                        </div>
                        <div className="space-y-3">
                            <div className="flex justify-between text-[10px] font-black uppercase tracking-widest text-neutral-600">
                                <span>SECURE RATE</span>
                                <span className="text-white">{(i + 1) * 20}%</span>
                            </div>
                            <div className="h-1.5 w-full bg-brand-surface rounded-full overflow-hidden">
                                <div className="h-full bg-brand-accent" style={{ width: `${(i + 1) * 20}%` }} />
                            </div>
                        </div>
                    </Card>
                ))}
            </div>
          </div>
        </section>

        <section className="px-6 sm:px-10">
          <Card className="mx-auto max-w-7xl p-10 sm:p-16 flex flex-col md:flex-row items-center justify-between gap-10 border-white/10 bg-gradient-to-br from-brand-deep to-brand-midnight shadow-2xl">
            <div className="space-y-4 text-center md:text-left">
              <h2 className="text-3xl font-black uppercase tracking-tighter sm:text-5xl">Ready to Initiate?</h2>
              <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest">Connect your Telegram account and start your collection protocol today.</p>
            </div>
            <Button
              onClick={() => window.open(telegramUrl, '_blank')}
              className="h-16 px-12 rounded-2xl text-sm font-black uppercase tracking-[0.2em] shadow-xl"
            >
              Initialize Sync
            </Button>
          </Card>
        </section>
      </main>

      <footer className="px-6 py-12 sm:px-10 border-t border-white/5 text-center">
        <p className="text-[10px] font-black text-neutral-600 uppercase tracking-widest">© 2025 SEAL YOUR WAIFU PROTOCOL. ALL RIGHTS RESERVED.</p>
      </footer>
    </div>
  );
};
