import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { apiFetch } from '../api';
import { Card } from '../components/UI';
import { Search, Loader2, Compass } from 'lucide-react';

export const Gallery = ({ onCharClick }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [rarity, setRarity] = useState('');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

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
      setPage(currentPage + 1);
    } catch (err) {
      console.error('Gallery fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [search, rarity, page]);

  // Initial fetch and filter reset
  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      fetchGallery(true);
    }, 400);

    return () => clearTimeout(delayDebounceFn);
  }, [search, rarity]);

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
        
        <div className="flex space-x-2 overflow-x-auto no-scrollbar pb-1">
          {['', 'Common', 'Rare', 'Epic', 'Legendary', 'Mythical', 'Celestial'].map((r) => (
            <button
              key={r}
              onClick={() => { setRarity(r); setPage(1); }}
              className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest whitespace-nowrap transition-all border ${
                rarity === r 
                ? 'bg-brand-neon text-brand-midnight border-brand-neon' 
                : 'bg-white/5 text-slate-400 border-white/5'
              }`}
            >
              {r || 'All Tiers'}
            </button>
          ))}
        </div>
      </section>

      {/* Gallery Grid */}
      <section>
        <div className="grid grid-cols-2 xs:grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7 2xl:grid-cols-8 gap-3">
          {items.map((char, i) => (
            <motion.div
              key={`${char.id}-${i}`}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: (i % 8) * 0.05 }}
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
        </div>

        {loading && (
          <div className="flex justify-center py-12">
            <Loader2 className="text-brand-neon animate-spin" size={24} />
          </div>
        )}

        {!loading && hasMore && (
          <button 
            onClick={() => fetchGallery()}
            className="w-full mt-8 py-4 rounded-2xl border border-white/5 bg-white/5 text-[10px] font-black uppercase tracking-[0.3em] text-slate-500 hover:text-white transition-colors"
          >
            Load More Characters
          </button>
        )}

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
