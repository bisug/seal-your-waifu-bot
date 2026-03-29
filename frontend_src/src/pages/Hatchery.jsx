import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useUser } from '../context/UserContext';
import { apiFetch } from '../api';
import { toast } from 'react-hot-toast';
import { Card, ProgressBar, Skeleton } from '../components/UI';
import { Egg, Zap, Clock, ChevronRight, Sparkles, Shield, Flame, Wind, Loader2 } from 'lucide-react';

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

const PetCard = ({ pet, isActive, onSelect }) => {
  const Icon = ABILITY_ICONS[pet.ability] || Zap;
  
  return (
    <button 
      onClick={onSelect}
      className={`glass-panel p-4 rounded-3xl border text-left relative transition-all active:scale-95 ${
        isActive ? 'border-brand-neon/40 ring-1 ring-brand-neon/20 shadow-lg shadow-brand-neon/5' : 'border-white/5 opacity-60 grayscale hover:opacity-100'
      }`}
    >
      <div className="flex justify-between items-start mb-4">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${isActive ? 'bg-brand-neon/10 text-brand-neon' : 'bg-slate-800 text-slate-500'}`}>
          <Icon size={20} />
        </div>
        {isActive && (
          <div className="bg-brand-neon text-brand-midnight text-[8px] font-black uppercase px-1.5 py-0.5 rounded tracking-tighter shadow-lg">
            Active Squad
          </div>
        )}
      </div>

      <h4 className="text-[13px] font-black uppercase tracking-tight text-white mb-0.5">{pet.name}</h4>
      <p className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-3">{pet.type || 'Nanotech Support'}</p>
      
      <div className="pt-3 border-t border-white/5 space-y-1">
         <div className="flex items-center space-x-1.5 text-brand-neon">
            <Icon size={10} />
            <span className="text-[9px] font-black uppercase tracking-widest">{pet.ability || 'Standard'}</span>
         </div>
         <p className="text-[8px] leading-tight text-slate-500 font-medium line-clamp-2">
            {pet.desc || 'Standard surveillance and support unit.'}
         </p>
      </div>
    </button>
  );
};

const EggCard = ({ egg, onIncubate, onHatch, loading }) => {
  const theme = EGG_THEMES[egg.tier] || EGG_THEMES.common;
  const isIncubating = egg.status === 'incubating';
  const [timeLeft, setTimeLeft] = useState('');
  
  // Real-time countdown
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
    <div className={`glass-panel p-5 rounded-3xl border ${theme.border} flex items-center space-x-4 relative overflow-hidden group`}>
      <div className={`w-14 h-14 rounded-2xl ${theme.bg} ${theme.color} flex items-center justify-center relative z-10`}>
        <Egg size={28} className={isIncubating ? 'animate-bounce' : ''} />
      </div>
      
      <div className="flex-1 relative z-10">
        <h4 className="text-[14px] font-black uppercase tracking-tight text-white mb-0.5">{egg.name || 'Unknown Pod'}</h4>
        <div className="flex items-center space-x-2">
           <span className={`text-[10px] font-bold uppercase tracking-widest ${theme.color}`}>{egg.tier} System</span>
           <div className="w-1 h-1 rounded-full bg-slate-700" />
           <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">{egg.status}</span>
        </div>
      </div>

      <div className="relative z-10">
        {egg.status === 'fresh' || !egg.status ? (
          <button 
            onClick={onIncubate}
            disabled={loading}
            className="bg-white text-brand-midnight text-[10px] font-black uppercase px-6 py-3 rounded-xl tracking-widest active:scale-95 transition-all shadow-lg"
          >
            Initiate
          </button>
        ) : (
          <div className="flex flex-col items-end">
             <div className="flex items-center space-x-2 mb-1">
                <Clock size={12} className="text-brand-neon" />
                <span className="text-[12px] font-black font-mono text-brand-neon">{timeLeft}</span>
             </div>
             {isReady && (
               <button 
                 onClick={onHatch}
                 disabled={loading}
                 className="bg-brand-neon text-brand-midnight text-[10px] font-black uppercase px-6 py-2.5 rounded-xl tracking-widest animate-pulse shadow-[0_0_15px_rgba(0,255,255,0.3)]"
               >
                 Hatch
               </button>
             )}
          </div>
        )}
      </div>

      <div className="absolute right-0 bottom-0 translate-x-1/4 translate-y-1/4 opacity-5 group-hover:opacity-10 transition-opacity">
         <Egg size={120} />
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

export const Hatchery = () => {
  const { user, loading: userLoading, refreshUser } = useUser();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('eggs'); // 'eggs' or 'pets'
  const [hatchingResult, setHatchingResult] = useState(null);

  const handleIncubate = async (eggId) => {
    setLoading(true);
    try {
      await apiFetch(`/eggs/incubate/${eggId}`, { method: 'POST' });
      toast.success('Incubation Matrix Active');
      await refreshUser();
    } catch (err) {
      toast.error(err.message || 'Calibration failure');
    } finally {
      setLoading(false);
    }
  };

  const handleHatch = async (eggId) => {
    setLoading(true);
    try {
      const res = await apiFetch(`/eggs/hatch/${eggId}`, { method: 'POST' });
      if (res.status === 'success') {
        setHatchingResult(res.character);
        toast.success('Lifeform Detected');
      } else {
        toast.error(res.message || 'Incubation Failure');
      }
      await refreshUser();
    } catch (err) {
      toast.error(err.message || 'Hatch protocol interrupted');
    } finally {
      setLoading(false);
    }
  };

  const handleSetPet = async (petName) => {
    try {
      await apiFetch(`/pets/set_active/${petName}`, { method: 'POST' });
      toast.success(`${petName} Synced to Core`);
      await refreshUser();
    } catch (err) {
      toast.error(err.message || 'Sync failed');
    }
  };

  if (userLoading) return (
    <div className="p-10 flex flex-col items-center justify-center min-h-[60vh]">
       <Loader2 className="animate-spin text-brand-neon/20 mb-4" size={32} />
       <p className="text-slate-600 text-[10px] font-black uppercase tracking-widest">Scanning Pod Signatures...</p>
    </div>
  );
  
  if (!user) return null;

  return (
    <div className="pb-24 pt-6 px-4 max-w-lg mx-auto">
      <section className="mb-8 text-center relative">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 bg-brand-neon/5 blur-[60px] rounded-full pointer-events-none" />
        <h1 className="text-2xl font-black uppercase tracking-[0.3em] mb-2 text-white">Hatchery</h1>
        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest opacity-60">Nanobotic Lifeform Management</p>
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
              {tab === 'eggs' ? <Egg size={14} /> : <Zap size={14} />}
              <span>{tab === 'eggs' ? `PODS (${user.eggs?.length || 0})` : 'PET SQUAD'}</span>
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
              <EmptyState icon={Egg} message="No pods detected. High-tier eggs are generated via the Elite Pass." />
            )}
          </motion.section>
        ) : (
          <motion.section 
            key="pet-grid"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="grid grid-cols-2 gap-3"
          >
            {user.pets && user.pets.length > 0 ? (
              user.pets.map((pet) => (
                <PetCard 
                  key={pet.name} 
                  pet={pet} 
                  isActive={user.current_pet === pet.name}
                  onSelect={() => handleSetPet(pet.name)}
                />
              ))
            ) : (
              <div className="col-span-2">
                <EmptyState icon={Zap} message="No companions active. Purchase support units in the Shop." />
              </div>
            )}
          </motion.section>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {hatchingResult && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-brand-midnight/90 backdrop-blur-xl">
            <motion.div 
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="w-full max-w-sm"
            >
              <div className="text-center mb-8">
                 <h3 className="text-brand-neon font-black uppercase tracking-[0.4em] text-sm mb-2">Lifeform Detected</h3>
                 <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Integrating personality to matrix</p>
              </div>

              <div className="relative">
                <div className="absolute -inset-10 bg-brand-neon/10 blur-[100px] rounded-full animate-pulse" />
                <Card character={hatchingResult} />
              </div>

              <button 
                onClick={() => setHatchingResult(null)}
                className="w-full mt-12 py-5 rounded-2xl bg-white text-brand-midnight font-black uppercase text-[11px] tracking-[0.3em] active:scale-95 transition-all shadow-xl"
              >
                Close Portal
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
