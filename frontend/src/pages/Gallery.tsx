import React, { useMemo, useState, useEffect } from 'react';
import { apiFetch } from '../api/client';
import { Card as CharacterCard } from '../components/character/Card';
import { CardSkeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { ArrowDown10, ArrowDownZA, ArrowUp01, ArrowUpAZ, ChevronDown, Search, Loader2, type LucideIcon, BookOpen } from 'lucide-react';
import { useInfiniteGrid } from '../hooks/useInfiniteGrid';
import { Character } from '../context/UserContext';
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
  const {
    items,
    loading,
    search,
    setSearch,
    rarity,
    setRarity,
    lastElementRef,
    error,
    refresh
  } = useInfiniteGrid<Character>('/gallery', { params: gridParams, limit: 42 });

  const [availableRarities, setAvailableRarities] = useState<string[]>([]);
  const rarityOptions = useMemo(
    () => availableRarities.map((value) => ({ value, label: cleanRarityLabel(value) || value })),
    [availableRarities],
  );

  useEffect(() => {
    apiFetch('/rarities').then(setAvailableRarities).catch(console.error);
  }, []);

  useEffect(() => {
    window.addEventListener('gallery-refresh', refresh);
    return () => window.removeEventListener('gallery-refresh', refresh);
  }, [refresh]);

  return (
    <div className="pb-24 pt-6 max-w-5xl mx-auto adaptive-px space-y-8 select-none">
      <header className="space-y-6">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
             <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
                  <BookOpen className="text-purple-500" size={22} />
             </div>
             <h1 className="text-2xl font-black text-white tracking-tighter uppercase">Character Archive</h1>
          </div>
          <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest">
            The complete database of all available characters in the seal.
          </p>
        </div>

        <div className="flex flex-col md:flex-row gap-4 items-start md:items-end">
            <div className="w-full md:w-80">
                <Input
                    icon={Search}
                    placeholder="SEARCH DATABASE..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            </div>

            <div className="flex flex-wrap items-center gap-2">
                <div className="relative group">
                    <select
                        aria-label="Filter by rarity"
                        value={rarity}
                        onChange={(event) => setRarity(event.target.value)}
                        className="h-10 pl-4 pr-10 bg-brand-deep border border-white/10 rounded-xl text-[10px] font-black text-white uppercase tracking-[0.2em] outline-none focus:border-brand-accent transition-all appearance-none cursor-pointer"
                    >
                        <option value="">ALL RARITIES</option>
                        {rarityOptions.map(({ value, label }) => (
                            <option key={value} value={value}>{label.toUpperCase()}</option>
                        ))}
                    </select>
                    <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 pointer-events-none group-focus-within:text-brand-accent" />
                </div>

                <div className="flex gap-1 p-1 bg-brand-deep border border-white/5 rounded-xl">
                    {SORT_OPTIONS.map(({ sort: optionSort, order: optionOrder, label, Icon }) => {
                        const active = sort === optionSort && order === optionOrder;
                        return (
                        <button
                            key={`${optionSort}-${optionOrder}`}
                            type="button"
                            title={`Sort ${label}`}
                            onClick={() => {
                                setSort(optionSort);
                                setOrder(optionOrder);
                            }}
                            className={cn(
                                "p-2 rounded-lg transition-all",
                                active
                                    ? "bg-brand-accent/10 text-brand-accent ring-1 ring-brand-accent/20"
                                    : "text-neutral-500 hover:text-neutral-300 hover:bg-white/5"
                            )}
                        >
                            <Icon size={16} />
                        </button>
                        );
                    })}
                </div>
            </div>
        </div>
      </header>

      {error && items.length === 0 ? (
        <ErrorState message={error} onAction={refresh} />
      ) : items.length > 0 ? (
        <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-3 sm:gap-4">
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
        <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-3 sm:gap-4">
          {Array.from({ length: 18 }).map((_, i) => <CardSkeleton key={`skeleton-${i}`} />)}
        </div>
      ) : (
        <EmptyState
          icon={Search}
          title="No characters found"
          message="No records match your current search parameters."
        />
      )}

      {loading && items.length > 0 && (
        <div className="flex justify-center py-12">
          <Loader2 size={32} className="animate-spin text-brand-accent/50" />
        </div>
      )}
    </div>
  );
};
