import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useUser } from '../context/UserContext';
import { apiFetch } from '../api/client';
import { ProgressBar } from '../components/ui/ProgressBar';
import { Card } from '../components/character/Card';
import { Skeleton, CardSkeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { Avatar } from '../components/Avatar';
import { Shield, Activity, Users, Trophy, Search, Loader2, Gauge } from 'lucide-react';
import { formatNumber } from '../utils';
import { useInfiniteGrid } from '../hooks/useInfiniteGrid';
import { Character } from '../context/UserContext';

interface ProfileProps {
  onCharClick: (character: Character) => void;
}

export const Profile = ({ onCharClick }: ProfileProps) => {
  const { user, loading: userLoading, liteMode, toggleLiteMode } = useUser();
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

  // Fetch available rarities once
  useEffect(() => {
    apiFetch('/rarities').then(setAvailableRarities).catch(console.error);
  }, []);

  if (userLoading && items.length === 0) return (
    <div className="pb-24 pt-6 px-6">
       <div className="h-64 mb-8">
          <Skeleton className="w-full h-full rounded-3xl" />
       </div>
       <div className="grid grid-cols-3 gap-3 mb-8">
          {[1,2,3].map(i => <Skeleton key={i} className="h-16 rounded-2xl" />)}
       </div>
       <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-2">
          {Array.from({ length: 9 }).map((_, i) => (
            <CardSkeleton key={`prof-skeleton-${i}`} />
          ))}
       </div>
    </div>
  );

  if (!user) return null;

  return (
    <div className="pb-28">
      {/* Premium Hero Section */}
      <section className="relative min-h-[11rem] overflow-hidden flex flex-col justify-end px-4 pb-5">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-brand-midnight/60 to-brand-midnight z-10" />
        <div className="absolute inset-0 bg-mesh opacity-30 z-0 scale-150 animate-pulse" />
        
        {/* Performance Toggle */}
        <div className="absolute top-4 right-4 z-30" style={{ paddingTop: 'env(safe-area-inset-top)' }}>
           <button 
             onClick={toggleLiteMode}
             className="bg-brand-midnight/60 backdrop-blur-md border border-white/10 px-3 py-1.5 rounded-full flex items-center space-x-1.5 active:scale-95 transition-all shadow-lg"
           >
             <Gauge size={12} className={liteMode ? "text-green-400" : "text-brand-accent"} />
             <span className="text-[10px] font-bold uppercase tracking-widest text-slate-300">
               {liteMode ? "Lite" : "Premium"}
             </span>
           </button>
        </div>
        <img 
          src={user.avatar || 'https://files.catbox.moe/2hsawz.jpg'} 
          className="absolute inset-0 w-full h-full object-cover opacity-40 blur-[8px] scale-125 transition-transform duration-[10s] hover:scale-150"
          alt="Profile Background"
        />
        
        <div className="relative z-20 flex items-center space-x-4">
          <div className="relative group">
            <div className="absolute inset-0 bg-brand-accent rounded-2xl blur-xl opacity-40 group-hover:opacity-60 transition-opacity duration-500 animate-pulse-ring" />
            <Avatar 
              src={user.avatar} 
              alt="User" 
              className="w-16 h-16 rounded-2xl border-2 border-brand-accent transform transition-transform duration-500 group-hover:scale-105 relative z-10 shadow-neon"
            />
            <div className="absolute -bottom-1.5 -right-1.5 bg-gradient-to-tr from-brand-accent to-brand-accent-secondary text-white text-xs font-black px-2.5 py-0.5 rounded-lg shadow-lg ring-2 ring-brand-midnight z-20 shadow-neon">
              LVL {user.stats?.level || 1}
            </div>
          </div>
          <div className="text-left">
            <h1 className="text-xl font-black uppercase tracking-tight leading-none mb-1 shadow-black/50 drop-shadow-lg text-white">
              {user.first_name || 'Collector'}
            </h1>
            <div className="flex items-center space-x-2">
              <span className="h-2 w-2 rounded-full bg-brand-accent shadow-neon" />
              <p className="text-xs font-bold text-slate-300 uppercase tracking-widest opacity-90">@{user.username || 'unknown'}</p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Dashboard */}
      <div className="px-4 -mt-4 relative z-30 grid grid-cols-3 gap-2.5 mb-8">
        {[
          { icon: Shield, label: 'XP', value: user.stats?.xp || 0, color: 'text-brand-accent', bg: 'bg-brand-accent/5' },
          { icon: Activity, label: 'Zenith ⧫', value: user.stats?.zenith || 0, color: 'text-brand-accent', bg: 'bg-brand-accent/5' },
          { icon: Users, label: 'Collection', value: user.stats?.total_characters || 0, color: 'text-white', bg: 'bg-white/5' },
        ].map((stat, i) => (
          <div key={i} className={`glass-panel p-3 rounded-2xl border border-white/10 flex flex-col items-center ${stat.bg} backdrop-blur-md`}>
            <div className={`${stat.color} mb-1.5 opacity-80`}>
              <stat.icon size={16} />
            </div>
            <span className="text-lg font-black tracking-tight">{formatNumber(stat.value)}</span>
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{stat.label}</span>
          </div>
        ))}
      </div>

      {/* Progress Section */}
      <section className="px-4 mb-6">
        <ProgressBar 
          current={user.stats?.xp_current || 0} 
          total={user.stats?.xp_needed || 1000} 
          label="Exp Progression"
        />
      </section>

      {/* Active Pet Section */}
      {user.current_pet && (
        <section className="px-4 mb-8">
          <div className="glass-panel p-4 rounded-3xl border border-white/5 relative overflow-hidden backdrop-blur-md">
            <div className="absolute top-0 right-0 w-32 h-32 bg-brand-accent/10 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />
            
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">Active Pet</h2>
              <span className="text-[10px] font-black text-brand-accent tracking-widest uppercase border border-brand-accent/20 bg-brand-accent/10 px-2.5 py-1 rounded-lg">
                {user.current_pet.mood}
              </span>
            </div>
            
            <div className="flex gap-4">
              <div className="w-16 h-16 shrink-0 rounded-2xl overflow-hidden border border-white/10 shadow-lg bg-black/40">
                <img src={user.current_pet.img} alt={user.current_pet.name} className="w-full h-full object-cover" />
              </div>
              
              <div className="flex-1 flex flex-col justify-center">
                <div className="flex justify-between items-start mb-1">
                  <h3 className="font-black text-white text-lg tracking-tight leading-none">{user.current_pet.name}</h3>
                  <span className="text-[11px] font-bold text-brand-accent-secondary bg-brand-accent-secondary/10 px-2 py-0.5 rounded-md border border-brand-accent-secondary/20">
                    LVL {user.current_pet.level}
                  </span>
                </div>
                
                <p className="text-[11px] text-slate-300 font-bold uppercase tracking-widest mb-2 flex items-center gap-1.5">
                  <Activity size={12} className="text-brand-accent" /> {user.current_pet.ability}
                </p>
                
                <div className="flex items-center gap-2 mb-3">
                  <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-brand-accent transition-all duration-1000 shadow-neon" 
                      style={{ width: `${Math.min(100, (user.current_pet.xp / user.current_pet.xp_needed) * 100)}%` }}
                    />
                  </div>
                  <span className="text-[10px] font-medium text-slate-400">
                    {user.current_pet.xp}/{user.current_pet.xp_needed}
                  </span>
                </div>

                <div className="flex gap-2 mt-1">
                   <button className="flex-1 py-2 bg-brand-accent/10 border border-brand-accent/20 rounded-xl text-[10px] font-black uppercase tracking-widest text-brand-accent hover:bg-brand-accent/20 active:scale-95 transition-all text-center shadow-neon">
                      Feed
                   </button>
                   <button className="flex-1 py-2 bg-white/5 border border-white/10 rounded-xl text-[10px] font-black uppercase tracking-widest text-white hover:bg-white/10 active:scale-95 transition-all text-center">
                      Play
                   </button>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Harem Grid Search & Header */}
      <section className="px-4">
        <div className="sticky-header px-4 py-3 -mx-4 mb-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-[11px] font-bold uppercase tracking-widest text-slate-400">My Harem</h2>
            <div className="flex items-center space-x-1 text-[11px] font-bold text-white uppercase tracking-widest bg-brand-accent-secondary/20 px-3 py-1.5 rounded-xl border border-brand-accent-secondary/30 shadow-neon">
              <Trophy size={12} className="text-brand-accent-secondary" />
              <span>Rank #{user.stats?.rank || '---'}</span>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex space-x-2 overflow-x-auto no-scrollbar py-0.5 scroll-fade-mask">
              <button 
                onClick={() => setRarity('')}
                className={`px-5 py-2.5 rounded-xl text-[11px] font-bold uppercase tracking-widest whitespace-nowrap transition-all border ${
                  rarity === '' 
                  ? 'bg-gradient-to-tr from-brand-accent to-brand-accent-secondary text-white border-brand-accent shadow-neon scale-105'
                  : 'bg-white/5 text-slate-400 border-white/5 hover:border-white/10'
                }`}
              >
                All Tiers
              </button>
              {availableRarities.map((r) => (
                <button 
                  key={r}
                  onClick={() => setRarity(r)}
                  className={`px-5 py-2.5 rounded-xl text-[11px] font-bold uppercase tracking-widest whitespace-nowrap transition-all border ${
                    rarity === r 
                    ? 'bg-gradient-to-tr from-brand-accent to-brand-accent-secondary text-white border-brand-accent shadow-neon scale-105'
                    : 'bg-white/5 text-slate-400 border-white/5 hover:border-white/10'
                  }`}
                >
                  {r.split(' ')[1] || r}
                </button>
              ))}
            </div>

            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-600" size={14} />
              <input 
                type="text" 
                placeholder="Search collection..." 
                className="w-full bg-slate-900/40 border border-white/10 rounded-xl py-3.5 pl-11 pr-4 text-sm focus:border-brand-accent outline-none transition-all placeholder:text-slate-500 font-medium tracking-wide backdrop-blur-sm"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
        </div>
        
        {items.length > 0 || (loading && page > 1) ? (
          <div className={`grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-2 transition-opacity duration-300 ${loading && page === 1 ? 'opacity-40 grayscale-[0.3]' : 'opacity-100'}`}>
             <AnimatePresence>
               {items.map((char, i) => (
                 <motion.div
                   key={char.id}
                   ref={i === items.length - 1 ? lastElementRef : null}
                   initial={{ opacity: 0, scale: 0.9, y: 10 }}
                   animate={{ opacity: 1, scale: 1, y: 0 }}
                   transition={{ delay: Math.min((i % 8) * 0.05, 0.4) }}
                 >
                   <Card 
                    character={char} 
                    onClick={onCharClick} 
                   />
                 </motion.div>
               ))}
             </AnimatePresence>
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
            title="No characters found in your harem."
            message="Try adjusting your search."
          />
        )}

        {/* Loading Spacing */}
        {loading && items.length > 0 && (
           <div className="flex justify-center py-8">
              <Loader2 className="animate-spin text-brand-accent/20" size={20} />
           </div>
        )}
      </section>
    </div>
  );
};
