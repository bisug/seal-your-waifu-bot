import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useUser } from '../context/UserContext';
import { apiFetch } from '../api';
import { ProgressBar, Card, Skeleton, CardSkeleton } from '../components/UI';
import { Shield, Zap, Users, Trophy, Search, Loader2 } from 'lucide-react';
import { formatNumber } from '../utils';

export const Profile = ({ onCharClick }) => {
  const { user, loading: userLoading } = useUser();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [search, setSearch] = useState('');
  
  const observer = useRef();
  const lastElementRef = useCallback(node => {
    if (loading) return;
    if (observer.current) observer.current.disconnect();
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore) {
        setPage(prev => prev + 1);
      }
    });
    if (node) observer.current.observe(node);
  }, [loading, hasMore]);

  const fetchHarem = useCallback(async (isNew = false) => {
    setLoading(true);
    try {
      const currentPage = isNew ? 1 : page;
      // Note: Backend /harem already handles grouping/counting duplicates
      const data = await apiFetch(`/harem?page=${currentPage}&limit=24&search=${encodeURIComponent(search)}`);
      
      if (isNew) {
        setItems(data.items);
      } else {
        setItems(prev => [...prev, ...data.items]);
      }
      
      setHasMore((isNew ? data.items.length : items.length + data.items.length) < data.total);
    } catch (err) {
      console.error('Harem fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  // Initial fetch and search debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1);
      fetchHarem(true);
    }, 400);
    return () => clearTimeout(timer);
  }, [search]);

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
       <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2">
          {Array.from({ length: 9 }).map((_, i) => (
            <CardSkeleton key={`prof-skeleton-${i}`} />
          ))}
       </div>
    </div>
  );

  if (!user) return null;

  return (
    <div className="pb-8">
      {/* Premium Hero Section */}
      <section className="relative h-44 overflow-hidden flex flex-col justify-end px-4 pb-5">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-brand-midnight/60 to-brand-midnight z-10" />
        <div className="absolute inset-0 bg-mesh opacity-30 z-0 scale-150 animate-pulse" />
        <img 
          src={user.avatar || 'https://files.catbox.moe/2hsawz.jpg'} 
          className="absolute inset-0 w-full h-full object-cover opacity-40 blur-[4px] scale-110"
          alt="Profile Background"
        />
        
        <div className="relative z-20 flex items-center space-x-4">
          <div className="relative group">
            <div className="w-16 h-16 rounded-2xl overflow-hidden border-2 border-brand-neon neon-shadow bg-brand-midnight transform transition-transform group-hover:scale-105">
              <img src={user.avatar || 'https://files.catbox.moe/2hsawz.jpg'} className="w-full h-full object-cover" alt="User" />
            </div>
            <div className="absolute -bottom-1.5 -right-1.5 bg-brand-neon text-brand-midnight text-[10px] font-black px-2 py-0.5 rounded-md shadow-lg shadow-brand-neon/40 ring-2 ring-brand-midnight">
              LVL {user.stats?.level || 1}
            </div>
          </div>
          <div className="text-left">
            <h1 className="text-xl font-black uppercase tracking-tight leading-none mb-1 shadow-black/50 drop-shadow-lg text-white">
              {user.first_name || 'Collector'}
            </h1>
            <div className="flex items-center space-x-2">
              <span className="h-1.5 w-1.5 rounded-full bg-brand-neon animate-pulse" />
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.25em] opacity-90">@{user.username || 'unknown'}</p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Dashboard */}
      <div className="px-4 -mt-4 relative z-30 grid grid-cols-3 gap-2.5 mb-8">
        {[
          { icon: Shield, label: 'XP', value: user.stats?.xp || 0, color: 'text-brand-neon', bg: 'bg-brand-neon/5' },
          { icon: Zap, label: 'Zenith ⧫', value: user.stats?.zenith || 0, color: 'text-brand-accent', bg: 'bg-brand-accent/5' },
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
      <section className="px-4 mb-8">
        <ProgressBar 
          current={user.stats?.xp_current || 0} 
          total={user.stats?.xp_needed || 1000} 
          label="Exp Progression"
        />
      </section>

      {/* Harem Grid Search & Header */}
      <section className="px-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-[10px] font-black uppercase tracking-widest text-slate-500">My Harem</h2>
          <div className="flex items-center space-x-1 text-[10px] font-black text-brand-neon uppercase tracking-widest bg-brand-neon/5 px-2.5 py-1 rounded-lg border border-brand-neon/10 shadow-[0_0_10px_rgba(0,255,255,0.05)]">
            <Trophy size={10} />
            <span>Rank #{user.stats?.rank || '---'}</span>
          </div>
        </div>

        <div className="relative mb-6">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={14} />
          <input 
            type="text" 
            placeholder="Search your harem..." 
            className="w-full bg-slate-900/40 border border-white/10 rounded-xl py-3 pl-11 pr-4 text-xs focus:border-brand-neon/50 outline-none transition-all placeholder:text-slate-600 font-bold uppercase tracking-widest backdrop-blur-sm"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        
        {items.length > 0 || loading ? (
          <div className="grid grid-cols-2 xs:grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2">
             <AnimatePresence mode="popLayout">
               {items.map((char, i) => (
                 <motion.div
                   key={`${char.id}-${i}`}
                   ref={i === items.length - 1 ? lastElementRef : null}
                   layout
                   initial={{ opacity: 0, scale: 0.9, y: 10 }}
                   animate={{ opacity: 1, scale: 1, y: 0 }}
                   transition={{ delay: (i % 8) * 0.05 }}
                 >
                   <Card 
                    character={char} 
                    onClick={() => onCharClick(char)} 
                   />
                 </motion.div>
               ))}
             </AnimatePresence>
             {loading && Array.from({ length: 6 }).map((_, i) => (
                <CardSkeleton key={`loading-${i}`} />
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
              <Loader2 className="animate-spin text-brand-neon/20" size={20} />
           </div>
        )}
      </section>
    </div>
  );
};
