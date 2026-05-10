import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useUser } from '../context/UserContext';
import { useApi, useToast, Card } from '../components/UI';
import { ShoppingBag, Sparkles, Activity, Shield, PackageOpen, Loader2 } from 'lucide-react';
import { formatNumber } from '../utils';
import { apiFetch } from '../api';

export const Shop = ({ onCharClick }) => {
  const { data: chars, loading } = useApi('/shop/characters');
  const { data: hub } = useApi('/shop/hub');

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
                  onClick={() => onCharClick(char)}
                  className="w-full py-3.5 rounded-2xl bg-white text-brand-midnight font-black uppercase text-[10px] tracking-[0.2em] shadow-xl active:scale-95 transition-all flex items-center justify-center gap-2"
                >
                   BUY {char.zenith_price} <Activity size={12} />
                </button>
              )}
            </motion.div>
          ))}
        </div>
      )}

    </div>
  );
};
