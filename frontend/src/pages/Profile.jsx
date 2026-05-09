import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useUser } from '../context/UserContext';
import { apiFetch } from '../api';
import { ProgressBar, Card, Skeleton, CardSkeleton } from '../components/UI';
import { Avatar } from '../components/Avatar';
import { Shield, Activity, Users, Trophy, Search, Loader2 } from 'lucide-react';
import { formatNumber } from '../utils';

export const Profile = ({ onCharClick }) => {
  const { user, loading: userLoading } = useUser();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [search, setSearch] = useState('');
  const [rarity, setRarity] = useState('');
  const [availableRarities, setAvailableRarities] = useState([]);
  
  const observer = useRef();
  const searchAbortController = useRef(null);

  const lastElementRef = useCallback(node => {
    if (loading) return;
    if (observer.current) observer.current.disconnect();
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore && !loading) {
        setPage(prev => prev + 1);
      }
    });
    if (node) observer.current.observe(node);
  }, [loading, hasMore]);

  const fetchHarem = useCallback(async (isNew = false) => {
    setLoading(true);
    
    if (isNew) {
      if (searchAbortController.current) {
        searchAbortController.current.abort();
      }
      searchAbortController.current = new AbortController();
    }
    
    try {
      const currentPage = isNew ? 1 : page;
      const data = await apiFetch(
        `/harem?page=${currentPage}&limit=24&search=${encodeURIComponent(search)}&rarity=${encodeURIComponent(rarity)}`,
        { signal: searchAbortController.current?.signal }
      );
      
      if (isNew) {
        setItems(data.items);
      } else {
        setItems(prev => [...prev, ...data.items]);
      }
      
      setHasMore(data.items.length === 24);
    } catch (err) {
      if (err.name === 'AbortError') return; // Ignore aborted requests
      console.error('Harem fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [page, search, rarity]);

  // Initial fetch and search/rarity debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1);
      fetchHarem(true);
    }, 400);
    return () => clearTimeout(timer);
  }, [search, rarity]);

  // Fetch available rarities once
  useEffect(() => {
    apiFetch('/rarities').then(setAvailableRarities).catch(console.error);
  }, []);

  // Infinite scroll trigger
  useEffect(() => {
    if (page > 1) {
      fetchHarem(false);
    }
  }, [page]);

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
        <img 
          src={user.avatar || 'https://files.catbox.moe/2hsawz.jpg'} 
          className="absolute inset-0 w-full h-full object-cover opacity-40 blur-[4px] scale-110"
          alt="Profile Background"
        />
        
        <div className="relative z-20 flex items-center space-x-4">
          <div className="relative group">
            <Avatar 
              src={user.avatar} 
              alt="User" 
              className="w-16 h-16 rounded-2xl border-2 border-brand-accent transform transition-transform group-hover:scale-105"
            />
            <div className="absolute -bottom-1.5 -right-1.5 bg-brand-accent text-white text-[10px] font-black px-2 py-0.5 rounded-md shadow-lg ring-2 ring-brand-midnight">
              LVL {user.stats?.level || 1}
            </div>
          </div>
          <div className="text-left">
            <h1 className="text-xl font-black uppercase tracking-tight leading-none mb-1 shadow-black/50 drop-shadow-lg text-white">
              {user.first_name || 'Collector'}
            </h1>
            <div className="flex items-center space-x-2">
              <span className="h-1.5 w-1.5 rounded-full bg-brand-accent" />
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.25em] opacity-90">@{user.username || 'unknown'}</p>
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
            <span className="text-[13px] font-black tracking-tight">{formatNumber(stat.value)}</span>
            <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">{stat.label}</span>
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
              <h2 className="text-[10px] font-black uppercase tracking-widest text-slate-500">Active Pet</h2>
              <span className="text-[9px] font-black text-brand-accent tracking-widest uppercase border border-brand-accent/20 bg-brand-accent/5 px-2 py-0.5 rounded-lg">
                {user.current_pet.mood}
              </span>
            </div>
            
            <div className="flex gap-4">
              <div className="w-16 h-16 shrink-0 rounded-2xl overflow-hidden border border-white/10 shadow-lg bg-black/40">
                <img src={user.current_pet.img} alt={user.current_pet.name} className="w-full h-full object-cover" />
              </div>
              
              <div className="flex-1 flex flex-col justify-center">
                <div className="flex justify-between items-start mb-1">
                  <h3 className="font-black text-white text-base tracking-tight leading-none">{user.current_pet.name}</h3>
                  <span className="text-[10px] font-black text-slate-300">
                    LVL {user.current_pet.level}
                  </span>
                </div>
                
                <p className="text-[9px] text-slate-400 font-bold uppercase tracking-widest mb-2 flex items-center gap-1.5">
                  <Activity size={10} className="text-brand-accent" /> {user.current_pet.ability}
                </p>
                
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-brand-accent transition-all duration-1000" 
                      style={{ width: `${Math.min(100, (user.current_pet.xp / user.current_pet.xp_needed) * 100)}%` }}
                    />
                  </div>
                  <span className="text-[9px] font-mono text-slate-500">
                    {user.current_pet.xp}/{user.current_pet.xp_needed}
                  </span>
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
            <h2 className="text-[10px] font-black uppercase tracking-widest text-slate-500">My Harem</h2>
            <div className="flex items-center space-x-1 text-[10px] font-black text-brand-accent uppercase tracking-widest bg-brand-accent/5 px-2.5 py-1 rounded-lg border border-brand-accent/10">
              <Trophy size={10} />
              <span>Rank #{user.stats?.rank || '---'}</span>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex space-x-2 overflow-x-auto no-scrollbar py-0.5 scroll-fade-mask">
              <button 
                onClick={() => { setRarity(''); setPage(1); }}
                className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-[0.15em] whitespace-nowrap transition-all border ${
                  rarity === '' 
                  ? 'bg-brand-accent text-white border-brand-accent shadow-lg scale-105'
                  : 'bg-white/5 text-slate-500 border-white/5 hover:border-white/10'
                }`}
              >
                All Tiers
              </button>
              {availableRarities.map((r) => (
                <button 
                  key={r}
                  onClick={() => { setRarity(r); setPage(1); }}
                  className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-[0.15em] whitespace-nowrap transition-all border ${
                    rarity === r 
                    ? 'bg-brand-accent text-white border-brand-accent shadow-lg scale-105'
                    : 'bg-white/5 text-slate-500 border-white/5 hover:border-white/10'
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
                className="w-full bg-slate-900/40 border border-white/10 rounded-xl py-3 pl-11 pr-4 text-[11px] focus:border-brand-accent/50 outline-none transition-all placeholder:text-slate-600 font-bold tracking-widest backdrop-blur-sm"
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
                   key={`${char.id}-${i}`}
                   ref={i === items.length - 1 ? lastElementRef : null}
                   initial={{ opacity: 0, scale: 0.9, y: 10 }}
                   animate={{ opacity: 1, scale: 1, y: 0 }}
                   transition={{ delay: Math.min((i % 8) * 0.05, 0.4) }}
                 >
                   <Card 
                    character={char} 
                    onClick={() => onCharClick(char)} 
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
          <div className="glass-panel p-10 rounded-3xl border border-white/5 text-center flex flex-col items-center opacity-80">
            <Users size={40} className="text-slate-800 mb-4" />
            <p className="text-slate-500 text-[11px] font-bold uppercase tracking-widest italic leading-relaxed">
              No characters found in your harem.<br/>Try adjusting your search.
            </p>
          </div>
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
