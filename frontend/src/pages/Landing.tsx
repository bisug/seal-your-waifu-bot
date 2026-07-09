import { useMemo, useState, type CSSProperties, type ElementType, type PointerEvent } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { cn } from '../utils';
import {
  ArrowRight,
  Egg,
  Gem,
  PawPrint,
  Send,
  Sparkles,
  Trophy,
  Zap,
  ShieldCheck,
  Heart,
  Target,
  Database,
  Terminal,
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
    badge: 'CLASS_SSR',
    title: 'VALKYRIE_01',
    meta: 'SYNC_LVL_100',
    className: 'left-[10%] top-[18%] hidden sm:block',
    rotate: -12,
    speed: -0.45,
    variant: 'primary',
  },
  {
    id: 'pet',
    badge: 'UNIT_COMP',
    title: 'NOVA_LYNX',
    meta: 'LUCK_AURA_ON',
    className: 'right-[8%] top-[15%]',
    rotate: 10,
    speed: 0.5,
    variant: 'success',
  },
  {
    id: 'egg',
    badge: 'BIO_CONT',
    title: 'ARC_EGG_X',
    meta: 'ETA: 02:18:40',
    className: 'left-[15%] bottom-[15%]',
    rotate: 8,
    speed: 0.35,
    variant: 'warning',
  },
  {
    id: 'rank',
    badge: 'TOP_ELITE',
    title: 'RANK_ALPHA',
    meta: 'SEASON_01_LOG',
    className: 'right-[18%] bottom-[12%] hidden md:block',
    rotate: -9,
    speed: -0.38,
    variant: 'epic',
  },
];

const featureCards: FeatureCardProps[] = [
  {
    icon: Sparkles,
    title: 'ASSET SUMMONING',
    description: 'High-fidelity collection system with real-time biometric ownership verification.',
    variant: 'primary',
  },
  {
    icon: Egg,
    title: 'BIOLOGICAL SYNC',
    description: 'Incubate secure biological containers to unlock classified personnel records.',
    variant: 'success',
  },
  {
    icon: PawPrint,
    title: 'SUPPORT UNITS',
    description: 'Deploy support companions with specialized combat perks and evolution paths.',
    variant: 'warning',
  },
  {
    icon: Trophy,
    title: 'GLOBAL LADDER',
    description: 'Compete for network dominance on tactical leaderboards and seasonal tracks.',
    variant: 'epic',
  },
];

const metrics = [
  { label: 'GACHA_MARKET', value: 'ROTATING' },
  { label: 'ASSET_ARCHIVE', value: 'CATALOG' },
  { label: 'SUPPORT_UNITS', value: 'DEPLOYED' },
  { label: 'OBJECTIVES', value: 'ACTIVE' },
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
            "h-44 w-32 overflow-hidden rounded-[24px] border p-5 shadow-2xl backdrop-blur-xl relative group",
            variant === 'primary' && "bg-brand-accent/10 border-brand-accent/20",
            variant === 'success' && "bg-success/10 border-success/20",
            variant === 'warning' && "bg-warning/10 border-warning/20",
            variant === 'epic' && "bg-epic/10 border-epic/20"
        )}
        animate={reduceMotion ? undefined : { y: [0, -12, 0], rotate: [rotate, rotate + 2, rotate] }}
        transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
        style={reduceMotion ? { transform: `rotate(${rotate}deg)` } : undefined}
      >
        <div className="absolute inset-0 bg-scanline opacity-[0.05] pointer-events-none" />
        <div className="mb-10 flex items-center justify-between">
            <div className="w-6 h-6 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
               <ShieldCheck size={12} className="opacity-40" />
            </div>
            <div className="h-1 w-1 rounded-full bg-white/20 animate-pulse" />
        </div>
        <div className="space-y-4">
            <div className="h-1 w-8 bg-white/10 rounded-full" />
            <div className="space-y-1.5">
                <p className="text-[10px] font-black leading-none text-white uppercase truncate tracking-tight">{title}</p>
                <p className="text-[7px] font-black uppercase text-neutral-500 tracking-[0.2em]">{badge}</p>
            </div>
        </div>
        <div className="absolute bottom-5 inset-x-5">
           <p className="text-[8px] font-mono font-bold text-white/40 uppercase tracking-tighter">{meta}</p>
        </div>
      </motion.div>
    </div>
  );
};

const FeatureCard = ({ icon: Icon, title, description, variant }: FeatureCardProps) => (
  <Card variant="tactical" className="p-8 border-white/[0.04] bg-white/[0.01] hover:border-white/[0.08] transition-all duration-500 group">
    <div className={cn(
        "mb-6 flex h-12 w-12 items-center justify-center rounded-2xl border transition-all duration-500 group-hover:scale-110 shadow-lg",
        variant === 'primary' && "text-brand-accent border-brand-accent/20 bg-brand-accent/5",
        variant === 'success' && "text-success border-success/20 bg-success/5",
        variant === 'warning' && "text-warning border-warning/20 bg-warning/5",
        variant === 'epic' && "text-epic border-epic/20 bg-epic/5"
    )}>
      <Icon size={24} />
    </div>
    <h3 className="text-[13px] font-black text-white uppercase tracking-[0.2em] mb-3">{title}</h3>
    <p className="text-[11px] font-bold leading-relaxed text-neutral-500 uppercase tracking-widest">{description}</p>
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
      x: ((event.clientX - rect.left) / rect.width - 0.5) * 60,
      y: ((event.clientY - rect.top) / rect.height - 0.5) * 60,
    });
  };

  const sceneStyle = {
    '--scene-x': `${pointer.x}px`,
    '--scene-y': `${pointer.y}px`,
  } as CSSProperties;

  return (
    <div className="h-svh min-h-svh overflow-x-hidden overflow-y-auto bg-brand-midnight text-white select-none tactical-noise">
      <section
        className="relative min-h-[95svh] overflow-hidden px-8 pb-16 pt-28 sm:px-12"
        onPointerMove={handlePointerMove}
        onPointerLeave={() => setPointer({ x: 0, y: 0 })}
        style={sceneStyle}
      >
        <div className="tactical-grid pointer-events-none absolute inset-0 opacity-20" aria-hidden="true" />

        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.05),transparent_70%)] pointer-events-none" />

        <div className="pointer-events-none absolute inset-0 opacity-60 sm:opacity-100" aria-hidden="true">
          <motion.div
            className="absolute left-1/2 top-[48%] h-[32rem] w-[32rem] rounded-full border border-white/[0.02]"
            animate={reduceMotion ? undefined : { rotate: 360 }}
            transition={{ duration: 60, repeat: Infinity, ease: 'linear' }}
            style={{ x: '-50%', y: '-50%' }}
          />
          <div className="absolute left-1/2 top-[48%] h-[42rem] w-[42rem] -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/[0.01] opacity-50" />

          {sceneCards.map((card) => (
            <SceneCard key={card.id} {...card} pointer={pointer} reduceMotion={reduceMotion} />
          ))}

          <div className="absolute left-1/2 top-[48%] z-10 flex h-40 w-40 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-[3rem] border border-white/[0.08] bg-brand-midnight/40 shadow-2xl backdrop-blur-3xl group">
             <div className="absolute inset-0 bg-brand-accent/5 rounded-[3rem] blur-2xl group-hover:bg-brand-accent/10 transition-colors" />
             <div className="w-20 h-20 rounded-[1.5rem] bg-white/[0.03] flex items-center justify-center border border-white/[0.08] relative z-10 shadow-inner">
                <Heart size={40} className="text-white transition-transform duration-700 group-hover:scale-110" strokeWidth={1} fill="currentColor" />
             </div>
          </div>
        </div>

        <header className="absolute left-0 right-0 top-0 z-40">
          <nav className="mx-auto flex h-24 w-full max-w-7xl items-center justify-between px-8 sm:px-12">
            <div className="flex items-center gap-4">
              <div className="flex h-11 w-11 items-center justify-center rounded-[14px] border border-white/[0.08] bg-white/[0.02] shadow-xl">
                <Heart size={20} className="text-white" strokeWidth={2.5} fill="currentColor" />
              </div>
              <div className="flex flex-col gap-0.5">
                 <span className="text-[11px] font-black text-white tracking-[0.3em] uppercase leading-none">PROTOCOL</span>
                 <span className="text-[8px] font-black text-neutral-600 uppercase tracking-widest leading-none">v2.4_STABLE</span>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.open(telegramUrl, '_blank')}
              className="rounded-[14px] border-white/[0.08] bg-white/[0.02] font-black uppercase text-[10px] tracking-widest h-11 px-6 hover:bg-white/5 active:scale-95"
            >
              <Send size={14} className="mr-2" />
              TERMINAL
            </Button>
          </nav>
        </header>

        <div className="relative z-30 mx-auto flex max-w-7xl flex-col justify-center h-full min-h-[70svh]">
          <div className="w-full max-w-[28rem] sm:max-w-3xl space-y-10">
            <div className="inline-flex items-center gap-3 rounded-xl border border-brand-accent/30 bg-brand-accent/10 px-4 py-2 text-[10px] font-black uppercase tracking-[0.3em] text-brand-accent shadow-[0_0_20px_rgba(59,130,246,0.2)] animate-in">
              <Zap size={14} className="animate-pulse" />
              SYNC_STATUS: ONLINE
            </div>

            <div className="space-y-4">
                <h1 className="text-5xl font-black leading-[0.85] tracking-tighter text-white sm:text-8xl lg:text-9xl uppercase drop-shadow-2xl">
                    SUMMON.<br />
                    ARCHIVE.<br />
                    DOMINATE.
                </h1>
                <div className="h-1.5 w-24 bg-brand-accent rounded-full shadow-[0_0_15px_rgba(59,130,246,0.5)]" />
            </div>

            <p className="max-w-[24rem] text-[13px] font-bold leading-relaxed text-neutral-500 uppercase tracking-[0.15em] sm:max-w-xl sm:text-base opacity-80">
              THE DEFINITIVE TELEGRAM GACHA OPERATING SYSTEM. <br /> SECURE RARE ASSETS, EXPAND YOUR HAREM, AND COMPETE FOR NETWORK DOMINANCE.
            </p>

            <div className="flex flex-col gap-4 sm:flex-row pt-6">
              <Button
                onClick={() => {
                    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
                    window.open(telegramUrl, '_blank');
                }}
                className="h-16 px-12 rounded-[22px] text-xs font-black uppercase tracking-[0.3em] shadow-[0_20px_50px_rgba(255,255,255,0.15)] active:scale-95"
              >
                INITIALIZE SYNC
              </Button>
              <Button
                variant="secondary"
                className="h-16 px-10 rounded-[22px] text-xs font-black uppercase tracking-[0.3em] border-white/[0.08] bg-white/[0.02] active:scale-95"
                onClick={() => {
                    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
                    document.getElementById('drops')?.scrollIntoView({ behavior: 'smooth' });
                }}
              >
                ACCESS LOGS
              </Button>
            </div>

            {error && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-12 p-6 rounded-[24px] border border-danger/20 bg-danger/[0.03] flex flex-col sm:flex-row items-center justify-between gap-6 backdrop-blur-xl">
                <div className="flex items-center gap-4">
                   <div className="w-10 h-10 rounded-xl bg-danger/10 flex items-center justify-center text-danger border border-danger/20">
                      <Target size={20} />
                   </div>
                   <p className="text-[11px] font-black uppercase tracking-widest text-danger/80">{error}</p>
                </div>
                {onRetry && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={onRetry}
                    className="border-danger/30 text-danger font-black uppercase tracking-[0.2em] px-6 h-10 rounded-xl hover:bg-danger/5"
                  >
                    RE-SYNC
                  </Button>
                )}
              </motion.div>
            )}
          </div>
        </div>
      </section>

      <section className="border-y border-white/[0.04] bg-white/[0.01] backdrop-blur-md">
        <div className="mx-auto grid max-w-7xl grid-cols-2 gap-px bg-white/[0.04] sm:grid-cols-4">
          {metrics.map((metric) => (
            <div key={metric.label} className="bg-brand-midnight px-8 py-10 sm:px-12 group hover:bg-white/[0.01] transition-colors">
              <p className="text-[10px] font-black uppercase tracking-[0.4em] text-neutral-700 group-hover:text-brand-accent transition-colors mb-4">{metric.label}</p>
              <div className="flex items-center gap-3">
                 <div className="h-1.5 w-1.5 rounded-full bg-brand-accent animate-pulse shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
                 <p className="text-xl font-black text-white tracking-[0.1em] font-mono">{metric.value}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <main id="drops" className="space-y-40 py-40">
        <section className="px-8 sm:px-12">
          <div className="mx-auto grid max-w-7xl gap-20 lg:grid-cols-[0.9fr_1.1fr] items-center">
            <div className="space-y-8">
              <div className="w-16 h-16 rounded-[20px] bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center shadow-[0_0_20px_rgba(59,130,246,0.15)]">
                <Terminal size={32} className="text-brand-accent" />
              </div>
              <div className="space-y-4">
                 <h2 className="text-4xl font-black leading-[0.9] uppercase tracking-tighter sm:text-6xl">
                   TACTICAL<br />
                   GACHA_OS.
                 </h2>
                 <p className="text-[13px] font-bold leading-relaxed text-neutral-500 uppercase tracking-[0.2em] max-w-lg opacity-80">
                   ENGINEERED FOR ELITE COLLECTORS. EVERY INTERACTION IS OPTIMIZED FOR HIGH-FREQUENCY ASSET EXTRACTION DIRECTLY WITHIN THE TELEGRAM ECOSYSTEM.
                 </p>
              </div>
              <div className="flex gap-4">
                 <div className="h-px w-12 bg-brand-accent" />
                 <div className="h-px w-4 bg-neutral-800" />
                 <div className="h-px w-4 bg-neutral-800" />
              </div>
            </div>

            <div className="grid gap-5 sm:grid-cols-2">
              {featureCards.map((feature) => (
                <FeatureCard key={feature.title} {...feature} />
              ))}
            </div>
          </div>
        </section>

        <section className="px-8 sm:px-12">
          <div className="mx-auto max-w-7xl flex flex-col items-center text-center space-y-20">
            <div className="space-y-6 max-w-2xl">
              <Badge variant="primary" className="rounded-xl px-5 py-1.5 font-black tracking-[0.3em] text-[10px] uppercase border-brand-accent/30 bg-brand-accent/10 shadow-lg">HAREM_HIERARCHY</Badge>
              <h2 className="text-4xl font-black uppercase tracking-tighter sm:text-7xl drop-shadow-xl">ASSET_CLASSES</h2>
              <p className="text-[13px] font-bold text-neutral-500 uppercase tracking-[0.2em] opacity-80">MASTER THE PROBABILITY FIELDS AND SECURE HIGH-VALUE PERSONNEL FOR YOUR ARCHIVE.</p>
            </div>

            <div className="w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {[
                    { label: 'CLASS_SR', variant: 'primary', rate: 40, icon: ShieldCheck },
                    { label: 'CLASS_SSR', variant: 'warning', rate: 25, icon: Target },
                    { label: 'CLASS_UR', variant: 'danger', rate: 10, icon: Zap },
                    { label: 'CLASS_EX', variant: 'epic', rate: 5, icon: Sparkles },
                ].map((tier, i) => (
                    <Card key={i} variant="tactical" className="p-8 border-white/[0.04] bg-white/[0.01] space-y-8 group hover:border-white/[0.1] transition-all duration-700">
                        <div className="flex justify-between items-center">
                            <Badge variant={tier.variant as any} className="font-black px-3 py-1 rounded-md shadow-sm border-none tracking-widest text-[9px]">{tier.label}</Badge>
                            <tier.icon size={18} className="text-neutral-800 group-hover:text-white/20 transition-colors" />
                        </div>
                        <div className="h-40 w-full rounded-[24px] bg-black/40 border border-white/[0.03] flex items-center justify-center relative overflow-hidden group-hover:border-white/10 transition-colors">
                            <div className="absolute inset-0 bg-scanline opacity-[0.03]" />
                            <Heart size={44} className="text-neutral-900 drop-shadow-inner group-hover:scale-110 transition-transform duration-700" fill="currentColor" />
                        </div>
                        <div className="space-y-4">
                            <div className="flex justify-between text-[9px] font-black uppercase tracking-[0.3em] text-neutral-600">
                                <span>SUMMON_RATE</span>
                                <span className="text-white font-mono">{tier.rate}%</span>
                            </div>
                            <div className="h-1.5 w-full bg-white/[0.02] rounded-full overflow-hidden p-[1px] border border-white/[0.02]">
                                <motion.div
                                    initial={{ width: 0 }}
                                    whileInView={{ width: `${tier.rate}%` }}
                                    transition={{ duration: 1.5, delay: i * 0.1 }}
                                    className={cn(
                                        "h-full rounded-full shadow-[0_0_10px_rgba(0,0,0,0.5)]",
                                        tier.variant === 'primary' && "bg-brand-accent",
                                        tier.variant === 'warning' && "bg-warning",
                                        tier.variant === 'danger' && "bg-danger",
                                        tier.variant === 'epic' && "bg-epic"
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
          <Card variant="tactical" className="mx-auto max-w-7xl p-12 sm:p-24 flex flex-col md:flex-row items-center justify-between gap-16 border-white/[0.08] bg-gradient-to-br from-brand-deep/80 to-brand-midnight rounded-[48px] shadow-[0_40px_100px_rgba(0,0,0,0.6)] relative overflow-hidden group">
            <div className="absolute inset-0 tactical-grid opacity-[0.05]" />
            <div className="absolute -bottom-20 -right-20 w-80 h-80 bg-brand-accent/5 blur-[100px] rounded-full group-hover:bg-brand-accent/10 transition-colors duration-1000" />

            <div className="space-y-6 text-center md:text-left relative z-10">
              <h2 className="text-4xl font-black uppercase tracking-tighter sm:text-7xl leading-[0.9] drop-shadow-2xl">READY FOR<br />SUMMONS?</h2>
              <p className="text-[13px] font-bold text-neutral-500 uppercase tracking-[0.2em] max-w-md mx-auto md:mx-0 opacity-80 leading-relaxed">
                 CONNECT YOUR SECURE TELEGRAM ID AND INITIALIZE THE HAREM PROTOCOL IMMEDIATELY.
              </p>
            </div>

            <div className="relative z-10 shrink-0">
                <Button
                onClick={() => {
                    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('heavy');
                    window.open(telegramUrl, '_blank');
                }}
                className="h-20 px-16 rounded-[28px] text-[13px] font-black uppercase tracking-[0.4em] shadow-[0_25px_60px_rgba(59,130,246,0.3)] hover:shadow-[0_25px_60px_rgba(59,130,246,0.5)] active:scale-95 transition-all duration-500"
                >
                <Database size={20} className="mr-4" strokeWidth={2.5} />
                INITIALIZE_SYNC
                </Button>
            </div>
          </Card>
        </section>
      </main>

      <footer className="px-12 py-16 border-t border-white/[0.04] bg-black/20 text-center relative">
        <div className="flex flex-col items-center gap-6">
           <div className="flex items-center gap-3 opacity-20">
              <div className="h-px w-8 bg-white" />
              <Heart size={14} fill="currentColor" />
              <div className="h-px w-8 bg-white" />
           </div>
           <p className="text-[10px] font-black text-neutral-700 uppercase tracking-[0.5em]">© 2025 WAIFU PROTOCOL. ALL RIGHTS RESERVED.</p>
           <div className="flex gap-4 opacity-10 font-mono text-[8px] uppercase tracking-tighter">
              <span>NODE_ID: {useMemo(() => "7X4K9L2".toUpperCase(), [])}</span>
              <span>•</span>
              <span>LINK_STATUS: SECURE</span>
           </div>
        </div>
      </footer>
    </div>
  );
};
