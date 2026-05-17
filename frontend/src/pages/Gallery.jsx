import React, { useState, useEffect, useCallback, useRef } from 'react';
import { apiFetch } from '../api/client';
import { Card } from '../components/character/Card';
import { Skeleton, CardSkeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { Search, Loader2, Users, CheckCircle2 } from 'lucide-react';
import { useInfiniteGrid } from '../hooks/useInfiniteGrid';

export const Gallery = ({ onCharClick }) => {
  const {
    items,
    loading,
    page,
    search,
    setSearch,
    rarity,
    setRarity,
    lastElementRef
  } = useInfiniteGrid('/gallery');

  const [availableRarities, setAvailableRarities] = useState([]);

  useEffect(() => {
    apiFetch('/rarities').then(setAvailableRarities).catch(console.error);
  }, []);

  return (
    <div className="pb-32 pt-0 px-4 relative ">
      <div className="sticky top-0 z-40 bg-brand-midnight/80 backdrop-blur-xl -mx-4 px-4 py-4 border-b border-white/5 mb-6">
        <div className="relative group mb-4">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-brand-accent transition-colors" size={14} />
          <input 
            type="text" 
            placeholder="Search characters or anime..." 
            className="w-full bg-slate-900/40 border border-white/10 rounded-xl py-3 pl-11 pr-4 text-xs focus:border-brand-accent/50 outline-none transition-all placeholder:text-slate-600 font-bold tracking-tight backdrop-blur-sm"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="flex space-x-2 overflow-x-auto no-scrollbar scroll-fade-mask py-0.5">
          <button
            onClick={() => setRarity('')}
            className={`px-4 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest whitespace-nowrap transition-all border ${
              rarity === ''
              ? 'bg-brand-accent text-brand-midnight border-brand-accent shadow-lg shadow-brand-accent/30 scale-105'
              : 'bg-white/5 text-slate-500 border-white/5'
            }`}
          >
            All Rarities
          </button>
          {availableRarities.map((r) => (
            <button 
              key={r}
              onClick={() => setRarity(r)}
              className={`px-4 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest whitespace-nowrap transition-all border ${
                rarity === r 
                ? 'bg-brand-accent text-brand-midnight border-brand-accent shadow-lg shadow-brand-accent/30 scale-105'
                : 'bg-white/5 text-slate-500 border-white/5'
              }`}
            >
              {r.split(' ')[1] || r}
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
                <div className="absolute inset-0 bg-brand-midnight/40 backdrop-blur-[1px] flex items-center justify-center rounded-[1.25rem] z-30 pointer-events-none">
                  <div className="bg-brand-accent/90 text-white px-2 py-0.5 rounded-full text-[7px] font-black uppercase tracking-widest shadow-lg flex items-center gap-1 border border-white/20">
                    <CheckCircle2 size={8} strokeWidth={4} />
                    <span>Collected</span>
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
          title="No results matched"
          message="Try adjusting your filters."
        />
      )}

      {loading && items.length > 0 && (
        <div className="flex justify-center py-8">
          <Loader2 size={14} className="animate-spin text-brand-accent" />
        </div>
      )}
    </div>
  );
};
