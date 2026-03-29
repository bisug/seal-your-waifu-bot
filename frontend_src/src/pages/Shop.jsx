import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { apiFetch } from '../api';
import { Card } from '../components/UI';
import { ShoppingBag, Zap, Timer, Loader2, PackageOpen } from 'lucide-react';
import { useUser } from '../context/UserContext';

export const Shop = ({ onCharClick }) => {
  const { user, refreshUser } = useUser();
  const [activeTab, setActiveTab] = useState('market');
  const [marketItems, setMarketItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [hatching, setHatching] = useState(false);
  const [buyingId, setBuyingId] = useState(null);
  const [newChar, setNewChar] = useState(null);

  useEffect(() => {
    fetchShopData();
  }, [activeTab]);

  const fetchShopData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'market') {
        const data = await apiFetch('/shop/characters');
        setMarketItems(data);
      }
    } catch (err) {
      console.error('Shop fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const buyCharacter = async (charId) => {
    if (buyingId) return;
    setBuyingId(charId);
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
    try {
      const res = await apiFetch(`/shop/buy/character/${charId}`, { method: 'POST' });
      if (res.status === 'success') {
        window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
        await refreshUser();
        await fetchShopData();
      }
    } catch (err) {
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
      window.Telegram?.WebApp?.showAlert(err.message);
    } finally {
      setBuyingId(null);
    }
  };

  const incubateEgg = async (eggId) => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
    try {
      await apiFetch(`/eggs/incubate/${eggId}`, { method: 'POST' });
      refreshUser();
    } catch (err) {
      window.Telegram?.WebApp?.showAlert(err.message);
    }
  };

  const hatchEgg = async (eggId) => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('heavy');
    setHatching(true);
    try {
      const res = await apiFetch(`/eggs/hatch/${eggId}`, { method: 'POST' });
      if (res.status === 'success') {
         setNewChar(res.character);
         refreshUser();
      } else {
         window.Telegram?.WebApp?.showAlert(res.message);
      }
    } catch (err) {
      window.Telegram?.WebApp?.showAlert(err.message);
    } finally {
      setHatching(false);
    }
  };

  return (
    <div className="pb-32 pt-6 px-4">
      <header className="mb-6 flex justify-between items-end px-2">
        <div>
          <h1 className="text-2xl font-black uppercase tracking-tight">Market</h1>
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Trade Zeniths & Eggs</p>
        </div>
        <div className="flex items-center space-x-2 bg-brand-accent/10 border border-brand-accent/20 px-3 py-1.5 rounded-xl">
          <Zap size={14} className="text-brand-accent" />
          <span className="text-sm font-black text-brand-accent">{user?.stats?.zenith?.toLocaleString() || 0}</span>
        </div>
      </header>

      <div className="flex p-1.5 bg-white/5 rounded-2xl mb-8 border border-white/5">
        {[
          { id: 'market', icon: ShoppingBag, label: 'Market' },
          { id: 'eggs', icon: Timer, label: 'Hatchery' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex items-center justify-center space-x-2 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
              activeTab === tab.id ? 'bg-white text-brand-midnight shadow-lg' : 'text-slate-500 hover:text-white'
            }`}
          >
            <tab.icon size={14} />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {loading && activeTab === 'market' ? (
        <div className="flex justify-center py-20"><Loader2 className="text-brand-neon animate-spin" /></div>
      ) : (
        <AnimatePresence mode="wait">
          {activeTab === 'market' && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} key="market">
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 2xl:grid-cols-6 gap-4">
                {marketItems.map(char => (
                  <div key={char.id} className="space-y-3">
                    <Card character={char} onClick={() => onCharClick(char)} />
                    <button 
                      disabled={char.owned || buyingId === char.id}
                      onClick={() => buyCharacter(char.id)}
                      className={`w-full py-3 rounded-xl text-[10px] font-black uppercase tracking-widest border transition-all flex items-center justify-center gap-2 ${
                        char.owned 
                        ? 'border-white/5 bg-white/5 text-slate-600 grayscale' 
                        : buyingId === char.id
                        ? 'border-brand-accent/50 bg-brand-accent/20 text-brand-accent animate-pulse'
                        : 'border-brand-accent/50 bg-brand-accent/10 text-brand-accent hover:bg-brand-accent hover:text-brand-midnight shadow-lg shadow-brand-accent/10'
                      }`}
                    >
                      {buyingId === char.id ? (
                        <>
                          <Loader2 size={12} className="animate-spin" />
                          <span>SECURE LINK...</span>
                        </>
                      ) : char.owned ? (
                        'COLLECTED'
                      ) : (
                        `BUY ✧ ${char.zenith_price || 500}`
                      )}
                    </button>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === 'eggs' && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} key="eggs" className="space-y-4">
              {user?.eggs?.length > 0 ? (
                user.eggs.map(egg => (
                  <div key={egg.id} className="glass-panel p-5 rounded-2xl border border-white/5 flex items-center space-x-4">
                    <div className="w-14 h-14 rounded-xl flex items-center justify-center bg-brand-midnight border border-white/5">
                      <PackageOpen className={egg.status === 'incubating' ? 'animate-bounce text-brand-neon' : 'text-white/20'} />
                    </div>
                    <div className="flex-1 text-left">
                       <h3 className="text-xs font-black uppercase tracking-widest">{egg.name || 'Unknown Egg'}</h3>
                       <p className="text-[10px] text-slate-500 font-bold mb-2 uppercase">{egg.tier} TIER</p>
                       {egg.status === 'incubating' && (
                          <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                             <motion.div initial={{ width: 0 }} animate={{ width: '100%' }} className="h-full bg-brand-neon" />
                          </div>
                       )}
                    </div>
                    <div>
                      {egg.status === 'fresh' ? (
                        <button onClick={() => incubateEgg(egg.id)} className="px-4 py-2 rounded-lg bg-brand-neon text-brand-midnight text-[10px] font-black uppercase">INCUBATE</button>
                      ) : (
                        <button 
                          disabled={egg.remaining_mins > 0} 
                          onClick={() => hatchEgg(egg.id)} 
                          className={`px-4 py-2 rounded-lg text-[10px] font-black uppercase ${egg.remaining_mins <= 0 ? 'bg-brand-neon text-brand-midnight' : 'bg-white/5 text-slate-600'}`}
                        >
                          {egg.remaining_mins <= 0 ? 'HATCH' : `${egg.remaining_mins}m`}
                        </button>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-20 text-center opacity-40 italic text-xs uppercase tracking-widest font-bold">No eggs found</div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      )}

      <AnimatePresence>
        {(hatching || newChar) && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-[200] bg-brand-midnight/90 backdrop-blur-xl flex items-center justify-center p-8">
             {hatching ? (
               <div className="text-center space-y-6">
                  <motion.div animate={{ scale: [1, 1.1, 1], rotate: [0, 5, -5, 0] }} transition={{ repeat: Infinity, duration: 0.5 }} className="w-32 h-32 mx-auto bg-brand-neon/10 rounded-full flex items-center justify-center border-4 border-brand-neon/30">
                    <PackageOpen size={48} className="text-brand-neon" />
                  </motion.div>
                  <h2 className="text-brand-neon font-black text-xl uppercase tracking-[0.5em] animate-pulse">Hatching Egg...</h2>
               </div>
             ) : (
               <motion.div initial={{ scale: 0.8 }} animate={{ scale: 1 }} className="w-full max-w-sm text-center">
                  <div className="mb-4">
                     <p className="text-brand-neon font-black uppercase tracking-widest mb-2 font-black italic">! UNBOXED !</p>
                     <h2 className="text-3xl font-black uppercase italic leading-none">{newChar.name}</h2>
                  </div>
                  <div className="aspect-[3/4] rounded-3xl overflow-hidden border-4 border-brand-neon shadow-[0_0_50px_rgba(0,255,255,0.3)] mb-8">
                    <img src={newChar.img_url} className="w-full h-full object-cover" alt="New" />
                  </div>
                  <button 
                    onClick={() => { setNewChar(null); onCharClick(newChar); }}
                    className="w-full py-5 rounded-2xl bg-white text-brand-midnight font-black uppercase tracking-[0.3em] text-xs shadow-2xl"
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
