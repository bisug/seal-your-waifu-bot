import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useUser } from '../context/UserContext';
import { useApi, useToast, Card } from '../components/UI';
import { ShoppingBag, Sparkles, Activity, Shield, PackageOpen, Loader2 } from 'lucide-react';
import { formatNumber } from '../utils';
import { apiFetch } from '../api';

export const Shop = ({ onCharClick }) => {
  const { refreshUser } = useUser();
  const { addToast } = useToast();
  const [buyingId, setBuyingIndex] = useState(null);
  const [hatchingResult, setHatchingResult] = useState(null);

  const { data: chars, loading, execute: fetchChars } = useApi('/shop/characters');
  const { data: hub, execute: fetchHub } = useApi('/shop/hub');

  const handleBuy = async (char) => {
    if (buyingId) return;
    setBuyingIndex(char.id);
    try {
      const res = await apiFetch(`/shop/buy/character/${char.id}`, { method: 'POST' });
      addToast(`Acquired ${res.char_name}!`, 'success');
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
      await fetchChars();
      await fetchHub();
      await refreshUser();
    } catch (err) {
      addToast(err.message, 'error');
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
    } finally {
      setBuyingIndex(null);
    }
  };

  return (
    <div className="pb-32 pt-6 px-4">
      <header className="mb-10 px-2 flex justify-between items-end">
        <div>
           <div className="flex items-center space-x-2 text-brand-accent mb-1">
             <ShoppingBag size={16} />
             <span className="text-[10px] font-black uppercase tracking-[0.3em]">Imperial Market</span>
           </div>
           <h1 className="text-3xl font-black uppercase tracking-tight">Daily Shop</h1>
        </div>
        <div className="flex flex-col items-end gap-1.5">
           <div className="flex items-center space-x-2 bg-brand-accent/10 border border-brand-accent/20 px-3 py-1.5 rounded-xl shadow-lg shadow-brand-accent/5">
              <Activity size={14} className="text-brand-accent" />
              <span className="text-sm font-black text-brand-accent">{formatNumber(hub?.zenith || 0)}</span>
           </div>
        </div>
      </header>

      {loading && !chars ? (
        <div className="flex justify-center py-20"><Loader2 className="animate-spin text-brand-accent" /></div>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          {chars?.map((char) => (
            <motion.div
              key={char.id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex flex-col"
            >
              <div className="relative mb-3 aspect-[3/4]">
                 <Card character={char} onClick={() => onCharClick(char)} />
                 {char.owned && (
                   <div className="absolute inset-0 bg-brand-midnight/60 backdrop-blur-[2px] flex items-center justify-center rounded-[1.5rem] z-30">
                      <div className="bg-brand-accent text-white px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest shadow-lg">
                        COLLECTED
                      </div>
                   </div>
                 )}
              </div>

              {!char.owned && (
                <button
                  onClick={() => handleBuy(char)}
                  disabled={!!buyingId}
                  className="w-full py-3.5 rounded-2xl bg-white text-brand-midnight font-black uppercase text-[10px] tracking-[0.2em] shadow-xl active:scale-95 transition-all flex items-center justify-center gap-2"
                >
                  {buyingId === char.id ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    <>BUY {char.zenith_price} <Activity size={12} /></>
                  )}
                </button>
              )}
            </motion.div>
          ))}
        </div>
      )}

      <AnimatePresence>
        {hatchingResult && (
          <div className="fixed inset-0 z-[200] flex items-center justify-center p-6 bg-brand-midnight/95 backdrop-blur-3xl">
             <div className="text-center max-w-xs w-full">
                <div className="w-32 h-32 mx-auto bg-brand-accent/10 rounded-full flex items-center justify-center border-4 border-brand-accent/30 shadow-[0_0_30px_rgba(59,130,246,0.2)] mb-8">
                    <PackageOpen size={48} className="text-brand-accent" />
                </div>
                <h2 className="text-brand-accent font-black text-xl uppercase tracking-[0.5em] animate-pulse mb-8">Unboxing...</h2>
                <div className="aspect-[3/4] rounded-3xl overflow-hidden border-4 border-brand-accent shadow-[0_0_50px_rgba(59,130,246,0.3)] mb-8 relative">
                   <img src={hatchingResult.img_url} className="w-full h-full object-cover" />
                   <div className="absolute inset-0 bg-gradient-to-t from-brand-midnight to-transparent" />
                   <div className="absolute bottom-4 inset-x-0">
                     <p className="text-brand-accent font-black uppercase tracking-widest mb-2 italic">! SEALED !</p>
                     <h3 className="text-white font-black uppercase text-lg">{hatchingResult.name}</h3>
                   </div>
                </div>
                <button
                  onClick={() => setHatchingResult(null)}
                  className="w-full py-5 bg-white text-brand-midnight rounded-2xl font-black uppercase tracking-[0.3em]"
                >
                  Confirm
                </button>
             </div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
