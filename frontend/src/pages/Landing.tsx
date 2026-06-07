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
} from 'lucide-react';

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
    meta: 'Animated pull',
    className: 'left-[9%] top-[17%] hidden sm:block',
    rotate: -13,
    speed: -0.55,
    tone: 'from-rose-500/30 via-fuchsia-500/10 to-cyan-400/25',
  },
  {
    id: 'pet',
    badge: 'PET',
    title: 'Nova Lynx',
    meta: 'Luck aura',
    className: 'right-[8%] top-[16%]',
    rotate: 11,
    speed: 0.48,
    tone: 'from-emerald-400/25 via-cyan-300/10 to-zinc-950',
  },
  {
    id: 'egg',
    badge: 'EGG',
    title: 'Arc Egg',
    meta: '02:18:40',
    className: 'left-[14%] bottom-[12%]',
    rotate: 9,
    speed: 0.36,
    tone: 'from-amber-300/30 via-orange-500/10 to-zinc-950',
  },
  {
    id: 'rank',
    badge: 'TOP',
    title: 'Rank 01',
    meta: 'Daily ladder',
    className: 'right-[17%] bottom-[10%] hidden md:block',
    rotate: -8,
    speed: -0.4,
    tone: 'from-sky-400/25 via-indigo-400/10 to-zinc-950',
  },
];

const featureCards: FeatureCardProps[] = [
  {
    icon: Sparkles,
    title: 'Cinematic pulls',
    description: 'Daily shop rolls, rarity reveals, and fast collection loops built for Telegram.',
    tone: 'text-fuchsia-300 bg-fuchsia-400/10 border-fuchsia-300/20',
  },
  {
    icon: Egg,
    title: 'Egg incubation',
    description: 'Hatch timed eggs, unlock fresh characters, and keep your queue moving.',
    tone: 'text-amber-300 bg-amber-300/10 border-amber-300/20',
  },
  {
    icon: PawPrint,
    title: 'Pet companions',
    description: 'Bring pets into the economy with mood, levels, abilities, and shop unlocks.',
    tone: 'text-emerald-300 bg-emerald-300/10 border-emerald-300/20',
  },
  {
    icon: Trophy,
    title: 'Ranked chase',
    description: 'Quests, referrals, passes, and leaderboards give collectors a reason to return.',
    tone: 'text-sky-300 bg-sky-300/10 border-sky-300/20',
  },
];

const metrics = [
  { label: 'Daily shop', value: 'Rotating' },
  { label: 'Collection', value: 'Catalog' },
  { label: 'Pets', value: 'Active' },
  { label: 'Quests', value: 'Live' },
];

const rarityRows = [
  { label: 'Common', width: '32%', color: 'bg-neutral-400' },
  { label: 'Rare', width: '48%', color: 'bg-sky-400' },
  { label: 'Epic', width: '66%', color: 'bg-fuchsia-400' },
  { label: 'Mythic', width: '84%', color: 'bg-amber-300' },
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
        className={`landing-holo-card h-40 w-28 overflow-hidden rounded-lg border border-white/15 bg-gradient-to-br ${tone} p-3 shadow-2xl backdrop-blur-md sm:h-44 sm:w-32`}
        animate={reduceMotion ? undefined : { y: [0, -10, 0], rotate: [rotate, rotate + 2, rotate] }}
        transition={{ duration: 5.8, repeat: Infinity, ease: 'easeInOut' }}
        style={reduceMotion ? { transform: `rotate(${rotate}deg)` } : undefined}
      >
        <div className="mb-12 flex items-center justify-between">
          <span className="rounded-md border border-white/15 bg-black/25 px-2 py-1 text-[10px] font-black text-white">
            {badge}
          </span>
          <Star size={15} className="text-white/70" />
        </div>
        <div className="absolute inset-x-4 top-16 h-14 rounded-lg border border-white/10 bg-black/20" />
        <div className="absolute inset-x-3 bottom-3">
          <p className="text-sm font-black leading-tight text-white">{title}</p>
          <p className="mt-1 text-[10px] font-bold uppercase text-white/55">{meta}</p>
        </div>
      </motion.div>
    </div>
  );
};

const FeatureCard = ({ icon: Icon, title, description, tone }: FeatureCardProps) => (
  <article className="rounded-lg border border-white/10 bg-white/[0.035] p-5 shadow-sm">
    <div className={`mb-5 flex h-10 w-10 items-center justify-center rounded-lg border ${tone}`}>
      <Icon size={19} />
    </div>
    <h3 className="text-base font-black text-white">{title}</h3>
    <p className="mt-3 text-sm font-medium leading-6 text-neutral-400">{description}</p>
  </article>
);

export const Landing = ({ error, onRetry }: LandingProps) => {
  const reduceMotion = Boolean(useReducedMotion());
  const [pointer, setPointer] = useState<ScenePointer>({ x: 0, y: 0 });

  const botUsername = useMemo(
    () => (import.meta.env.VITE_BOT_USERNAME || 'Seal_Your_WaifuBot').replace(/^@/, ''),
    [],
  );
  const telegramUrl = `https://t.me/${botUsername}`;

  const handlePointerMove = (event: PointerEvent<HTMLElement>) => {
    if (reduceMotion) return;

    const rect = event.currentTarget.getBoundingClientRect();
    setPointer({
      x: ((event.clientX - rect.left) / rect.width - 0.5) * 52,
      y: ((event.clientY - rect.top) / rect.height - 0.5) * 52,
    });
  };

  const sceneStyle = {
    '--scene-x': `${pointer.x}px`,
    '--scene-y': `${pointer.y}px`,
  } as CSSProperties;

  return (
    <div className="landing-page h-svh min-h-svh overflow-x-hidden overflow-y-auto bg-[#08090b] text-white">
      <section
        className="landing-hero relative min-h-[82svh] overflow-hidden px-5 pb-12 pt-24 sm:px-8 lg:px-10"
        onPointerMove={handlePointerMove}
        onPointerLeave={() => setPointer({ x: 0, y: 0 })}
        style={sceneStyle}
      >
        <div className="landing-grid pointer-events-none absolute inset-0" aria-hidden="true" />
        <div className="landing-stage pointer-events-none absolute inset-0" aria-hidden="true">
          <motion.div
            className="landing-core absolute left-1/2 top-[46%] h-72 w-72 rounded-full border border-white/10"
            animate={reduceMotion ? undefined : { rotate: 360 }}
            transition={{ duration: 34, repeat: Infinity, ease: 'linear' }}
            style={{ x: '-50%', y: '-50%' }}
          />
          <motion.div
            className="landing-core landing-core-wide absolute left-1/2 top-[46%] h-[27rem] w-[27rem] rounded-full border border-cyan-300/10"
            animate={reduceMotion ? undefined : { rotate: -360 }}
            transition={{ duration: 46, repeat: Infinity, ease: 'linear' }}
            style={{ x: '-50%', y: '-50%' }}
          />
          <div className="landing-runway absolute left-1/2 top-[46%] h-[34rem] w-[34rem] -translate-x-1/2 -translate-y-1/2 rounded-full" />

          {sceneCards.map((card) => (
            <SceneCard key={card.id} {...card} pointer={pointer} reduceMotion={reduceMotion} />
          ))}

          <div className="absolute left-1/2 top-[47%] z-10 flex h-28 w-28 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-lg border border-white/15 bg-black/30 shadow-2xl backdrop-blur-md">
            <img src="/favicon.svg" alt="" className="h-14 w-14" aria-hidden="true" />
          </div>
        </div>

        <header className="absolute left-0 right-0 top-0 z-30">
          <nav className="mx-auto flex h-[72px] w-full max-w-7xl items-center justify-between px-5 sm:px-8 lg:px-10">
            <a href="/" className="flex min-w-0 items-center gap-3" aria-label="Seal home">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-white/10 bg-white/5">
                <img src="/favicon.svg" alt="" className="h-5 w-5" aria-hidden="true" />
              </span>
              <span className="truncate text-sm font-black text-white">Seal</span>
            </a>
            <a
              href={telegramUrl}
              target="_blank"
              rel="noreferrer"
              className="hidden h-10 shrink-0 items-center gap-2 rounded-lg border border-white/10 bg-white/10 px-4 text-xs font-black uppercase text-white transition-colors hover:bg-white/15 sm:inline-flex"
              aria-label="Open Seal in Telegram"
            >
              <Send size={14} />
              <span>Telegram</span>
            </a>
          </nav>
        </header>

        <div className="relative z-20 mx-auto flex max-w-7xl flex-col justify-center">
          <div className="w-full max-w-[22rem] pt-2 sm:max-w-3xl sm:pt-10 lg:pt-16">
            <div className="mb-5 inline-flex items-center gap-2 rounded-lg border border-cyan-300/20 bg-cyan-300/10 px-3 py-2 text-xs font-black uppercase text-cyan-200">
              <Zap size={14} />
              Telegram collector RPG
            </div>

            <h1 className="max-w-4xl text-[2.15rem] font-black leading-[1.02] tracking-normal text-white sm:text-6xl sm:leading-[0.95] lg:text-7xl">
              <span className="block sm:inline">Collect rare cards, </span>
              <span className="block sm:inline">hatch eggs, </span>
              <span className="block sm:inline">and flex the </span>
              <span className="block sm:inline">perfect lineup.</span>
            </h1>

            <p className="mt-6 max-w-[21rem] text-base font-semibold leading-7 text-neutral-300 sm:max-w-xl sm:text-lg">
              Seal turns every Telegram session into a compact anime collection loop with drops, pets,
              quests, shops, and leaderboards.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <a
                href={telegramUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-flex h-12 items-center justify-center gap-2 rounded-lg bg-white px-5 text-sm font-black text-zinc-950 transition-transform active:scale-[0.98]"
              >
                <Send size={17} />
                Open in Telegram
              </a>
              <a
                href="#drops"
                className="inline-flex h-12 items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/10 px-5 text-sm font-black text-white transition-colors hover:bg-white/15"
              >
                <BookOpen size={17} />
                View drops
                <ArrowRight size={16} />
              </a>
            </div>

            {error && (
              <div className="mt-5 flex max-w-xl flex-col gap-3 rounded-lg border border-amber-300/20 bg-amber-300/10 p-4 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm font-semibold leading-6 text-amber-100">{error}</p>
                {onRetry && (
                  <button
                    type="button"
                    onClick={onRetry}
                    className="inline-flex h-10 shrink-0 items-center justify-center rounded-lg border border-amber-100/20 px-4 text-xs font-black uppercase text-amber-50 transition-colors hover:bg-amber-100/10"
                  >
                    Retry
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="border-y border-white/10 bg-[#0d0f13]" aria-label="Seal highlights">
        <div className="mx-auto grid max-w-7xl grid-cols-2 gap-px bg-white/10 sm:grid-cols-4">
          {metrics.map((metric) => (
            <div key={metric.label} className="bg-[#0d0f13] px-5 py-5 sm:px-8">
              <p className="text-[10px] font-black uppercase text-neutral-500">{metric.label}</p>
              <p className="mt-2 text-lg font-black text-white">{metric.value}</p>
            </div>
          ))}
        </div>
      </section>

      <main id="drops">
        <section className="px-5 py-14 sm:px-8 lg:px-10">
          <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[0.85fr_1.15fr] lg:items-end">
            <div>
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg border border-white/10 bg-white/5">
                <Gem size={21} className="text-cyan-300" />
              </div>
              <h2 className="max-w-lg text-3xl font-black leading-tight tracking-normal text-white sm:text-4xl">
                A compact loop with enough depth to keep collectors plotting.
              </h2>
              <p className="mt-4 max-w-xl text-sm font-medium leading-7 text-neutral-400">
                The webapp is tuned for quick taps, clear progress, and high-signal collection moments.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              {featureCards.map((feature) => (
                <FeatureCard key={feature.title} {...feature} />
              ))}
            </div>
          </div>
        </section>

        <section className="border-t border-white/10 bg-[#0c0c10] px-5 py-14 sm:px-8 lg:px-10">
          <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-2">
              {['SR', 'SSR', 'UR', 'EX'].map((rarity, index) => (
                <article
                  key={rarity}
                  className="landing-drop-card relative min-h-44 overflow-hidden rounded-lg border border-white/10 bg-white/[0.035] p-4"
                >
                  <div className="flex items-center justify-between">
                    <span className="rounded-md border border-white/10 bg-black/20 px-2 py-1 text-[10px] font-black text-white">
                      {rarity}
                    </span>
                    {index % 2 === 0 ? (
                      <Crown size={16} className="text-amber-300" />
                    ) : (
                      <Bot size={16} className="text-cyan-300" />
                    )}
                  </div>
                  <div className="absolute inset-x-4 top-16 h-16 rounded-lg border border-white/10 bg-black/20" />
                  <div className="absolute bottom-4 left-4 right-4">
                    <p className="text-sm font-black text-white">Drop tier {index + 1}</p>
                    <div className="mt-3 h-1.5 rounded-full bg-white/10">
                      <div
                        className={`h-full rounded-full ${rarityRows[index].color}`}
                        style={{ width: rarityRows[index].width }}
                      />
                    </div>
                  </div>
                </article>
              ))}
            </div>

            <div>
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg border border-white/10 bg-white/5">
                <Sparkles size={21} className="text-fuchsia-300" />
              </div>
              <h2 className="max-w-lg text-3xl font-black leading-tight tracking-normal text-white sm:text-4xl">
                Designed for quick decisions, clean reveals, and a daily reason to return.
              </h2>
              <div className="mt-6 space-y-4">
                {rarityRows.map((row) => (
                  <div key={row.label}>
                    <div className="mb-2 flex items-center justify-between text-xs font-black uppercase">
                      <span className="text-neutral-400">{row.label}</span>
                      <span className="text-white">{row.width}</span>
                    </div>
                    <div className="h-2 rounded-full bg-white/10">
                      <div className={`h-full rounded-full ${row.color}`} style={{ width: row.width }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="px-5 py-14 sm:px-8 lg:px-10">
          <div className="mx-auto flex max-w-7xl flex-col items-start gap-6 border-t border-white/10 pt-10 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-2xl font-black tracking-normal text-white">Ready to start the collection?</h2>
              <p className="mt-2 text-sm font-semibold text-neutral-400">Open Seal from Telegram and jump into your profile.</p>
            </div>
            <a
              href={telegramUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex h-12 items-center justify-center gap-2 rounded-lg bg-cyan-300 px-5 text-sm font-black text-zinc-950 transition-transform active:scale-[0.98]"
            >
              <Send size={17} />
              Launch Seal
            </a>
          </div>
        </section>
      </main>
    </div>
  );
};
