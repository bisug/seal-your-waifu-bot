import React, { useState, useEffect } from 'react';
import { useUser } from '../context/UserContext';
import { apiFetch } from '../api/client';
import { ProgressBar } from '../components/ui/ProgressBar';
import { Card } from '../components/character/Card';
import { Skeleton, CardSkeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { Avatar } from '../components/Avatar';
import { Shield, Activity, Users, Trophy, Search, Loader2 } from 'lucide-react';
import { formatNumber, cn } from '../utils';
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
       <div className="h-28 mb-6">
          <Skeleton className="w-full h-full rounded-2xl" />
       </div>
       <div className="grid grid-cols-3 gap-3 mb-6">
          {[1,2,3].map(i => <Skeleton key={i} className="h-20 rounded-xl" />)}
       </div>
       <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 gap-3">
          {Array.from({ length: 9 }).map((_, i) => (
            <CardSkeleton key={`prof-skeleton-${i}`} />
          ))}
       </div>
    </div>
  );

  if (!user) return null;

  return (
    <div className="pb-20 pt-4 max-w-4xl mx-auto">
      {/* Profile Header */}
      <section className="px-4 mb-6">
        <div className="flex items-center space-x-4 bg-brand-deep border border-white/5 p-4 rounded-2xl shadow-sm">
          <div className="relative shrink-0">
            <Avatar 
              src={user.avatar} 
              alt="User" 
              className="w-16 h-16 rounded-xl border border-white/10"
            />
            <div className="absolute -bottom-2 -right-2 bg-brand-accent text-white text-xs font-bold px-2 py-0.5 rounded-lg border-2 border-brand-deep">
              Lvl {user.stats?.level || 1}
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-lg font-bold text-white truncate tracking-tight mb-0.5">
              {user.first_name || 'Collector'}
            </h1>
            <p className="text-sm text-neutral-400 font-medium">@{user.username || 'unknown'}</p>
          </div>
          <div className="hidden sm:flex flex-col items-end">
            <div className="flex items-center space-x-2 text-sm font-semibold text-neutral-300 bg-brand-midnight px-3 py-1.5 rounded-lg border border-white/5 shadow-sm">
              <Trophy size={16} className="text-amber-500" />
              <span>Rank #{formatNumber(user.stats?.rank || 0)}</span>
            </div>
          </div>
        </div>
      </section>

      {/* Primary Stats */}
      <div className="px-4 grid grid-cols-3 gap-3 mb-6">
        {[
          { icon: Shield, label: 'XP', value: user.stats?.xp || 0, color: 'text-brand-accent' },
          { icon: Activity, label: 'Zenith', value: user.stats?.zenith || 0, color: 'text-emerald-500' },
          { icon: Users, label: 'Collection', value: user.stats?.total_characters || 0, color: 'text-purple-500' },
        ].map((stat, i) => (
          <div key={i} className="bg-brand-deep p-4 rounded-xl border border-white/5 flex flex-col justify-between shadow-sm">
            <span className="text-xs font-medium text-neutral-500 mb-2">{stat.label}</span>
            <div className="flex items-center justify-between">
              <span className="text-base font-bold text-white tabular-nums">{formatNumber(stat.value)}</span>
              <stat.icon size={16} className={stat.color} />
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

      {/* Collection Filters */}
      <section className="px-4">
        <div className="sticky top-14 z-40 bg-brand-midnight/90 backdrop-blur-md py-4 border-b border-white/5 mb-6 -mx-4 px-4 shadow-sm">
          <div className="space-y-4">
            <div className="relative max-w-md mx-auto sm:mx-0">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-500" size={16} />
              <input
                type="text"
                placeholder="Search collection..."
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
                All
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
        </div>
        
        {items.length > 0 || (loading && page > 1) ? (
          <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-7 gap-3">
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
          <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-7 gap-3">
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
              <Loader2 className="animate-spin text-neutral-600" size={24} />
           </div>
        )}
      </section>
    </div>
  );
};
