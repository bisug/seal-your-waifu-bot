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
          <Skeleton className="w-full h-full rounded-lg" />
       </div>
       <div className="grid grid-cols-3 gap-2 mb-6">
          {[1,2,3].map(i => <Skeleton key={i} className="h-14 rounded-lg" />)}
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
    <div className="pb-10 pt-4">
      {/* Refined Header */}
      <section className="px-4 mb-6">
        <div className="flex items-center space-x-4 bg-zinc-900 border border-white/5 p-4 rounded-lg shadow-sm">
          <div className="relative shrink-0">
            <Avatar 
              src={user.avatar} 
              alt="User" 
              className="w-14 h-14 rounded-lg border border-white/10"
            />
            <div className="absolute -bottom-1 -right-1 bg-brand-accent text-white text-[10px] font-bold px-1.5 py-0.5 rounded shadow-sm ring-2 ring-zinc-900">
              {user.stats?.level || 1}
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-base font-bold text-zinc-100 truncate">
              {user.first_name || 'Collector'}
            </h1>
            <p className="text-xs text-zinc-500 font-medium tracking-tight">@{user.username || 'unknown'}</p>
          </div>
          <div className="hidden xs:flex flex-col items-end">
            <div className="flex items-center space-x-1.5 text-xs font-semibold text-zinc-300 bg-zinc-950 px-2 py-1 rounded border border-white/5">
              <Trophy size={12} className="text-amber-500" />
              <span>#{user.stats?.rank || '---'}</span>
            </div>
          </div>
        </div>
      </section>

      {/* Stats - Grid refined */}
      <div className="px-4 grid grid-cols-3 gap-3 mb-6">
        {[
          { icon: Shield, label: 'XP', value: user.stats?.xp || 0, color: 'text-blue-500' },
          { icon: Activity, label: 'Zenith', value: user.stats?.zenith || 0, color: 'text-emerald-500' },
          { icon: Users, label: 'Owned', value: user.stats?.total_characters || 0, color: 'text-purple-500' },
        ].map((stat, i) => (
          <div key={i} className="bg-zinc-900/50 p-3 rounded-lg border border-white/5 flex flex-col">
            <span className="text-xs font-medium text-zinc-500 mb-1">{stat.label}</span>
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-zinc-100 tabular-nums">{formatNumber(stat.value)}</span>
              <stat.icon size={12} className={stat.color} />
            </div>
          </div>
        ))}
      </div>

      <section className="px-4 mb-8">
        <ProgressBar 
          current={user.stats?.xp_current || 0} 
          total={user.stats?.xp_needed || 1000} 
          label="Progress to next level"
        />
      </section>

      {/* Content Area */}
      <section className="px-4">
        <div className="sticky top-14 z-40 bg-brand-midnight py-4 border-b border-white/5 mb-4 -mx-4 px-4">
          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500" size={14} />
              <input
                type="text"
                placeholder="Search collection..."
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
                  ? 'bg-zinc-100 text-zinc-950 border-zinc-100'
                  : 'bg-zinc-900 text-zinc-400 border-white/5 hover:border-zinc-700'
                }`}
              >
                All
              </button>
              {availableRarities.map((r) => (
                <button 
                  key={r}
                  onClick={() => setRarity(r)}
                  className={`px-3 py-1.5 rounded text-xs font-medium whitespace-nowrap transition-all border ${
                    rarity === r 
                    ? 'bg-zinc-100 text-zinc-950 border-zinc-100'
                    : 'bg-zinc-900 text-zinc-400 border-white/5 hover:border-zinc-700'
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
           <div className="flex justify-center py-6">
              <Loader2 className="animate-spin text-zinc-800" size={20} />
           </div>
        )}
      </section>
    </div>
  );
};
