import React, { useState, useEffect } from 'react';
import { apiFetch } from '../api/client';
import { Card } from '../components/character/Card';
import { CardSkeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { Search, Loader2, Users, CheckCircle2 } from 'lucide-react';
import { useInfiniteGrid } from '../hooks/useInfiniteGrid';
import { Character, useUser } from '../context/UserContext';
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
    lastElementRef
  } = useInfiniteGrid<Character>('/gallery');

  const [availableRarities, setAvailableRarities] = useState<string[]>([]);

  useEffect(() => {
    apiFetch('/rarities').then(setAvailableRarities).catch(console.error);
  }, []);

  return (
    <div className="pb-32 pt-0 px-4 relative ">
      <div className="sticky top-0 z-40 -mx-4 px-4 py-4 border-b border-white/5 mb-6 bg-brand-midnight">
        <div className="relative group mb-4">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500 group-focus-within:text-brand-accent transition-colors" size={14} />
          <input 
            type="text" 
            placeholder="Search catalog..."
            className="w-full bg-zinc-900 border border-white/5 rounded-md py-2.5 pl-10 pr-4 text-xs focus:border-brand-accent/50 outline-none transition-all placeholder:text-zinc-600 font-medium"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="flex space-x-2 overflow-x-auto no-scrollbar py-0.5">
          <button
            onClick={() => setRarity('')}
            className={`px-3 py-1.5 rounded text-xs font-medium whitespace-nowrap transition-all border ${
              rarity === ''
              ? 'bg-zinc-100 text-zinc-950 border-zinc-100 shadow-sm'
              : 'bg-zinc-900 text-zinc-400 border-white/5 hover:border-zinc-700'
            }`}
          >
            All Rarities
          </button>
          {availableRarities.map((r) => (
            <button 
              key={r}
              onClick={() => setRarity(r)}
              className={`px-3 py-1.5 rounded text-xs font-medium whitespace-nowrap transition-all border ${
                rarity === r 
                ? 'bg-zinc-100 text-zinc-950 border-zinc-100 shadow-sm'
                : 'bg-zinc-900 text-zinc-400 border-white/5 hover:border-zinc-700'
              }`}
            >
              {r.replace(/[\u2700-\u27bf]|[\u2190-\u21ff]|[\u2000-\u206f]|[\u2600-\u26ff]|[\u2b00-\u2bff]|[\u00a0-\u00bf]|\u2013|\u2014/g, '').trim()}
            </button>
          ))}
        </div>
      </div>

      {items.length > 0 ? (
        <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-2">
          {items.map((char, i) => (
            <div
              key={char.id}
              ref={i === items.length - 1 ? lastElementRef : null}
              className="relative"
            >
              <Card character={char} onClick={() => onCharClick(char)} />
              {char.owned && (
                <div className="absolute inset-0 flex items-center justify-center rounded-md z-30 pointer-events-none bg-zinc-950/40">
                  <div className="bg-brand-accent text-white px-2 py-1 rounded-sm text-[8px] font-bold uppercase tracking-wider shadow-sm flex items-center gap-1 border border-white/10">
                    <CheckCircle2 size={10} strokeWidth={3} />
                    <span>Owned</span>
                  </div>
                </div>
              )}
            </div>
          ))}
          {loading && Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={`load-${i}`} />)}
        </div>
      ) : loading ? (
        <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-2">
          {Array.from({ length: 18 }).map((_, i) => <CardSkeleton key={`skeleton-${i}`} />)}
        </div>
      ) : (
        <EmptyState
          icon={Users}
          title="No results found"
          message="Adjust your filters to see more characters."
        />
      )}

      {loading && items.length > 0 && (
        <div className="flex justify-center py-8">
          <Loader2 size={20} className="animate-spin text-zinc-800" />
        </div>
      )}
    </div>
  );
};
