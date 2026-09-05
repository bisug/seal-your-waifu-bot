import { BookOpen } from 'lucide-react';
import { useMemo, useState } from 'react';
import { PokemonCard } from '../components/pokemon/PokemonCard';
import { PokemonDetailModal } from '../components/pokemon/PokemonDetailModal';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/ui/EmptyState';
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
  const [detailDex, setDetailDex] = useState<number | null>(null);
  const gridParams = useMemo(() => (type ? { type } : {}), [type]);
  const { items, loading, lastElementRef } = useInfiniteGrid<Pokemon>(
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

      <div className="flex gap-1.5 flex-wrap">
        <Button
          variant={type === null ? 'secondary' : 'outline'}
          size="sm"
          onClick={() => setType(null)}
        >
          All
        </Button>
        {TYPES.map((t) => (
          <Button
            key={t}
            variant={type === t ? 'secondary' : 'outline'}
            size="sm"
            onClick={() => setType(t)}
          >
            {TYPE_EMOJI[t]} {t}
          </Button>
        ))}
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
          message="No Pokémon match this filter."
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
