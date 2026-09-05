import { BookOpen, ChevronDown, Search, X } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { PokemonCard } from '../components/pokemon/PokemonCard';
import { PokemonDetailModal } from '../components/pokemon/PokemonDetailModal';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/ui/EmptyState';
import { Input } from '../components/ui/Input';
import { Skeleton } from '../components/ui/Skeleton';
import { useInfiniteGrid } from '../hooks/useInfiniteGrid';
import type { Pokemon } from '../context/UserContext';

const TYPES = [
  'normal', 'fire', 'water', 'electric', 'grass', 'ice',
  'fighting', 'poison', 'ground', 'flying', 'psychic', 'bug',
  'rock', 'ghost', 'dragon', 'dark', 'steel', 'fairy',
] as const;

const TYPE_EMOJI: Record<string, string> = {
  normal: '⭐', fire: '🔥', water: '💧', electric: '⚡', grass: '🌿',
  ice: '❄️', fighting: '🥊', poison: '☠️', ground: '⛰️', flying: '🕊️',
  psychic: '🔮', bug: '🐛', rock: '🪨', ghost: '👻', dragon: '🐉',
  dark: '🌑', steel: '⚙️', fairy: '🧚',
};

const PAGE_SIZE = 60;

export const Pokedex = () => {
  const [type, setType] = useState<string | null>(null);
  const [typeMenuOpen, setTypeMenuOpen] = useState(false);
  const [detailDex, setDetailDex] = useState<number | null>(null);
  const typeMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!typeMenuOpen) return;
    const onPointerDown = (e: PointerEvent) => {
      if (typeMenuRef.current && !typeMenuRef.current.contains(e.target as Node)) {
        setTypeMenuOpen(false);
      }
    };
    document.addEventListener('pointerdown', onPointerDown);
    return () => document.removeEventListener('pointerdown', onPointerDown);
  }, [typeMenuOpen]);

  const pickType = (t: string | null) => {
    window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
    setType(t);
    setTypeMenuOpen(false);
  };
  const gridParams = useMemo(() => (type ? { type } : {}), [type]);
  const { items, loading, search, setSearch, lastElementRef } = useInfiniteGrid<Pokemon>(
    '/shop/pokemon',
    { params: gridParams, limit: PAGE_SIZE },
  );
  const total = items.length;

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <h2 className="text-sm font-semibold text-zinc-300">
          Pokédex <span className="text-zinc-600">({total})</span>
        </h2>
      </div>

      <div className="relative">
        <Input
          icon={Search}
          placeholder="Search Pokémon by name or number..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className={search ? 'pr-10' : undefined}
        />
        {search && (
          <button
            type="button"
            aria-label="Clear search"
            onClick={() => setSearch('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-zinc-500 hover:text-zinc-200 transition-colors"
          >
            <X size={14} />
          </button>
        )}
      </div>

      <div className="relative" ref={typeMenuRef}>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setTypeMenuOpen((v) => !v)}
          rightIcon={
            <ChevronDown
              size={12}
              className={`transition-transform duration-200 ${typeMenuOpen ? 'rotate-180' : ''}`}
            />
          }
        >
          {type ? `${TYPE_EMOJI[type] ?? '❔'} ${type}` : 'All Types'}
        </Button>
        {typeMenuOpen && (
          <div className="absolute left-0 z-50 mt-1.5 w-44 max-h-64 overflow-y-auto rounded-md border border-white/10 bg-zinc-950 p-1 shadow-xl shadow-black/60">
            <button
              key="all"
              type="button"
              onClick={() => pickType(null)}
              className={`flex w-full items-center gap-2 rounded-sm px-2.5 py-2 text-left text-[11px] font-bold uppercase tracking-wider transition-colors ${
                type === null ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
              }`}
            >
              All
            </button>
            {TYPES.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => pickType(t)}
                className={`flex w-full items-center gap-2 rounded-sm px-2.5 py-2 text-left text-[11px] font-bold uppercase tracking-wider transition-colors ${
                  type === t ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
                }`}
              >
                <span>{TYPE_EMOJI[t]}</span> {t}
              </button>
            ))}
          </div>
        )}
      </div>

      {loading ? (
        <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
          {Array.from({ length: 12 }).map((_, i) => (
            <Skeleton key={i} className="aspect-square rounded-md" />
          ))}
        </div>
      ) : !items.length ? (
        <EmptyState
          icon={BookOpen}
          title="Nothing found"
          message={search ? `No Pokémon match "${search}".` : 'No Pokémon match this filter.'}
        />
      ) : (
        <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
          {items.map((p, i) => (
            <div
              key={p.dex}
              ref={i === items.length - 1 ? lastElementRef : null}
            >
              <PokemonCard pokemon={p} compact onClick={(pk) => setDetailDex(pk.dex)} />
            </div>
          ))}
          {loading &&
            Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={`more-${i}`} className="aspect-square rounded-md" />
            ))}
        </div>
      )}

      <PokemonDetailModal dex={detailDex} onClose={() => setDetailDex(null)} />
    </div>
  );
};
