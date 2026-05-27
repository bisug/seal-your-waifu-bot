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
          <Skeleton className="w-full h-full rounded-2xl" />
       </div>
       <div className="grid grid-cols-3 gap-2 mb-6">
          {[1,2,3].map(i => <Skeleton key={i} className="h-14 rounded-xl" />)}
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
    <div className="pb-28 pt-4">
      {/* Professional Compact Header */}
      <section className="px-4 mb-6">
        <div className="flex items-center space-x-4 bg-white/5 p-4 rounded-2xl border border-white/5">
          <div className="relative shrink-0">
            <Avatar 
              src={user.avatar} 
              alt="User" 
              className="w-14 h-14 rounded-xl border border-white/10"
            />
            <div className="absolute -bottom-1 -right-1 bg-brand-accent text-white text-[9px] font-black px-1.5 py-0.5 rounded shadow-lg ring-1 ring-brand-midnight">
              L{user.stats?.level || 1}
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-lg font-bold text-white truncate leading-tight">
              {user.first_name || 'Collector'}
            </h1>
            <p className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">@{user.username || 'unknown'}</p>
          </div>
          <div className="flex flex-col items-end">
            <div className="flex items-center space-x-1 text-[10px] font-bold text-white uppercase tracking-wider bg-white/5 px-2 py-1 rounded-lg border border-white/5">
              <Trophy size={10} className="text-brand-accent" />
              <span>#{user.stats?.rank || '---'}</span>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Dashboard - Compact */}
      <div className="px-4 grid grid-cols-3 gap-2 mb-6">
        {[
          { icon: Shield, label: 'XP', value: user.stats?.xp || 0 },
          { icon: Activity, label: 'Zenith', value: user.stats?.zenith || 0 },
          { icon: Users, label: 'Owned', value: user.stats?.total_characters || 0 },
        ].map((stat, i) => (
          <div key={i} className="bg-white/5 p-2.5 rounded-xl border border-white/5 flex flex-col items-center">
            <span className="text-sm font-bold text-white">{formatNumber(stat.value)}</span>
            <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">{stat.label}</span>
          </div>
        ))}
      </div>

      {/* Progress Section */}
      <section className="px-4 mb-8">
        <ProgressBar 
          current={user.stats?.xp_current || 0} 
          total={user.stats?.xp_needed || 1000} 
          label="Level Progress"
        />
      </section>

      {/* Harem Grid Search & Header */}
      <section className="px-4">
        <div className="sticky-header py-3 mb-4 bg-brand-midnight">
          <div className="space-y-3">
            <div className="flex space-x-2 overflow-x-auto no-scrollbar py-0.5 scroll-fade-mask">
              <button 
                onClick={() => setRarity('')}
                className={`px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-widest whitespace-nowrap transition-all border ${
                  rarity === '' 
                  ? 'bg-brand-accent text-white border-brand-accent'
                  : 'bg-white/5 text-slate-500 border-white/5 hover:border-white/10'
                }`}
              >
                All
              </button>
              {availableRarities.map((r) => (
                <button 
                  key={r}
                  onClick={() => setRarity(r)}
                  className={`px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-widest whitespace-nowrap transition-all border ${
                    rarity === r 
                    ? 'bg-brand-accent text-white border-brand-accent'
                    : 'bg-white/5 text-slate-500 border-white/5 hover:border-white/10'
                  }`}
                >
                  {r.split(' ')[1] || r}
                </button>
              ))}
            </div>

            <div className="relative">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-600" size={14} />
              <input 
                type="text" 
                placeholder="Search harem..."
                className="w-full bg-white/5 border border-white/5 rounded-xl py-3 pl-10 pr-4 text-xs focus:border-brand-accent/50 outline-none transition-all placeholder:text-slate-600 font-medium"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
        </div>
        
        {items.length > 0 || (loading && page > 1) ? (
          <div className={`grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-2 transition-opacity duration-200 ${loading && page === 1 ? 'opacity-50' : 'opacity-100'}`}>
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
            title="No characters found"
            message="Try adjusting your search."
          />
        )}

        {loading && items.length > 0 && (
           <div className="flex justify-center py-6">
              <Loader2 className="animate-spin text-brand-accent/30" size={18} />
           </div>
        )}
      </section>
    </div>
  );
};
