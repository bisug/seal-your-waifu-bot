import React, { useState, useEffect } from 'react';
import { useUser } from '../context/UserContext';
import { apiFetch } from '../api/client';
import { ProgressBar } from '../components/ui/ProgressBar';
import { Card } from '../components/character/Card';
import { Skeleton, CardSkeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { Avatar } from '../components/Avatar';
import { Shield, Activity, Users, Trophy, Search, Loader2 } from 'lucide-react';
import { formatNumber } from '../utils';
import { useInfiniteGrid } from '../hooks/useInfiniteGrid';
import { Character } from '../context/UserContext';

interface ProfileProps {
  onCharClick: (character: Character) => void;
}

export const Profile = ({ onCharClick }: ProfileProps) => {
  const { user, loading: userLoading } = useUser();
  const {
    items,
    loading,
    page,
    search,
    setSearch,
    rarity,
    setRarity,
    lastElementRef
  } = useInfiniteGrid<Character>('/harem');
  
  const [availableRarities, setAvailableRarities] = useState<string[]>([]);

  useEffect(() => {
    apiFetch('/rarities').then(setAvailableRarities).catch(console.error);
  }, []);

  if (userLoading && items.length === 0) return (
    <div className="pb-24 pt-6 px-4">
       <div className="h-40 mb-6">
          <Skeleton className="w-full h-full rounded-xl" />
       </div>
       <div className="grid grid-cols-3 gap-3 mb-6">
          {[1,2,3].map(i => <Skeleton key={i} className="h-16 rounded-xl" />)}
       </div>
       <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 gap-2">
          {Array.from({ length: 9 }).map((_, i) => (
            <CardSkeleton key={`prof-skeleton-${i}`} />
          ))}
       </div>
    </div>
  );

  if (!user) return null;

  return (
    <div className="pb-20 pt-4">
      {/* Profile Header */}
      <section className="px-4 mb-8">
        <div className="flex items-center space-x-5 bg-zinc-900 border border-white/5 p-5 rounded-2xl">
          <div className="relative shrink-0">
            <Avatar 
              src={user.avatar} 
              alt="User" 
              className="w-16 h-16 rounded-xl border border-white/10"
            />
            <div className="absolute -bottom-1 -right-1 bg-brand-accent text-white text-[9px] font-bold px-1.5 py-0.5 rounded ring-4 ring-zinc-900">
              Lvl {user.stats?.level || 1}
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-lg font-bold text-white truncate tracking-tight mb-0.5">
              {user.first_name || 'Collector'}
            </h1>
            <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">@{user.username || 'unknown'}</p>
          </div>
          <div className="hidden xs:flex flex-col items-end">
            <div className="flex items-center space-x-1.5 text-[10px] font-bold text-zinc-300 bg-zinc-950 px-2.5 py-1.5 rounded-lg border border-white/5 uppercase tracking-widest">
              <Trophy size={12} className="text-amber-500" />
              <span>Rank #{user.stats?.rank || '---'}</span>
            </div>
          </div>
        </div>
      </section>

      {/* Primary Stats */}
      <div className="px-4 grid grid-cols-3 gap-3 mb-8">
        {[
          { icon: Shield, label: 'Experience', value: user.stats?.xp || 0, color: 'text-blue-500' },
          { icon: Activity, label: 'Zenith', value: user.stats?.zenith || 0, color: 'text-emerald-500' },
          { icon: Users, label: 'Collection', value: user.stats?.total_characters || 0, color: 'text-purple-500' },
        ].map((stat, i) => (
          <div key={i} className="bg-zinc-900/50 p-4 rounded-xl border border-white/5 flex flex-col">
            <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest mb-2">{stat.label}</span>
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-white tabular-nums tracking-tight">{formatNumber(stat.value)}</span>
              <stat.icon size={14} className={stat.color} />
            </div>
          </div>
        ))}
      </div>

      <section className="px-4 mb-10">
        <ProgressBar 
          current={user.stats?.xp_current || 0} 
          total={user.stats?.xp_needed || 1000} 
          label="Progress to next level"
        />
      </section>

      {/* Collection Filters */}
      <section className="px-4">
        <div className="sticky top-14 z-40 bg-zinc-950/80 backdrop-blur-md py-4 border-b border-white/5 mb-6 -mx-4 px-4">
          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-600" size={14} />
              <input
                type="text"
                placeholder="SEARCH COLLECTION..."
                className="w-full bg-zinc-900 border border-white/5 rounded-xl py-3 pl-10 pr-4 text-[10px] font-bold uppercase tracking-widest focus:border-white/20 outline-none transition-all placeholder:text-zinc-700"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <div className="flex space-x-2 overflow-x-auto no-scrollbar py-0.5">
              <button 
                onClick={() => setRarity('')}
                className={`px-4 py-2 rounded-lg text-[9px] font-bold uppercase tracking-widest transition-all border ${
                  rarity === '' 
                  ? 'bg-white text-zinc-950 border-white'
                  : 'bg-zinc-900 text-zinc-500 border-white/5 hover:border-white/10'
                }`}
              >
                All
              </button>
              {availableRarities.map((r) => (
                <button 
                  key={r}
                  onClick={() => setRarity(r)}
                  className={`px-4 py-2 rounded-lg text-[9px] font-bold uppercase tracking-widest whitespace-nowrap transition-all border ${
                    rarity === r 
                    ? 'bg-white text-zinc-950 border-white'
                    : 'bg-zinc-900 text-zinc-500 border-white/5 hover:border-white/10'
                  }`}
                >
                  {r.replace(/[\u2700-\u27bf]|[\u2190-\u21ff]|[\u2000-\u206f]|[\u2600-\u26ff]|[\u2b00-\u2bff]|[\u00a0-\u00bf]|\u2013|\u2014/g, '').trim()}
                </button>
              ))}
            </div>
          </div>
        </div>
        
        {items.length > 0 || (loading && page > 1) ? (
          <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-2">
               {items.map((char, i) => (
                 <Card
                  key={char.id}
                  ref={i === items.length - 1 ? lastElementRef : null}
                  character={char}
                  onClick={onCharClick}
                 />
               ))}
             {loading && page > 1 && Array.from({ length: 6 }).map((_, i) => (
                <CardSkeleton key={`loading-${i}`} />
             ))}
          </div>
        ) : loading && page === 1 ? (
          <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-2">
             {Array.from({ length: 18 }).map((_, i) => (
                <CardSkeleton key={`loading-new-${i}`} />
             ))}
          </div>
        ) : (
          <EmptyState
            icon={Users}
            title="Collection empty"
            message="Characters you collect will appear here."
          />
        )}

        {loading && items.length > 0 && (
           <div className="flex justify-center py-8">
              <Loader2 className="animate-spin text-zinc-800" size={20} />
           </div>
        )}
      </section>
    </div>
  );
};
