import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useApi } from '../components/UI';
import { Heart, Activity, Check, Zap, Loader2 } from 'lucide-react';
import { useUser } from '../context/UserContext';

import { formatNumber } from '../utils';

export const PetShop = ({ onPetClick }) => {
  const { user } = useUser();

  const { data, loading } = useApi('/shop/pets', {
    initialData: { pets: [], owned: [], current_level: 1 }
  });

  const { pets = [], owned = [], current_level = 1 } = data || {};

  if (loading && pets.length === 0) {
    return (
      <div className="pb-32 pt-20 px-4 flex flex-col items-center justify-center">
        <Loader2 className="animate-spin text-brand-accent mb-4" />
        <p className="text-[10px] font-black uppercase tracking-widest text-slate-500">Syncing Pet Market...</p>
      </div>
    );
  }

  if (!loading && pets.length === 0) {
    return (
      <div className="pb-32 pt-20 px-4 flex flex-col items-center justify-center text-center">
        <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center mb-4 border border-white/5">
          <Activity className="text-slate-700" size={32} />
        </div>
        <h3 className="text-white font-black uppercase tracking-wider mb-2">Market Closed</h3>
        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest max-w-[200px]">
          The pet shop is currently out of stock or undergoing maintenance.
        </p>
      </div>
    );
  }

  return (
    <div className="pb-32 pt-6 px-4">
      <header className="mb-6 flex justify-between items-end px-2">
        <div>
          <h1 className="text-2xl font-black uppercase tracking-tight">Pet Shop</h1>
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Acquire Companions</p>
        </div>
        <div className="flex items-center space-x-2 bg-brand-accent/10 border border-brand-accent/20 px-3 py-1.5 rounded-xl shadow-[0_0_15px_rgba(59,130,246,0.1)]">
          <Activity size={14} className="text-brand-accent" />
          <span className="text-sm font-black text-brand-accent">{formatNumber(user?.stats?.zenith || 0)}</span>
        </div>
      </header>

      <div className="space-y-4">
        <AnimatePresence>
          {pets.map((pet, i) => {
            const isOwned = owned.includes(pet.name);
            const isLocked = current_level < pet.req_level;
            
            return (
              <motion.div 
                key={pet.name}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                onClick={() => onPetClick && onPetClick({ ...pet, shopIndex: i, owned: isOwned })}
                className={`flex gap-4 p-4 rounded-3xl border border-white/10 backdrop-blur-md glass-panel relative overflow-hidden transition-all active:scale-[0.98] cursor-pointer ${
                  isOwned || isLocked ? 'opacity-80 grayscale-[0.3]' : 'hover:border-brand-accent/30 hover:bg-white/[0.02]'
                }`}
              >
                <div className="absolute top-0 right-0 w-32 h-32 bg-brand-accent/10 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />
                
                <div className="w-24 h-24 shrink-0 rounded-2xl overflow-hidden border border-white/20 shadow-lg bg-black/40">
                  <img src={pet.img} alt={pet.name} className="w-full h-full object-cover" />
                </div>
                
                <div className="flex-1 flex flex-col pt-1">
                  <h3 className="font-black text-white text-lg tracking-tight leading-none mb-1">{pet.name}</h3>
                  <p className="text-[9px] font-bold text-brand-accent uppercase tracking-widest mb-3 flex items-center gap-1">
                    <Activity size={10} />
                    <span>{pet.ability}</span>
                  </p>
                  
                  <div className="grid grid-cols-2 gap-y-1 gap-x-2 mb-3">
                    <div className="flex items-center gap-1.5 text-[10px] text-slate-300 font-mono">
                      <Heart size={10} className="text-red-400" /> {pet.hp}
                    </div>
                    <div className="flex items-center gap-1.5 text-[10px] text-slate-300 font-mono">
                      <Zap size={10} className="text-orange-400" /> {pet.atk}
                    </div>
                    <div className="flex items-center gap-1.5 text-[10px] text-slate-300 font-mono col-span-2 text-brand-accent">
                       Luck {(pet.luck * 100).toFixed(0)}%
                    </div>
                  </div>
                  
                  <div className="mt-auto">
                    {isOwned ? (
                      <div className="w-full py-2 bg-brand-accent/10 text-brand-accent rounded-xl text-[9px] font-black uppercase tracking-widest flex items-center justify-center gap-2 border border-brand-accent/20">
                        <Check size={11} strokeWidth={3} /> Owned
                      </div>
                    ) : isLocked ? (
                      <div className="w-full py-2 bg-red-500/10 text-red-500 rounded-xl text-[9px] font-black uppercase tracking-widest flex items-center justify-center gap-2 border border-red-500/10">
                         Req Lvl {pet.req_level}
                      </div>
                    ) : (
                      <div className="w-full py-2 bg-white/5 text-white/50 rounded-xl text-[9px] font-black uppercase tracking-widest flex items-center justify-center gap-2 border border-white/5">
                        Preview & Buy
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
};
