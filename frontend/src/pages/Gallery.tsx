import {
  ArrowDown10,
  ArrowDownZA,
  ArrowUp01,
  ArrowUpAZ,
  BookOpen,
  ChevronDown,
  Database,
  Loader2,
  type LucideIcon,
  RefreshCw,
  Search,
  X,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useApi } from '../hooks/useApi';
import { Card as CharacterCard } from '../components/character/Card';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { Input } from '../components/ui/Input';
import { CardSkeleton } from '../components/ui/Skeleton';
import { Character } from '../context/UserContext';
import { useInfiniteGrid } from '../hooks/useInfiniteGrid';
import { cleanRarityLabel, cn } from '../utils';

interface GalleryProps {
  onCharClick: (character: Character) => void;
}

type CatalogSort = 'numeric' | 'alphabet';
type CatalogOrder = 'asc' | 'desc';

const SORT_OPTIONS: Array<{
  sort: CatalogSort;
  order: CatalogOrder;
  label: string;
  Icon: LucideIcon;
}> = [
  { sort: 'numeric', order: 'asc', label: 'ID Asc', Icon: ArrowUp01 },
  { sort: 'numeric', order: 'desc', label: 'ID Desc', Icon: ArrowDown10 },
  { sort: 'alphabet', order: 'asc', label: 'A-Z', Icon: ArrowUpAZ },
  { sort: 'alphabet', order: 'desc', label: 'Z-A', Icon: ArrowDownZA },
];

export const Gallery = ({ onCharClick }: GalleryProps) => {
  const [sort, setSort] = useState<CatalogSort>('numeric');
  const [order, setOrder] = useState<CatalogOrder>('asc');
  const gridParams = useMemo(() => ({ sort, order }), [sort, order]);
  const { items, loading, search, setSearch, rarity, setRarity, lastElementRef, error, refresh } =
    useInfiniteGrid<Character>('/gallery', { params: gridParams, limit: 42 });

  const [availableRarities, setAvailableRarities] = useState<string[]>([]);
  const rarityOptions = useMemo(
    () => availableRarities.map((value) => ({ value, label: cleanRarityLabel(value) || value })),
    [availableRarities],
  );

  const { data: rarityData } = useApi<string[]>('/rarities');

  useEffect(() => {
    if (rarityData) setAvailableRarities(rarityData);
  }, [rarityData]);

  return (
    <div className="pt-6 max-w-5xl mx-auto adaptive-px space-y-8 select-none">
      <header className="space-y-6">
        <div className="flex items-center gap-2.5">
          <BookOpen className="text-brand-accent" size={20} />
          <div className="flex flex-col flex-1">
            <h1 className="text-xl font-bold text-zinc-100 uppercase tracking-tight">Archive</h1>
            <div className="flex items-center gap-1.5 opacity-60">
              <Database size={10} className="text-zinc-500" />
              <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                Every character you've Collected
              </p>
            </div>
          </div>
          <button
            type="button"
            aria-label="Refresh archive"
            onClick={() => {
              window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
              refresh();
            }}
            className="w-9 h-9 flex items-center justify-center rounded-md bg-zinc-900 border border-white/5 text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 transition-all shrink-0"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        <div className="flex flex-col md:flex-row gap-4 items-stretch md:items-end bg-zinc-950 border border-white/5 p-4 rounded-md">
          <div className="flex-1 space-y-1.5">
            <span className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest pl-1">
              Search Characters
            </span>
            <div className="relative">
              <Input
                icon={Search}
                placeholder="Enter character name..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className={cn('h-10', search && 'pr-10')}
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
          </div>

          <div className="space-y-1.5">
            <span className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest pl-1">
              Filter & Sort
            </span>
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative group w-40 sm:w-48">
                <select
                  aria-label="Filter by rarity"
                  value={rarity}
                  onChange={(event) => setRarity(event.target.value)}
                  className="w-full h-10 pl-3.5 pr-10 bg-zinc-900 border border-white/10 rounded-md text-[10px] font-bold text-zinc-400 uppercase tracking-widest outline-none focus:border-brand-accent appearance-none cursor-pointer hover:bg-zinc-800 transition-all"
                >
                  <option value="">ALL RARITIES</option>
                  {rarityOptions.map(({ value, label }) => (
                    <option key={value} value={value}>
                      {label.toUpperCase()}
                    </option>
                  ))}
                </select>
                <ChevronDown
                  size={14}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-zinc-600 pointer-events-none group-focus-within:text-brand-accent transition-colors"
                />
              </div>

              <div className="flex gap-1 p-1 bg-zinc-900 border border-white/10 rounded-md h-10 items-center">
                {SORT_OPTIONS.map(({ sort: optionSort, order: optionOrder, label, Icon }) => {
                  const active = sort === optionSort && order === optionOrder;
                  return (
                    <button
                      key={`${optionSort}-${optionOrder}`}
                      type="button"
                      title={`Sort ${label}`}
                      onClick={() => {
                        window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
                        setSort(optionSort);
                        setOrder(optionOrder);
                      }}
                      className={cn(
                        'p-2.5 rounded transition-all',
                        active
                          ? 'bg-brand-accent text-white'
                          : 'text-zinc-600 hover:text-zinc-300 hover:bg-white/5',
                      )}
                    >
                      <Icon size={16} />
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </header>

      {!loading && !error && items.length > 0 && (
        <p className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest -mt-4">
          {items.length} record{items.length === 1 ? '' : 's'} found
        </p>
      )}

      {error && items.length === 0 ? (
        <div className="py-20">
          <ErrorState message={error} onAction={refresh} />
        </div>
      ) : items.length > 0 ? (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3 sm:gap-4 px-0.5">
          {items.map((char, i) => (
            <CharacterCard
              key={char.id}
              ref={i === items.length - 1 ? lastElementRef : null}
              character={char}
              onClick={() => onCharClick(char)}
            />
          ))}
          {loading && Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={`load-${i}`} />)}
        </div>
      ) : loading ? (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3 sm:gap-4 px-0.5">
          {Array.from({ length: 18 }).map((_, i) => (
            <CardSkeleton key={`skeleton-${i}`} />
          ))}
        </div>
      ) : (
        <div className="py-20 border border-dashed border-white/5 rounded-lg bg-zinc-950/50">
          <EmptyState
            icon={Search}
            title="Archive Mismatch"
            message="Nothing here yet — hatch some eggs first."
          />
        </div>
      )}

      {loading && items.length > 0 && (
        <div className="flex justify-center py-20">
          <Loader2 size={24} className="animate-spin text-zinc-700" />
        </div>
      )}
    </div>
  );
};
