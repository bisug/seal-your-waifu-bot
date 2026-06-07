import React, { useMemo, useState, useEffect } from 'react';
import { apiFetch } from '../api/client';
import { Card } from '../components/character/Card';
import { CardSkeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { ArrowDown10, ArrowDownZA, ArrowUp01, ArrowUpAZ, ChevronDown, Search, Loader2, Users, type LucideIcon } from 'lucide-react';
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
    <div className="pb-32 pt-0 px-4 relative select-none max-w-5xl mx-auto">
      <div className="sticky top-0 z-40 -mx-4 px-4 py-4 border-b border-white/5 mb-8 bg-brand-midnight/90 backdrop-blur-md shadow-sm">
        <div className="relative group mb-4 max-w-md mx-auto sm:mx-0">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-500 group-focus-within:text-brand-accent transition-colors" size={16} />
          <input 
            type="text" 
            placeholder="Search by name, ID, or anime..."
            className="w-full bg-brand-deep border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-sm font-medium focus:border-brand-accent outline-none transition-all placeholder:text-neutral-500 text-white"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="flex flex-wrap gap-2 mb-3">
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
                  "inline-flex h-9 items-center gap-2 px-3 rounded-lg text-xs font-bold whitespace-nowrap transition-all border",
                  active
                    ? "bg-brand-accent text-brand-midnight border-brand-accent shadow-sm"
                    : "bg-brand-deep text-neutral-400 border-white/5 hover:border-white/10 hover:text-neutral-200"
                )}
              >
                <Icon size={14} />
                <span>{label}</span>
              </button>
            );
          })}
        </div>

        <div className="relative max-w-xs">
          <select
            aria-label="Filter by rarity"
            value={rarity}
            onChange={(event) => setRarity(event.target.value)}
            className="h-10 w-full appearance-none rounded-lg border border-white/10 bg-brand-deep px-3 pr-9 text-sm font-semibold text-white outline-none transition-colors focus:border-brand-accent"
          >
            <option value="">All Rarities</option>
            {rarityOptions.map(({ value, label }) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
          <ChevronDown
            size={16}
            className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500"
          />
        </div>
      </div>

      {error && items.length === 0 ? (
        <ErrorState message={error} onAction={refresh} />
      ) : items.length > 0 ? (
        <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-7 gap-3">
          {items.map((char, i) => (
            <div
              key={char.id}
              ref={i === items.length - 1 ? lastElementRef : null}
              className="relative group [content-visibility:auto] [contain-intrinsic-size:180px]"
            >
              <Card character={char} onClick={() => onCharClick(char)} />
            </div>
          ))}
          {loading && Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={`load-${i}`} />)}
        </div>
      ) : loading ? (
        <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-7 gap-3">
          {Array.from({ length: 18 }).map((_, i) => <CardSkeleton key={`skeleton-${i}`} />)}
        </div>
      ) : (
        <EmptyState
          icon={Users}
          title="No results found"
          message="Adjust your search criteria to discover more characters."
        />
      )}

      {loading && items.length > 0 && (
        <div className="flex justify-center py-10">
          <Loader2 size={24} className="animate-spin text-neutral-600" />
        </div>
      )}
    </div>
  );
};
