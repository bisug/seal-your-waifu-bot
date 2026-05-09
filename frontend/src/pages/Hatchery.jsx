import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useUser } from '../context/UserContext';
import { apiFetch } from '../api';

import { Card, ProgressBar, Skeleton, useToast } from '../components/UI';
import { useEggActions } from '../hooks/useEggActions';
import { Egg, Activity, Clock, ChevronRight, Sparkles, Shield, Flame, Wind, Loader2, Heart, Swords, ShoppingBag } from 'lucide-react';
import { formatNumber } from '../utils';

const EGG_THEMES = {
  common: { color: 'text-slate-400', bg: 'bg-slate-400/10', border: 'border-slate-400/20' },
  gold: { color: 'text-brand-accent', bg: 'bg-brand-accent/10', border: 'border-brand-accent/20' },
  void: { color: 'text-purple-500', bg: 'bg-purple-500/10', border: 'border-purple-500/20' }
};

const ABILITY_ICONS = {
  Caregiver: Shield,
  Scavenger: Sparkles,
  Pyromaniac: Flame,
  Swift: Wind
};

const StatBar = ({ icon: Icon, value, max = 300, color = "bg-brand-neon" }) => (
  <div className="flex items-center space-x-2">
    <Icon size={10} className="text-slate-500 shrink-0" />
    <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden border border-white/5 shadow-inner">
      <motion.div 
        initial={{ width: 0 }}
        animate={{ width: `${(value / max) * 100}%` }}
        transition={{ type: "spring", damping: 20, stiffness: 100 }}
        className={`h-full ${color} shadow-[0_0_12px_rgba(16,185,129,0.3)] relative`}
      >
        <div className="absolute inset-0 bg-white/20 animate-shimmer" />
      </motion.div>
    </div>
    <span className="text-[9px] font-mono font-black text-slate-300 w-6 text-right leading-none">{value}</span>
  </div>
);

const PetCard = ({ pet, isActive, onSelect }) => {
  const Icon = ABILITY_ICONS[pet.ability] || Activity;
  
  return (
    <button 
      onClick={() => onSelect({ ...pet, owned: true })}
      className={`glass-panel p-0 rounded-2xl border text-left relative transition-all active:scale-95 group overflow-hidden ${
        isActive ? 'border-brand-neon/40 ring-1 ring-brand-neon/20 shadow-lg shadow-brand-neon/5' : 'border-white/5 opacity-80 grayscale-[0.5] hover:opacity-100 hover:grayscale-0'
      }`}
    >
      {/* Background Pet Image */}
      <div className="relative h-28 overflow-hidden">
         <img 
            src={pet.img || 'https://files.catbox.moe/2hsawz.jpg'} 
            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
            alt={pet.name} 
         />
         <div className="absolute inset-0 bg-gradient-to-t from-brand-deep via-transparent to-transparent" />
         
         {/* Active Badge */}
         {isActive && (
            <div className="absolute top-2 right-2 bg-brand-neon text-brand-midnight text-[8px] font-black uppercase px-2 py-0.5 rounded-lg tracking-tighter shadow-lg border border-white/20 z-20">
              Active
            </div>
         )}
      </div>

      <div className="p-3 bg-brand-deep/80 backdrop-blur-md relative z-10 -mt-2">
        <div className="flex justify-between items-center mb-1">
          <h4 className="text-[11px] font-black uppercase tracking-tight text-white mb-0 truncate flex-1 pr-2">{pet.name}</h4>
          <span className="text-[10px] font-black font-mono text-brand-neon">LV. {pet.level}</span>
        </div>
        
        <p className="text-[8px] font-bold text-slate-400 uppercase tracking-widest mb-3 opacity-60">
           {pet.ability || 'Standard Pet'}
        </p>
        
        <div className="space-y-1.5 mb-3">
           <StatBar icon={Heart} value={pet.hp || 100} max={500} color="bg-rose-500" />
           <StatBar icon={Swords} value={pet.atk || 10} max={100} color="bg-amber-500" />
           <StatBar icon={Wind} value={pet.spd || 10} max={100} color="bg-cyan-500" />
        </div>

        <div className="pt-2 border-t border-white/5">
           <div className="flex items-center space-x-2">
              <div className="p-1 rounded bg-white/5 border border-white/5 text-brand-neon shrink-0">
                 <Icon size={10} />
              </div>
              <p className="text-[8px] leading-tight text-slate-500 font-medium line-clamp-1 italic">
                 {pet.desc || 'A loyal support pet.'}
              </p>
           </div>
        </div>
      </div>
    </button>
  );
};

const EggCard = ({ egg, onIncubate, onHatch, loading }) => {
  const theme = EGG_THEMES[egg.tier] || EGG_THEMES.common;
  const isIncubating = egg.status === 'incubating';
  const [timeLeft, setTimeLeft] = useState('');
  
  useEffect(() => {
    if (!isIncubating || !egg.hatch_time) return;
    
    const update = () => {
      const now = new Date();
      const end = new Date(egg.hatch_time);
      const diff = end - now;
      if (diff <= 0) {
        setTimeLeft('READY');
      } else {
        const mins = Math.floor(diff / 60000);
        const secs = Math.floor((diff % 60000) / 1000);
        setTimeLeft(`${mins}:${secs < 10 ? '0' : ''}${secs}`);
      }
    };
    update();
    const timer = setInterval(update, 1000);
    return () => clearInterval(timer);
  }, [egg.hatch_time, isIncubating]);

  const isReady = timeLeft === 'READY';

  return (
    <div className={`glass-panel p-4 rounded-[2rem] border ${theme.border} flex items-center space-x-4 relative overflow-hidden transition-all group hover:bg-white/[0.02]`}>
      <div className={`w-16 h-16 rounded-[1.25rem] ${theme.bg} ${theme.color} flex items-center justify-center relative z-10 border border-white/10 shadow-inner`}>
        <Egg size={32} className={`${isIncubating ? 'animate-bounce' : 'group-hover:scale-110 transition-transform'} drop-shadow-2xl`} />
        {isIncubating && (
           <div className="absolute inset-0 border-2 border-brand-neon/30 rounded-[1.25rem] animate-pulse" />
        )}
      </div>
      
      <div className="flex-1 relative z-10">
        <h4 className="text-[14px] font-black uppercase tracking-[0.1em] text-white mb-0.5">{egg.name || 'Unknown Egg'}</h4>
        <div className="flex items-center space-x-2">
           <span className={`text-[9px] font-black uppercase tracking-widest ${theme.color}`}>{egg.tier} core</span>
           <div className="w-1 h-1 rounded-full bg-slate-800" />
           <span className="text-[9px] font-black uppercase tracking-widest text-slate-600">{egg.status}</span>
        </div>
      </div>

      <div className="relative z-10">
        {egg.status === 'fresh' || !egg.status ? (
          <button 
            onClick={onIncubate}
            disabled={loading}
            className="h-11 px-6 rounded-2xl bg-white text-brand-midnight text-[10px] font-black uppercase tracking-[0.2em] shadow-xl active:scale-95 transition-all"
          >
            Incubate
          </button>
        ) : (
          <div className="flex flex-col items-end">
             <div className="flex items-center space-x-2 mb-1 bg-brand-neon/10 px-3 py-1 rounded-full border border-brand-neon/20">
                <Clock size={10} className="text-brand-neon animate-spin-slow" />
                <span className="text-[12px] font-black font-mono text-brand-neon leading-none">{timeLeft}</span>
             </div>
             {isReady && (
               <button 
                 onClick={onHatch}
                 disabled={loading}
                 className="mt-2 h-10 px-6 rounded-2xl bg-brand-neon text-brand-midnight text-[10px] font-black uppercase tracking-[0.2em] animate-pulse shadow-[0_0_20px_rgba(16,185,129,0.4)]"
               >
                 Hatch Now
               </button>
             )}
          </div>
        )}
      </div>

      <div className="absolute -right-2 -bottom-2 opacity-[0.03] group-hover:opacity-[0.05] transition-opacity pointer-events-none">
         <Egg size={140} />
      </div>
    </div>
  );
};

const EmptyState = ({ icon: Icon, message }) => (
  <div className="glass-panel p-12 rounded-3xl border border-white/5 text-center flex flex-col items-center opacity-40">
    <Icon size={40} className="text-slate-800 mb-4" />
    <p className="text-slate-500 text-[10px] font-bold uppercase tracking-widest leading-relaxed max-w-[200px]">
      {message}
    </p>
  </div>
);

export const Hatchery = ({ onPetClick }) => {
  const { user, loading: userLoading, refreshUser } = useUser();
  const { addToast } = useToast();
  const { incubateEgg, hatchEgg, loading, hatchingResult, setHatchingResult } = useEggActions();
  const [activeTab, setActiveTab] = useState('eggs'); // 'eggs' or 'pets'

  const handleIncubate = async (eggId) => {
    await incubateEgg(eggId);
  };

  const handleHatch = async (eggId) => {
    await hatchEgg(eggId);
  };

  // Fix: Use body class for scroll lock instead of direct selector mutation
  useEffect(() => {
    if (hatchingResult) {
      document.body.classList.add('no-scroll');
      return () => document.body.classList.remove('no-scroll');
    }
  }, [hatchingResult]);

  const handleSetPet = async (petName) => {
    try {
      await apiFetch(`/pets/set_active/${petName}`, { method: 'POST' });
      addToast(`${petName} Synced to Core`, 'success');
      await refreshUser();
    } catch (err) {
      addToast(err.message || 'Sync failed', 'error');
    }
  };

  if (userLoading) return (
    <div className="p-10 flex flex-col items-center justify-center min-h-[60vh]">
       <Loader2 className="animate-spin text-brand-neon/20 mb-4" size={32} />
       <p className="text-slate-600 text-[10px] font-black uppercase tracking-widest">Loading Eggs...</p>
    </div>
  );
  
  if (!user) return null;

  return (
    <div className="pb-24 pt-6 px-4 max-w-lg mx-auto">
      <section className="mb-8 text-center relative pt-4">
        <div className="absolute -top-10 left-1/2 -translate-x-1/2 w-48 h-48 bg-brand-neon/5 blur-[80px] rounded-full pointer-events-none" />
        <motion.div 
            initial={{ y: -10, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="inline-block px-4 py-1.5 rounded-full bg-white/5 border border-white/10 mb-4 backdrop-blur-md"
        >
            <div className="flex items-center space-x-2">
                <Sparkles size={14} className="text-brand-neon" />
                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-white">Advanced Hatchery</span>
            </div>
        </motion.div>
        <h1 className="text-3xl font-black uppercase tracking-[0.1em] mb-2 text-white">Incubation</h1>
        <p className="text-[11px] font-bold text-slate-500 uppercase tracking-widest opacity-60">Manage companions and hatch cores</p>
      </section>

      <div className="flex bg-white/5 p-1 rounded-2xl mb-8 border border-white/5">
        {['eggs', 'pets'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-3 rounded-xl text-[11px] font-black uppercase tracking-widest transition-all ${
              activeTab === tab ? 'bg-white/10 text-white shadow-lg border border-white/5' : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            <div className="flex items-center justify-center space-x-2">
              {tab === 'eggs' ? <Egg size={14} /> : <Activity size={14} />}
              <span>{tab === 'eggs' ? `EGGS (${formatNumber(user.eggs?.length)})` : `PETS (${formatNumber(user.pets?.length)})`}</span>
            </div>
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {activeTab === 'eggs' ? (
          <motion.section 
            key="egg-grid"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="space-y-4"
          >
            {user.eggs && user.eggs.length > 0 ? (
              user.eggs.map((egg) => (
                <EggCard 
                  key={egg.id} 
                  egg={egg} 
                  onIncubate={() => handleIncubate(egg.id)} 
                  onHatch={() => handleHatch(egg.id)}
                  loading={loading}
                />
              ))
            ) : (
              <EmptyState icon={Egg} message="No eggs found. Get eggs from the Shop or Seasonal Pass." />
            )}
          </motion.section>
        ) : (
          <motion.section 
            key="pet-grid"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
          >
            <div className="flex justify-between items-center mb-4 px-1">
               <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Companions List</span>
               <button 
                onClick={() => window.dispatchEvent(new CustomEvent('nav-market-pets'))}
                className="text-brand-neon text-[9px] font-black uppercase tracking-widest flex items-center gap-1.5 bg-brand-neon/10 px-3 py-1.5 rounded-lg border border-brand-neon/20 active:scale-95 transition-all"
               >
                 <ShoppingBag size={10} /> Buy More
               </button>
            </div>
            <div className="grid grid-cols-2 gap-3">
            {user.pets && user.pets.length > 0 ? (
              user.pets.map((pet) => (
                <PetCard 
                  key={pet.name} 
                  pet={pet} 
                  isActive={user.current_pet?.name === pet.name}
                  onSelect={onPetClick}
                />
              ))
            ) : (
              <div className="col-span-2">
                <div className="glass-panel p-12 rounded-[2.5rem] border border-white/5 text-center flex flex-col items-center">
                  <Activity size={40} className="text-slate-800 mb-6" />
                  <p className="text-slate-400 text-[11px] font-bold uppercase tracking-widest leading-relaxed max-w-[200px] mb-8">
                    No active companions detected in your hatchery.
                  </p>
                  <button 
                    onClick={() => {
                        window.dispatchEvent(new CustomEvent('nav-market-pets'));
                    }}
                    className="px-8 py-4 rounded-2xl bg-brand-neon text-brand-midnight text-[10px] font-black uppercase tracking-[0.2em] shadow-lg shadow-brand-neon/20 active:scale-95 transition-all"
                  >
                    Visit Pet Shop
                  </button>
                </div>
              </div>
            )}
          </motion.section>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {hatchingResult && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-brand-midnight/95 backdrop-blur-3xl overflow-hidden">
            <motion.div 
              initial={{ scale: 0 }}
              animate={{ rotate: [0, 90, 180, 270, 360] }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              className="absolute w-[800px] h-[800px] bg-brand-neon/5 blur-[120px] rounded-full pointer-events-none"
            />
            
            <motion.div 
              initial={{ scale: 0.5, opacity: 0, y: 50 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 1.1, opacity: 0 }}
              transition={{ type: "spring", bounce: 0.4, duration: 0.8 }}
              className="w-full max-w-sm relative z-20"
            >
              <div className="text-center mb-10">
                 <motion.div
                   initial={{ opacity: 0, y: -20 }}
                   animate={{ opacity: 1, y: 0 }}
                   transition={{ delay: 0.5 }}
                 >
                   <h3 className="text-brand-neon font-black uppercase tracking-[0.5em] text-[10px] mb-3">Sync Accomplished</h3>
                   <h2 className="text-2xl font-black text-white uppercase tracking-wider">New Unit Acquired</h2>
                 </motion.div>
              </div>

              <div className="relative group">
                <div className="absolute -inset-20 bg-brand-neon/15 blur-[100px] rounded-full animate-pulse" />
                <div className="absolute -inset-1 bg-gradient-to-r from-brand-neon/0 via-brand-neon/40 to-brand-neon/0 blur-xl opacity-50 group-hover:opacity-100 transition-opacity" />
                <Card character={hatchingResult} className="shadow-2xl shadow-brand-neon/10" />
              </div>

              <motion.button 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1 }}
                onClick={() => setHatchingResult(null)}
                whileTap={{ scale: 0.95 }}
                className="w-full mt-14 py-5 rounded-3xl bg-white text-brand-midnight font-black uppercase text-[11px] tracking-[0.4em] transition-all shadow-[0_20px_40px_rgba(255,255,255,0.1)] active:shadow-none"
              >
                Return to Core
              </motion.button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
