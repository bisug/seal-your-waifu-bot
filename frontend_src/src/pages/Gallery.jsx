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
      const data = await apiFetch(`/gallery?page=${currentPage}&limit=24&search=${search}&rarity=${rarity}`);
      
      if (isNew) {
        setItems(data.items);
      } else {
        setItems(prev => [...prev, ...data.items]);
      }
      
      setHasMore(data.items.length === 24);
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
    <div className="pb-32 pt-6 px-4">
      {/* Search & Filter Header */}
      <section className="mb-6 space-y-3">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
          <input 
            type="text" 
            placeholder="Search characters or anime..." 
            className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-4 text-sm focus:border-brand-neon outline-none transition-all placeholder:text-slate-600 font-medium"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        
        <ScrollArea>
           {['', 'Common', 'Rare', 'Epic', 'Legendary', 'Mythical', 'Celestial'].map((r) => (
            <button
              key={r}
              onClick={() => { setRarity(r); setPage(1); }}
              className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest whitespace-nowrap transition-all border ${
                rarity === r 
                ? 'bg-brand-neon text-brand-midnight border-brand-neon shadow-lg shadow-brand-neon/20' 
                : 'bg-white/5 text-slate-400 border-white/5 hover:border-white/10'
              }`}
            >
              {r || 'All Tiers'}
            </button>
          ))}
        </ScrollArea>
      </section>

      {/* Gallery Grid */}
      <section>
        <div className="grid grid-cols-2 xs:grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7 2xl:grid-cols-8 gap-3">
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
          </AnimatePresence>
          
          {loading && Array.from({ length: 8 }).map((_, i) => (
            <CardSkeleton key={`skeleton-${i}`} />
          ))}
        </div>


        {!loading && items.length === 0 && (
          <div className="py-20 text-center flex flex-col items-center">
            <Compass size={40} className="text-slate-800 mb-4" />
            <p className="text-slate-600 text-xs font-bold uppercase tracking-widest italic">No characters found</p>
          </div>
        )}
      </section>
    </div>
  );
};
