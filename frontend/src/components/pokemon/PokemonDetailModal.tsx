import { AnimatePresence, m } from 'framer-motion';
import {
  Egg,
  Gauge,
  Heart,
  Ruler,
  Sparkles,
  Star,
  Swords,
  Volume2,
  Weight,
  X,
  Zap,
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import type { Pokemon } from '../../context/UserContext';
import { cn, FALLBACK_IMAGE } from '../../utils';
import { useApi } from '../../hooks/useApi';
import { cdnUrl } from './PokemonCard';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Skeleton } from '../ui/Skeleton';

const TYPE_EMOJI: Record<string, string> = {
  normal: '⭐',
  fire: '🔥',
  water: '💧',
  electric: '⚡',
  grass: '🌿',
  ice: '❄️',
  fighting: '🥊',
  poison: '☠️',
  ground: '⛰️',
  flying: '🕊️',
  psychic: '🔮',
  bug: '🐛',
  rock: '🪨',
  ghost: '👻',
  dragon: '🐉',
  dark: '🌑',
  steel: '⚙️',
  fairy: '🧚',
};

const GEN_LABEL: Record<string, string> = {
  'generation-i': 'I',
  'generation-ii': 'II',
  'generation-iii': 'III',
  'generation-iv': 'IV',
  'generation-v': 'V',
  'generation-vi': 'VI',
  'generation-vii': 'VII',
  'generation-viii': 'VIII',
  'generation-ix': 'IX',
};

const GROWTH_LABEL: Record<string, string> = {
  slow: 'Slow',
  'medium-slow': 'Medium-Slow',
  medium: 'Medium',
  'medium-fast': 'Medium-Fast',
  fast: 'Fast',
  'slow-then-very-fast': 'Slow→Fast',
  'fast-then-very-slow': 'Fast→Slow',
};

const genderLabel = (rate: number | null | undefined) => {
  if (rate === null || rate === undefined || rate < 0) return 'Genderless';
  const female = (rate / 8) * 100;
  return `♂ ${(100 - female).toFixed(0)}% / ♀ ${female.toFixed(0)}%`;
};

interface PokemonDetailModalProps {
  dex: number | null;
  onClose: () => void;
  onSetActive?: (dex: number) => void;
  settingDex?: number | null;
}

export const PokemonDetailModal = ({
  dex,
  onClose,
  onSetActive,
  settingDex,
}: PokemonDetailModalProps) => {
  const [shiny, setShiny] = useState(false);
  const [imgError, setImgError] = useState(false);
  const [viewDex, setViewDex] = useState<number | null>(dex);
  const dialogRef = useRef<HTMLDivElement>(null);

  // biome-ignore lint/correctness/useExhaustiveDependencies: reset per-dex UI when the viewed dex changes
  useEffect(() => {
    setShiny(false);
    setImgError(false);
  }, [viewDex]);

  useEffect(() => {
    if (dex !== null) setViewDex(dex);
  }, [dex]);

  const { data: detail, loading } = useApi<Pokemon>(
    viewDex === null ? '/pokemon/0' : `/pokemon/${viewDex}`,
    { manual: viewDex === null },
  );

  useEffect(() => {
    if (viewDex === null) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [viewDex, onClose]);

  const playCry = () => {
    if (!detail?.cry) return;
    try {
      const audio = new Audio(detail.cry);
      audio.volume = 0.5;
      audio.play().catch(() => {});
    } catch {
      /* audio unavailable */
    }
  };

  const stats = detail?.base_stats ?? {};
  const statRows: Array<[string, string, number]> = [
    ['HP', '❤️', stats.hp ?? 0],
    ['Attack', '⚔️', stats.atk ?? 0],
    ['Defense', '🛡', stats.def ?? 0],
    ['Sp. Atk', '✨', stats.spatk ?? 0],
    ['Sp. Def', '🔮', stats.spdef ?? 0],
    ['Speed', '💨', stats.spd ?? 0],
  ];
  const maxStat = Math.max(...statRows.map(([, , v]) => v), 1);

  return (
    <AnimatePresence>
      {dex !== null && (
        <div className="fixed inset-0 z-[1000] flex items-end sm:items-center justify-center p-0 sm:p-6">
          <m.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-md"
            onClick={onClose}
          />

          <m.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="relative w-full max-w-[440px] max-h-[92svh] bg-zinc-950 rounded-t-xl sm:rounded-xl flex flex-col overflow-hidden shadow-2xl border-t sm:border border-white/5"
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-label={detail?.name ?? 'Pokémon detail'}
            tabIndex={-1}
          >
            <div className="absolute right-4 top-4 z-20">
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="w-8 h-8 p-0 rounded-full bg-black/20 backdrop-blur-md border border-white/5 hover:bg-black/40"
                aria-label="Close"
              >
                <X size={16} />
              </Button>
            </div>

            {loading ? (
              <div className="p-6 space-y-4">
                <Skeleton className="aspect-[4/3] rounded-md" />
                <Skeleton className="h-6 w-2/3 rounded" />
                <Skeleton className="h-4 w-full rounded" />
                <Skeleton className="h-4 w-4/5 rounded" />
              </div>
            ) : !detail ? (
              <div className="p-8 text-center text-xs text-zinc-500">Failed to load details.</div>
            ) : (
              <>
                {/* Artwork */}
                <div className="relative aspect-[4/3] flex-shrink-0 bg-zinc-900/50 flex items-center justify-center overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-transparent to-transparent" />
                  <m.img
                    initial={{ scale: 0.95, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.1, duration: 0.4 }}
                    src={
                      imgError
                        ? FALLBACK_IMAGE
                        : cdnUrl(shiny && detail.shiny_img ? detail.shiny_img : detail.img)
                    }
                    onError={() => setImgError(true)}
                    className="relative z-10 w-full h-full object-contain p-6"
                    alt={detail.name}
                  />
                  <div className="absolute bottom-4 left-4 z-20 flex gap-2 flex-wrap">
                    {(detail.types ?? []).map((t) => (
                      <Badge key={t} variant="secondary" size="sm">
                        {TYPE_EMOJI[t] ?? '❔'} {t.toUpperCase()}
                      </Badge>
                    ))}
                    {detail.is_legendary && (
                      <Badge variant="premium" size="sm">
                        LEGENDARY
                      </Badge>
                    )}
                    {detail.is_mythical && (
                      <Badge variant="mythic" size="sm">
                        MYTHICAL
                      </Badge>
                    )}
                    {detail.owned && (
                      <Badge variant="success" size="sm">
                        OWNED
                      </Badge>
                    )}
                  </div>
                  <div className="absolute bottom-4 right-4 z-20 flex gap-1.5">
                    {detail.shiny_img && (
                      <Button
                        variant={shiny ? 'accent' : 'ghost'}
                        size="sm"
                        onClick={() => setShiny((s) => !s)}
                        className="w-8 h-8 p-0 rounded-full bg-black/30 backdrop-blur-md border border-white/10"
                        aria-label="Toggle shiny"
                        title="Toggle shiny"
                      >
                        <Sparkles size={14} />
                      </Button>
                    )}
                    {detail.cry && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={playCry}
                        className="w-8 h-8 p-0 rounded-full bg-black/30 backdrop-blur-md border border-white/10"
                        aria-label="Play cry"
                        title="Play cry"
                      >
                        <Volume2 size={14} />
                      </Button>
                    )}
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1 p-5 space-y-4 overflow-y-auto overscroll-contain max-sm:pb-[max(1.5rem,var(--sab))]">
                  <div className="space-y-1">
                    <span className="text-[9px] font-mono font-bold uppercase text-zinc-500 tracking-widest">
                      #{String(detail.dex).padStart(3, '0')}
                      {detail.generation && ` · GEN ${GEN_LABEL[detail.generation] ?? '?'}`}
                    </span>
                    <h2 className="text-2xl font-bold text-zinc-100 tracking-tight">
                      {detail.name}
                    </h2>
                    {detail.desc && (
                      <p className="text-[11px] font-bold text-zinc-500 uppercase tracking-widest">
                        {detail.desc}
                      </p>
                    )}
                  </div>

                  {detail.level !== undefined && (
                    <div className="flex items-center gap-2">
                      <Badge variant="rare">Lv.{detail.level}</Badge>
                      {detail.is_active && (
                        <Badge variant="warning" icon={Star}>
                          ACTIVE
                        </Badge>
                      )}
                      {onSetActive && !detail.is_active && detail.owned && (
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={settingDex === detail.dex}
                          onClick={() => onSetActive(detail.dex)}
                        >
                          {settingDex === detail.dex ? 'Setting…' : 'Set Active'}
                        </Button>
                      )}
                    </div>
                  )}

                  {detail.flavor_text && (
                    <p className="text-xs text-zinc-400 italic leading-relaxed border-l-2 border-white/10 pl-3">
                      {detail.flavor_text}
                    </p>
                  )}

                  {/* Stat bars */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[9px] font-bold uppercase text-zinc-500 tracking-widest">
                        Base Stats
                      </span>
                      <Badge variant="primary" size="sm">
                        BST {detail.base_total ?? 0}
                      </Badge>
                    </div>
                    {statRows.map(([label, emoji, value]) => (
                      <div key={label} className="flex items-center gap-2">
                        <span className="w-16 text-[10px] text-zinc-500 shrink-0">
                          {emoji} {label}
                        </span>
                        <div className="flex-1 h-1.5 bg-zinc-900 rounded-full overflow-hidden">
                          <m.div
                            initial={{ width: 0 }}
                            animate={{ width: `${(value / maxStat) * 100}%` }}
                            transition={{ duration: 0.5, ease: 'easeOut' }}
                            className="h-full bg-brand-accent rounded-full"
                          />
                        </div>
                        <span className="w-7 text-right text-[10px] font-mono text-zinc-400">
                          {value}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Profile grid */}
                  <div className="grid grid-cols-2 gap-2">
                    <div className="rounded-md border border-white/5 bg-zinc-900/50 p-2.5 space-y-1">
                      <span className="flex items-center gap-1 text-[9px] font-bold uppercase text-zinc-500 tracking-widest">
                        <Ruler size={10} /> Height
                      </span>
                      <span className="text-xs font-semibold text-zinc-200">
                        {((detail.height_dm ?? 0) / 10).toFixed(1)} m
                      </span>
                    </div>
                    <div className="rounded-md border border-white/5 bg-zinc-900/50 p-2.5 space-y-1">
                      <span className="flex items-center gap-1 text-[9px] font-bold uppercase text-zinc-500 tracking-widest">
                        <Weight size={10} /> Weight
                      </span>
                      <span className="text-xs font-semibold text-zinc-200">
                        {((detail.weight_hg ?? 0) / 10).toFixed(1)} kg
                      </span>
                    </div>
                    <div className="rounded-md border border-white/5 bg-zinc-900/50 p-2.5 space-y-1">
                      <span className="flex items-center gap-1 text-[9px] font-bold uppercase text-zinc-500 tracking-widest">
                        <Heart size={10} /> Friendship
                      </span>
                      <span className="text-xs font-semibold text-zinc-200">
                        {detail.base_happiness ?? '—'}
                      </span>
                    </div>
                    <div className="rounded-md border border-white/5 bg-zinc-900/50 p-2.5 space-y-1">
                      <span className="flex items-center gap-1 text-[9px] font-bold uppercase text-zinc-500 tracking-widest">
                        <Gauge size={10} /> Catch Rate
                      </span>
                      <span className="text-xs font-semibold text-zinc-200">
                        {detail.capture_rate ?? '—'}
                      </span>
                    </div>
                  </div>

                  {/* Abilities */}
                  {detail.abilities?.length ? (
                    <div className="space-y-1.5">
                      <span className="text-[9px] font-bold uppercase text-zinc-500 tracking-widest">
                        Abilities
                      </span>
                      <div className="flex gap-1.5 flex-wrap">
                        {detail.abilities.map((a) => (
                          <Badge
                            key={a.name}
                            variant={a.is_hidden ? 'outline' : 'secondary'}
                            size="sm"
                          >
                            {a.name.replace('-', ' ').toUpperCase()}
                            {a.is_hidden ? ' · HIDDEN' : ''}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  ) : null}

                  {/* Breeding */}
                  <div className="space-y-1.5">
                    <span className="flex items-center gap-1 text-[9px] font-bold uppercase text-zinc-500 tracking-widest">
                      <Egg size={10} /> Breeding
                    </span>
                    <div className="text-[11px] text-zinc-400 space-y-0.5">
                      <p>
                        Gender:{' '}
                        <span className="text-zinc-200">{genderLabel(detail.gender_rate)}</span>
                      </p>
                      <p>
                        Egg groups:{' '}
                        <span className="text-zinc-200">
                          {detail.egg_groups?.length ? detail.egg_groups.join(', ') : '—'}
                        </span>
                      </p>
                      <p>
                        Growth:{' '}
                        <span className="text-zinc-200">
                          {GROWTH_LABEL[detail.growth_rate ?? ''] ?? detail.growth_rate ?? '—'}
                        </span>
                      </p>
                    </div>
                  </div>

                  {/* Evolution line */}
                  {detail.evolution_line && detail.evolution_line.length > 1 && (
                    <div className="space-y-1.5">
                      <span className="flex items-center gap-1 text-[9px] font-bold uppercase text-zinc-500 tracking-widest">
                        <Zap size={10} /> Evolution Line
                      </span>
                      <div className="flex items-center gap-1 overflow-x-auto pb-1">
                        {detail.evolution_line.map((e, i) => (
                          <div key={e.dex} className="flex items-center gap-1">
                            {i > 0 && <span className="text-zinc-600 text-xs">→</span>}
                            <button
                              type="button"
                              onClick={() => {
                                window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
                                setViewDex(e.dex);
                              }}
                              className={cn(
                                'shrink-0 w-14 space-y-0.5 rounded-md border p-1 transition-colors',
                                e.dex === detail.dex
                                  ? 'border-brand-accent/40 bg-brand-accent/5'
                                  : 'border-white/5 bg-zinc-900/50 hover:border-white/15',
                              )}
                              aria-label={`View ${e.name}`}
                            >
                              <img
                                src={cdnUrl(e.img) || FALLBACK_IMAGE}
                                alt={e.name}
                                loading="lazy"
                                className="w-full aspect-square object-contain"
                              />
                              <p className="text-[8px] font-semibold text-zinc-300 truncate">
                                {e.name}
                              </p>
                              {e.owned && (
                                <p className="text-[7px] text-emerald-500 font-bold uppercase">
                                  Owned
                                </p>
                              )}
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Moves */}
                  {detail.moves?.length ? (
                    <div className="space-y-1.5">
                      <span className="flex items-center gap-1 text-[9px] font-bold uppercase text-zinc-500 tracking-widest">
                        <Swords size={10} /> Moves ({detail.moves.length})
                      </span>
                      <div className="flex gap-1 flex-wrap">
                        {detail.moves.slice(0, 18).map((mv) => (
                          <Badge key={mv} variant="outline" size="xs">
                            {mv.replace('-', ' ')}
                          </Badge>
                        ))}
                        {detail.moves.length > 18 && (
                          <Badge variant="outline" size="xs">
                            +{detail.moves.length - 18} more
                          </Badge>
                        )}
                      </div>
                    </div>
                  ) : null}
                </div>
              </>
            )}
          </m.div>
        </div>
      )}
    </AnimatePresence>
  );
};
