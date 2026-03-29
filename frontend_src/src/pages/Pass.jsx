import React from 'react';
import { motion } from 'framer-motion';
import { Award, Lock, Sparkles, ChevronRight } from 'lucide-react';

export const Pass = () => {
  const rewards = [
    { lvl: 5, reward: 'Premium Egg', rarity: 'Rare', type: 'item' },
    { lvl: 10, reward: 'Zenith Pack (500)', rarity: 'Epic', type: 'currency' },
    { lvl: 15, reward: 'Collector Title', rarity: 'Legendary', type: 'cosmetic' },
    { lvl: 25, reward: 'Celestial Shard', rarity: 'Mythical', type: 'item' },
    { lvl: 50, reward: 'Mythical Seal', rarity: 'Celestial', type: 'waifu' },
  ];

  return (
    <div className="pb-32 pt-6 px-4 uppercase tracking-[0.2em] font-black">
      <header className="mb-10 px-2">
        <div className="flex items-center space-x-2 text-brand-accent mb-1">
          <Sparkles size={16} />
          <span className="text-[10px]">Neural Protocol</span>
        </div>
        <h1 className="text-2xl tracking-tight">Season 1 Pass</h1>
      </header>

      <div className="space-y-6 relative ml-4">
        <div className="absolute left-6 top-4 bottom-4 w-0.5 bg-white/5" />
        
        {rewards.map((r, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            className="flex items-center space-x-8 group"
          >
            <div className={`relative z-10 w-12 h-12 rounded-2xl flex items-center justify-center border-2 transition-all ${
              r.rarity === 'Celestial' ? 'border-brand-neon bg-brand-neon/10' : 
              r.rarity === 'Mythical' ? 'border-red-500 bg-red-500/10' : 
              'border-white/10 bg-white/5'
            }`}>
              <span className="text-xs font-black">{r.lvl}</span>
              {r.lvl === 50 && <div className="absolute -inset-1 rounded-2xl border-2 border-brand-neon/30 animate-ping" />}
            </div>

            <div className="flex-1 glass-panel p-4 rounded-2xl border border-white/5 group-hover:border-white/10 transition-all flex items-center justify-between">
              <div className="text-left">
                <p className="text-[12px] tracking-tight">{r.reward}</p>
                <div className="flex items-center space-x-1.5 mt-0.5">
                   <Award size={10} className="text-brand-neon" />
                   <span className="text-[8px] text-slate-500 font-bold">{r.rarity} REWARD</span>
                </div>
              </div>
              <Lock size={16} className="text-slate-700" />
            </div>
            
            <ChevronRight size={16} className="text-slate-800" />
          </motion.div>
        ))}
      </div>
      
      <div className="mt-12 p-6 glass-panel rounded-3xl border border-brand-neon/20 bg-brand-neon/[0.02] text-center">
         <p className="text-[10px] text-slate-500 mb-2">COMPLETE QUESTS TO LEVEL UP</p>
         <button className="w-full py-4 rounded-2xl bg-brand-neon text-brand-midnight text-[11px] font-black tracking-[0.3em]">PURCHASE PREMIUM</button>
      </div>
    </div>
  );
};
