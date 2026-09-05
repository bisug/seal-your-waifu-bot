import { BookOpen } from 'lucide-react';
import { useEffect, useState } from 'react';
import { apiFetch, getErrorMessage } from '../api/client';
import { PokemonCard } from '../components/pokemon/PokemonCard';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/ui/EmptyState';
import { Skeleton } from '../components/ui/Skeleton';
import { useToast } from '../components/ui/Toast';
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
  const { addToast } = useToast();
  const [items, setItems] = useState<Pokemon[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [type, setType] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const params = new URLSearchParams({ page: '1', limit: String(PAGE_SIZE) });
        if (type) params.set('type', type);
        const res = await apiFetch(`/shop/pokemon?${params}`);
        if (cancelled) return;
        setItems(res.items ?? []);
        setTotal(res.total ?? 0);
        setPage(1);
      } catch (err) {
        if (!cancelled) addToast(getErrorMessage(err), 'error');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    setLoading(true);
    load();
    return () => {
      cancelled = true;
    };
  }, [type, addToast]);

  const loadMore = async () => {
    setLoadingMore(true);
    try {
      const params = new URLSearchParams({
        page: String(page + 1),
        limit: String(PAGE_SIZE),
      });
      if (type) params.set('type', type);
      const res = await apiFetch(`/shop/pokemon?${params}`);
      setItems((prev) => [...prev, ...(res.items ?? [])]);
      setTotal(res.total ?? 0);
      setPage((p) => p + 1);
    } catch (err) {
      addToast(getErrorMessage(err), 'error');
    } finally {
      setLoadingMore(false);
    }
  };

  const hasMore = items.length < total;

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
        <>
          <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
            {items.map((p) => (
              <PokemonCard key={p.dex} pokemon={p} compact />
            ))}
          </div>
          {hasMore && (
            <Button
              variant="outline"
              className="w-full"
              disabled={loadingMore}
              onClick={loadMore}
            >
              {loadingMore ? 'Loading…' : `Load more (${items.length}/${total})`}
            </Button>
          )}
        </>
      )}
    </div>
  );
};
