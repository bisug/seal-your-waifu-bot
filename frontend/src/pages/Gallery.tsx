import React, { useState, useEffect } from 'react';
import { apiFetch } from '../api/client';
import { Card } from '../components/character/Card';
import { CardSkeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { Search, Loader2, Users } from 'lucide-react';
import { useInfiniteGrid } from '../hooks/useInfiniteGrid';
import { Character } from '../context/UserContext';
import { cn } from '../utils';

interface GalleryProps {
  onCharClick: (character: Character) => void;
}

export const Gallery = ({ onCharClick }: GalleryProps) => {
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
  } = useInfiniteGrid<Character>('/gallery');

  const [availableRarities, setAvailableRarities] = useState<string[]>([]);

  useEffect(() => {
    apiFetch('/rarities').then(setAvailableRarities).catch(console.error);
  }, []);

  return (
    <div className="pb-32 pt-0 px-4 relative select-none max-w-5xl mx-auto">
      <div className="sticky top-0 z-40 -mx-4 px-4 py-4 border-b border-white/5 mb-8 bg-brand-midnight/90 backdrop-blur-md shadow-sm">
        <div className="relative group mb-4 max-w-md mx-auto sm:mx-0">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-500 group-focus-within:text-brand-accent transition-colors" size={16} />
          <input 
            type="text" 
            placeholder="Search catalog..."
            className="w-full bg-brand-deep border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-sm font-medium focus:border-brand-accent outline-none transition-all placeholder:text-neutral-500 text-white"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="flex space-x-2 overflow-x-auto no-scrollbar pb-1">
          <button
            onClick={() => setRarity('')}
            className={cn(
              "px-4 py-1.5 rounded-lg text-sm font-semibold whitespace-nowrap transition-all border",
              rarity === ''
              ? "bg-white text-brand-midnight border-white shadow-sm"
              : "bg-brand-deep text-neutral-400 border-white/5 hover:border-white/10 hover:text-neutral-200"
            )}
          >
            All Rarities
          </button>
          {availableRarities.map((r) => (
            <button 
              key={r}
              onClick={() => setRarity(r)}
              className={cn(
                "px-4 py-1.5 rounded-lg text-sm font-semibold whitespace-nowrap transition-all border",
                rarity === r 
                ? "bg-white text-brand-midnight border-white shadow-sm"
                : "bg-brand-deep text-neutral-400 border-white/5 hover:border-white/10 hover:text-neutral-200"
              )}
            >
              {r.replace(/[\u2700-\u27bf]|[\u2190-\u21ff]|[\u2000-\u206f]|[\u2600-\u26ff]|[\u2b00-\u2bff]|[\u00a0-\u00bf]|\u2013|\u2014/g, '').trim()}
            </button>
          ))}
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
              className="relative group"
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
