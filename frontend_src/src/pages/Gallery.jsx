import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { apiFetch } from '../api';
import { Card, ScrollArea, CardSkeleton } from '../components/UI';
import { Search, Loader2, Compass } from 'lucide-react';

export const Gallery = ({ onCharClick }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [rarity, setRarity] = useState('');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

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

  const fetchGallery = useCallback(async (isNew = false) => {
    setLoading(true);
    try {
      const currentPage = isNew ? 1 : page;
      const data = await apiFetch(`/gallery?page=${currentPage}&limit=24&search=${encodeURIComponent(search)}&rarity=${encodeURIComponent(rarity)}`);
      
      if (isNew) {
        setItems(data.items);
      } else {
        setItems(prev => [...prev, ...data.items]);
      }
      
      setHasMore((isNew ? data.items.length : items.length + data.items.length) < data.total);
    } catch (err) {
      console.error('Gallery fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [search, rarity, page]);

  // Initial fetch and filter reset
  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      setPage(1);
      fetchGallery(true);
    }, 400);

    return () => clearTimeout(delayDebounceFn);
  }, [search, rarity]);

  // Infinite scroll trigger
  useEffect(() => {
    if (page > 1) {
      fetchGallery(false);
    }
  }, [page]);

  return (
    <div className="pb-8 pt-0 px-4 relative min-h-full">
      {/* Premium Search & Filter Header */}
      <section className="sticky top-0 z-30 bg-brand-midnight/80 backdrop-blur-xl pt-4 pb-3 mb-5 -mx-4 px-4 space-y-3 border-b border-white/5 shadow-2xl">
        <div className="relative group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-brand-neon transition-colors" size={14} />
          <input 
            type="text" 
            placeholder="Search characters or anime..." 
            className="w-full bg-slate-900/40 border border-white/10 rounded-xl py-3 pl-11 pr-4 text-xs focus:border-brand-neon/50 outline-none transition-all placeholder:text-slate-600 font-bold tracking-tight backdrop-blur-sm"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        
        <ScrollArea>
           {['', 'Common', 'Medium', 'Rare', 'Legendary', 'Cosmic', 'Exclusive', 'Limited Edition', 'Royal', 'Antique', 'Celestial'].map((r) => (
            <button 
              key={r}
              onClick={() => { setRarity(r); setPage(1); }}
              className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-[0.15em] whitespace-nowrap transition-all border ${
                rarity === r 
                ? 'bg-brand-neon text-brand-midnight border-brand-neon shadow-lg shadow-brand-neon/30 scale-105' 
                : 'bg-white/5 text-slate-500 border-white/5 hover:border-white/10'
              }`}
            >
              {r || 'All Tiers'}
            </button>
          ))}
        </ScrollArea>
      </section>

      {/* Gallery Grid */}
      <section>
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2">
          <AnimatePresence mode="popLayout">
            {items.map((char, i) => (
              <motion.div
                key={`${char.id}-${i}`}
                ref={i === items.length - 1 ? lastElementRef : null}
                layout
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{ 
                  duration: 0.4,
                  delay: (i % 8) * 0.05,
                  ease: "easeOut"
                }}
                className="relative"
              >
                <Card character={char} onClick={() => onCharClick(char)} />
                {char.owned && (
                  <div className="absolute top-1.5 right-1.5 bg-brand-neon text-brand-midnight rounded-full p-0.5 shadow-lg border border-brand-midnight z-10 scale-75">
                    <div className="w-2 h-2 rounded-full bg-brand-midnight animate-pulse" />
                  </div>
                )}
              </motion.div>
            ))}
            
            {loading && items.length === 0 && Array.from({ length: 12 }).map((_, i) => (
              <motion.div
                key={`skeleton-${i}`}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <CardSkeleton />
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Status Indicators */}
        <div className="mt-10 mb-6 flex flex-col items-center justify-center">
          {loading && items.length > 0 && (
            <div className="flex items-center space-x-3 bg-white/5 px-6 py-3 rounded-2xl border border-white/10 animate-pulse">
              <Loader2 size={14} className="animate-spin text-brand-neon" />
              <span className="text-[11px] font-black text-slate-500 uppercase tracking-[0.2em]">Loading Harem Data...</span>
            </div>
          )}

          {!hasMore && items.length > 0 && (
            <div className="flex flex-col items-center space-y-2 opacity-30">
              <div className="h-px w-24 bg-gradient-to-r from-transparent via-slate-700 to-transparent mb-2" />
              <span className="text-[11px] font-black text-slate-600 uppercase tracking-[0.3em]">End of Harem List</span>
            </div>
          )}

          {!loading && items.length === 0 && (
            <div className="py-20 text-center flex flex-col items-center">
              <Compass size={40} className="text-slate-800 mb-4" />
              <p className="text-slate-600 text-xs font-bold uppercase tracking-widest italic">No characters found</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};
