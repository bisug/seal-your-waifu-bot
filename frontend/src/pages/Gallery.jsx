import React, { useState, useEffect, useCallback, useRef } from 'react';
import { AnimatePresence } from 'framer-motion';
import { apiFetch } from '../api';
import { Card, Skeleton, CardSkeleton } from '../components/UI';
import { Search, Loader2, Users, CheckCircle2 } from 'lucide-react';

export const Gallery = () => {
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

  const fetchGallery = useCallback(async (isNew = false) => {
    setLoading(true);
    if (isNew) {
      if (searchAbortController.current) searchAbortController.current.abort();
      searchAbortController.current = new AbortController();
    }

    try {
      const currentPage = isNew ? 1 : page;
      const data = await apiFetch(
        `/gallery?page=${currentPage}&limit=24&search=${encodeURIComponent(search)}&rarity=${encodeURIComponent(rarity)}`,
        { signal: searchAbortController.current?.signal }
      );
      
      if (isNew) {
        setItems(data.items);
      } else {
        setItems(prev => [...prev, ...data.items]);
      }
      setHasMore(data.items.length === 24);
    } catch (err) {
      if (err.name === 'AbortError') return;
      console.error('Gallery fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [page, search, rarity]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1);
      fetchGallery(true);
    }, 400);
    return () => clearTimeout(timer);
  }, [search, rarity]);

  useEffect(() => {
    apiFetch('/rarities').then(setAvailableRarities).catch(console.error);
  }, []);

  useEffect(() => {
    let mounted = true;
    if (page > 1 && mounted) {
      Promise.resolve().then(() => {
        if (mounted) fetchGallery(false);
      });
    }
    return () => { mounted = false; };
  }, [page, fetchGallery]);

  return (
    <div className="pb-32 pt-0 px-4 relative ">
      <div className="sticky top-0 z-40 bg-brand-midnight/80 backdrop-blur-xl -mx-4 px-4 py-4 border-b border-white/5 mb-6">
        <div className="relative group mb-4">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-brand-accent transition-colors" size={14} />
          <input 
            type="text" 
            placeholder="Search characters or anime..." 
            className="w-full bg-slate-900/40 border border-white/10 rounded-xl py-3 pl-11 pr-4 text-xs focus:border-brand-accent/50 outline-none transition-all placeholder:text-slate-600 font-bold tracking-tight backdrop-blur-sm"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="flex space-x-2 overflow-x-auto no-scrollbar scroll-fade-mask py-0.5">
          <button
            onClick={() => { setRarity(''); setPage(1); }}
            className={`px-4 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest whitespace-nowrap transition-all border ${
              rarity === ''
              ? 'bg-brand-accent text-brand-midnight border-brand-accent shadow-lg shadow-brand-accent/30 scale-105'
              : 'bg-white/5 text-slate-500 border-white/5'
            }`}
          >
            All Rarities
          </button>
          {availableRarities.map((r) => (
            <button 
              key={r}
              onClick={() => { setRarity(r); setPage(1); }}
              className={`px-4 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest whitespace-nowrap transition-all border ${
                rarity === r 
                ? 'bg-brand-accent text-brand-midnight border-brand-accent shadow-lg shadow-brand-accent/30 scale-105'
                : 'bg-white/5 text-slate-500 border-white/5'
              }`}
            >
              {r.split(' ')[1] || r}
            </button>
          ))}
        </div>
      </div>

      {items.length > 0 ? (
        <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-2">
          {items.map((char, i) => (
            <div
              key={`${char.id}-${i}`}
              ref={i === items.length - 1 ? lastElementRef : null}
              className="relative"
            >
              <Card character={char} />
              {char.owned && (
                <div className="absolute top-1.5 right-1.5 bg-brand-accent text-brand-midnight rounded-full p-0.5 shadow-lg border border-brand-midnight z-10 scale-75">
                  <CheckCircle2 size={12} strokeWidth={4} />
                </div>
              )}
            </div>
          ))}
          {loading && Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={`load-${i}`} />)}
        </div>
      ) : loading ? (
        <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-2">
          {Array.from({ length: 18 }).map((_, i) => <CardSkeleton key={`skeleton-${i}`} />)}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-20 opacity-40">
           <Users size={48} className="text-slate-700 mb-4" />
           <p className="text-slate-500 text-[10px] font-black uppercase tracking-[0.2em]">No results matched</p>
        </div>
      )}

      {loading && items.length > 0 && (
        <div className="flex justify-center py-8">
          <Loader2 size={14} className="animate-spin text-brand-accent" />
        </div>
      )}
    </div>
  );
};
