import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { apiFetch } from '../api';
import { Card, CardSkeleton, useApi } from '../components/UI';
import { ShoppingBag, Zap, Timer, PackageOpen, Loader2, Check } from 'lucide-react';
import { useUser } from '../context/UserContext';
import { toast } from 'react-hot-toast';
import { formatNumber } from '../utils';

import { useEggActions } from '../hooks/useEggActions';

export const Shop = ({ onCharClick }) => {
  const { user, refreshUser } = useUser();
  const [activeTab, setActiveTab] = useState('market');
  const { incubateEgg, hatchEgg, loading: hatching, hatchingResult: newChar, setHatchingResult: setNewChar } = useEggActions();

  const handleTabChange = (tabId) => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
    setActiveTab(tabId);
  };

  const { data: marketItems, loading, execute: fetchShopData } = useApi('/shop/characters', { 
    initialData: [],
    manual: activeTab !== 'market'
  }, [activeTab]);

  // Use refs for callbacks to ensure the event listener always uses the latest functions
  // without needing to re-bind the listener (avoiding memory leaks or missed events)
  const fetchShopDataRef = React.useRef(fetchShopData);
  const refreshUserRef = React.useRef(refreshUser);

  useEffect(() => {
    fetchShopDataRef.current = fetchShopData;
    refreshUserRef.current = refreshUser;
  }, [fetchShopData, refreshUser]);

  useEffect(() => {
    const handlePurchase = async (e) => {
      const { charId } = e.detail;
      try {
        const res = await apiFetch(`/shop/buy/character/${charId}`, { method: 'POST' });
        if (res.status === 'success') {
          window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
          toast.success('Character added to harem');
          await refreshUserRef.current();
          await fetchShopDataRef.current();
        }
      } catch (err) {
        toast.error(err.message || 'Transaction failed');
      }
    };

    window.addEventListener('shop-data-refresh', fetchShopDataRef.current);
    return () => window.removeEventListener('shop-data-refresh', fetchShopDataRef.current);
  }, []); // Bind once on mount

  return (
    <div className="pb-8 pt-6 px-4">
      <header className="mb-6 flex justify-between items-end px-2">
        <div>
          <h1 className="text-2xl font-black uppercase tracking-tight">Market</h1>
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Acquire Waifus</p>
        </div>
        <div className="flex items-center space-x-2 bg-brand-neon/10 border border-brand-neon/20 px-3 py-1.5 rounded-xl shadow-[0_0_15px_rgba(0,242,255,0.1)]">
          <Zap size={14} className="text-brand-neon" />
          <span className="text-sm font-black text-brand-neon">{formatNumber(user?.stats?.zenith)}</span>
        </div>
      </header>

      <div className="flex p-1.5 bg-white/5 rounded-2xl mb-8 border border-white/5">
        {[
          { id: 'market', icon: ShoppingBag, label: 'Market' },
          { id: 'eggs', icon: Timer, label: 'Incubation' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => handleTabChange(tab.id)}
            className={`flex-1 flex items-center justify-center space-x-2 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
              activeTab === tab.id ? 'bg-white text-brand-midnight shadow-lg' : 'text-slate-500 hover:text-white'
            }`}
          >
            <tab.icon size={14} />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {loading && activeTab === 'market' && !(Array.isArray(marketItems) && marketItems.length) ? (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2">
          {Array.from({ length: 12 }).map((_, i) => (
            <CardSkeleton key={`shop-skeleton-${i}`} />
          ))}
        </div>
      ) : (
        <AnimatePresence mode="wait">
          {activeTab === 'market' && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} key="market" className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2">
                <AnimatePresence mode="popLayout">
                  {(Array.isArray(marketItems) ? marketItems : []).map((char, i) => (
                    <motion.div 
                      key={char.id} 
                      layout
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: (i % 8) * 0.05 }}
                      className="relative"
                    >
                      <div className={char.owned ? 'opacity-40 grayscale-[0.5]' : ''}>
                         <Card 
                           character={char} 
                           onClick={() => onCharClick(char)} 
                         />
                      </div>
                      
                      {char.owned && (
                        <div className="absolute top-1.5 right-1.5 bg-brand-neon text-brand-midnight rounded-full p-0.5 shadow-lg z-20 border border-brand-midnight scale-75">
                          <Check size={11} strokeWidth={4} />
                        </div>
                      )}
                    </motion.div>
                  ))}
                </AnimatePresence>
            </motion.div>
          )}

          {activeTab === 'eggs' && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} key="eggs" className="space-y-4">
              {user?.eggs?.length > 0 ? (
                (user.eggs || []).map(egg => (
                  <div key={egg.id} className="glass-panel p-5 rounded-2xl border border-white/5 flex items-center space-x-4 bg-mesh">
                    <div className="w-14 h-14 rounded-xl flex items-center justify-center bg-brand-midnight border border-white/5 relative overflow-hidden">
                      <div className="absolute inset-0 bg-brand-neon/5 blur-xl animate-pulse" />
                      <PackageOpen className={egg.status === 'incubating' ? 'animate-bounce text-brand-neon' : 'text-white/20'} />
                    </div>
                    <div className="flex-1 text-left">
                       <h3 className="text-xs font-black uppercase tracking-widest">{egg.name || 'Unknown Egg'}</h3>
                       <p className="text-[10px] text-slate-500 font-bold mb-2 uppercase">{egg.tier} TIER</p>
                       {egg.status === 'incubating' && (
                          <div className="h-1 w-full bg-slate-800 rounded-full overflow-hidden">
                             <motion.div initial={{ width: 0 }} animate={{ width: '100%' }} transition={{ duration: egg.remaining_mins * 60 }} className="h-full bg-brand-neon" />
                          </div>
                       )}
                    </div>
                    <div>
                      {egg.status === 'fresh' ? (
                        <button onClick={() => incubateEgg(egg.id)} className="px-4 py-2 rounded-lg bg-brand-neon text-brand-midnight text-[10px] font-black uppercase tracking-widest shadow-lg shadow-brand-neon/20 transition-all active:scale-95">INCUBATE</button>
                      ) : (
                        <button 
                          disabled={egg.remaining_mins > 0} 
                          onClick={() => hatchEgg(egg.id)} 
                          className={`px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${egg.remaining_mins <= 0 ? 'bg-brand-neon text-brand-midnight shadow-lg shadow-brand-neon/20 active:scale-95' : 'bg-white/5 text-slate-600 border border-white/5'}`}
                        >
                          {egg.remaining_mins <= 0 ? 'HATCH' : `${egg.remaining_mins}M`}
                        </button>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-20 text-center opacity-40 italic text-xs uppercase tracking-widest font-bold">No data found in harem hatchery</div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      )}

      {/* Cinematic Reveal remains as is for maximum impact */}
      <AnimatePresence>
        {(hatching || newChar) && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-[200] bg-brand-midnight/90 backdrop-blur-xl flex items-center justify-center p-8 bg-mesh">
             {hatching ? (
               <div className="text-center space-y-6">
                  <motion.div animate={{ scale: [1, 1.1, 1], rotate: [0, 5, -5, 0] }} transition={{ repeat: Infinity, duration: 0.5 }} className="w-32 h-32 mx-auto bg-brand-neon/10 rounded-full flex items-center justify-center border-4 border-brand-neon/30 shadow-[0_0_30px_rgba(0,242,255,0.2)]">
                    <PackageOpen size={48} className="text-brand-neon" />
                  </motion.div>
                  <h2 className="text-brand-neon font-black text-xl uppercase tracking-[0.5em] animate-pulse">Hatching Egg...</h2>
               </div>
             ) : (
               <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="w-full max-w-sm text-center">
                  <div className="mb-4">
                     <p className="text-brand-neon font-black uppercase tracking-widest mb-2 font-black italic">! SEALED !</p>
                     <h2 className="text-3xl font-black uppercase italic leading-none text-white tracking-tighter">{newChar.name}</h2>
                  </div>
                  <div className="aspect-[3/4] rounded-3xl overflow-hidden border-4 border-brand-neon shadow-[0_0_50px_rgba(0,242,255,0.3)] mb-8 relative">
                    <img src={newChar.img_url} className="w-full h-full object-cover" alt="New" />
                    <div className="absolute inset-0 bg-gradient-to-t from-brand-midnight via-transparent to-transparent opacity-60" />
                  </div>
                  <button 
                    onClick={() => { setNewChar(null); onCharClick(newChar); }}
                    className="w-full py-5 rounded-2xl bg-white text-brand-midnight font-black uppercase tracking-[0.3em] text-xs shadow-2xl hover:scale-[1.02] active:scale-95 transition-all"
                  >
                    COLLECT & VIEW
                  </button>
               </motion.div>
             )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
