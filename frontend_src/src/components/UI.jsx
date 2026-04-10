import React, { useState, createContext, useContext, useEffect, useCallback, useMemo, memo, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Info, CheckCircle2, AlertCircle, Loader2, Zap } from 'lucide-react';
import { apiFetch } from '../api';
import { toast } from 'react-hot-toast';
import { cn, formatNumber } from '../utils';

const RARITY_VISUALS = {
    'Common': { 
        bg: 'from-slate-500/20 to-slate-900', 
        glow: 'shadow-slate-500/10',
        text: 'text-slate-400',
        border: 'border-white/5'
    },
    'Medium': { 
        bg: 'from-emerald-500/20 to-slate-900', 
        glow: 'shadow-emerald-500/10',
        text: 'text-emerald-400',
        border: 'border-emerald-500/20'
    },
    'Rare': { 
        bg: 'from-blue-500/20 to-slate-900', 
        glow: 'shadow-blue-500/20',
        text: 'text-blue-400',
        border: 'border-blue-500/30'
    },
    'Legendary': { 
        bg: 'from-amber-500/30 to-slate-900', 
        glow: 'shadow-amber-500/30',
        text: 'text-amber-400',
        border: 'border-amber-500/40'
    },
    'Cosmic': { 
        bg: 'from-purple-500/40 to-slate-900', 
        glow: 'shadow-purple-500/40 neon-shadow',
        text: 'text-purple-400',
        border: 'border-purple-500/50'
    },
    'Exclusive': { 
        bg: 'from-rose-500/40 to-slate-900', 
        glow: 'shadow-rose-500/40 neon-shadow',
        text: 'text-rose-400',
        border: 'border-rose-500/50'
    },
    'Limited Edition': { 
        bg: 'from-orange-500/50 to-slate-900', 
        glow: 'shadow-orange-500/50 neon-shadow',
        text: 'text-orange-400',
        border: 'border-orange-500/60'
    },
    'Royal': { 
        bg: 'from-cyan-400/50 to-slate-900', 
        glow: 'shadow-cyan-400/50 neon-shadow',
        text: 'text-cyan-300',
        border: 'border-cyan-400/70'
    },
    'Antique': { 
        bg: 'from-yellow-200/40 to-slate-900', 
        glow: 'shadow-yellow-200/40 neon-shadow',
        text: 'text-yellow-200',
        border: 'border-yellow-200/50'
    },
    'Celestial': { 
        bg: 'from-white/40 to-slate-950', 
        glow: 'shadow-white/40 neon-shadow',
        text: 'text-white',
        border: 'border-white/80'
    },
};

/**
 * Animated Progress Bar for XP, Health, or Pass levels.
 */
export const ProgressBar = ({ current, total, color = "bg-brand-neon", label }) => {
  const percentage = Math.min(100, Math.max(0, (current / total) * 100));

  return (
    <div className="w-full space-y-1.5">
      {label && (
        <div className="flex justify-between items-end text-[10px] font-black text-slate-400 px-0.5 uppercase tracking-widest">
          <span className="opacity-70">{label}</span>
          <span className="text-white/80 tabular-nums">{formatNumber(current)} / {formatNumber(total)}</span>
        </div>
      )}
      <div className="h-2 w-full bg-slate-900/50 rounded-full overflow-hidden border border-white/10 p-[1px]">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1.5, ease: [0.34, 1.56, 0.64, 1] }}
          className={`h-full ${color} rounded-full neon-shadow shadow-current relative`}
        >
            <div className="absolute inset-0 bg-white/20 animate-pulse" />
        </motion.div>
      </div>
    </div>
  );
};

/**
 * Cinematic Skeleton Loaders
 */
export const Skeleton = ({ className }) => (
  <div className={`bg-white/5 overflow-hidden relative ${className}`}>
    <div className="absolute inset-0 animate-shimmer" />
  </div>
);

export const CardSkeleton = () => (
  <div className="rounded-2xl glass-panel border border-white/5 overflow-hidden">
    <div className="aspect-[3/4] p-3 flex flex-col justify-end space-y-2">
      <Skeleton className="h-2 w-1/3 rounded" />
      <Skeleton className="h-3 w-2/3 rounded" />
    </div>
  </div>
);

/**
 * Horizontal Scroll with Fade Mask
 */
export const ScrollArea = ({ children, className = "" }) => (
  <div className={`relative ${className}`}>
    <div className="scroll-fade-mask overflow-x-auto no-scrollbar flex space-x-2 py-1">
      {children}
    </div>
  </div>
);

/**
 * Branded Toast Notification System
 */
const ToastContext = createContext(null);

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'info') => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 3000);
  }, []);

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div className="fixed top-4 left-1/2 -translate-x-1/2 z-[300] w-full max-w-[280px] pointer-events-none flex flex-col items-center space-y-2">
        <AnimatePresence>
          {toasts.map(toast => (
            <motion.div
              key={toast.id}
              initial={{ y: -20, opacity: 0, scale: 0.9 }}
              animate={{ y: 0, opacity: 1, scale: 1 }}
              exit={{ y: -10, opacity: 0, scale: 0.95 }}
              className="glass-panel w-full px-4 py-3 rounded-2xl border border-white/10 shadow-2xl flex items-center space-x-3 pointer-events-auto"
            >
              <div className={toast.type === 'success' ? 'text-brand-neon' : toast.type === 'error' ? 'text-red-500' : 'text-brand-accent'}>
                {toast.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
              </div>
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-200 truncate pr-2">
                {toast.message}
              </span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => useContext(ToastContext);

// Shallow array comparison utility
function shallowEqual(obj1, obj2) {
  if (obj1 === obj2) return true;
  const keys1 = Object.keys(obj1 || {});
  const keys2 = Object.keys(obj2 || {});
  if (keys1.length !== keys2.length) return false;
  for (let key of keys1) {
      if (obj1[key] !== obj2[key]) return false;
  }
  return true;
}

/**
 * Standardized API Hook for managed loading/error/data states.
 * Includes optional caching and automatic dependency tracking.
 */
export const useApi = (endpoint, options = {}, deps = []) => {
  const [data, setData] = useState(options.initialData || null);
  const [loading, setLoading] = useState(!options.manual);
  const [error, setError] = useState(null);

  const optionsRef = useRef(options);
  
  if (!shallowEqual(optionsRef.current, options)) {
    optionsRef.current = options;
  }

  const execute = useCallback(async (overrides = {}) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch(endpoint, { ...optionsRef.current, ...overrides });
      setData(res);
      return res;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [endpoint]); // Safely drops the heavy JSON parse logic and binds to endpoint

  useEffect(() => {
    if (!optionsRef.current.manual) {
      execute();
    }
  }, deps);

  return { data, loading, error, execute, setData };
};

/**
 * Cinematic Detail Modal
 */
/**
 * Cinematic Detail Modal
 */
export const Modal = ({ character, onClose, actions }) => {
    useEffect(() => {
        if (character) {
            const scroller = document.querySelector('.app-scroller');
            if (scroller) scroller.style.overflow = 'hidden';
            return () => {
                const scroller = document.querySelector('.app-scroller');
                if (scroller) scroller.style.overflow = 'auto';
            };
        }
    }, [character]);

    if (!character) return null;

    return (
        <AnimatePresence>
            <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-[100] flex items-center justify-center bg-brand-midnight/95 backdrop-blur-2xl"
            >
                {/* Cinematic Ambient Glow */}
                <div className="absolute inset-0 overflow-hidden pointer-events-none">
                    <div className="absolute top-[-20%] left-[-20%] w-[80%] h-[80%] bg-brand-neon/10 blur-[150px] rounded-full" />
                    <div className="absolute bottom-[-20%] right-[-20%] w-[80%] h-[80%] bg-brand-accent/5 blur-[150px] rounded-full" />
                </div>

                <div className="absolute inset-0" onClick={onClose} />

                <motion.div 
                    initial={{ scale: 0.9, opacity: 0, y: 100 }}
                    animate={{ scale: 1, opacity: 1, y: 0 }}
                    exit={{ scale: 0.9, opacity: 0, y: 100 }}
                    transition={{ type: "spring", damping: 25, stiffness: 200 }}
                    className="relative w-full max-w-lg h-[100dvh] sm:h-auto sm:max-h-[90vh] bg-brand-midnight sm:border border-white/5 sm:rounded-[3rem] overflow-hidden shadow-[0_0_100px_rgba(0,0,0,0.5)] flex flex-col"
                >
                    {/* Floating Close Button */}
                    <button 
                        onClick={onClose} 
                        className="absolute top-8 right-8 z-50 w-12 h-12 rounded-2xl bg-brand-midnight/40 backdrop-blur-xl border border-white/10 flex items-center justify-center text-white/50 active:scale-95 transition-all hover:text-white"
                    >
                        <X size={24} />
                    </button>

                    <div className="flex-1 overflow-y-auto no-scrollbar">
                        {/* Hero Section */}
                        <div className="relative aspect-[4/5] sm:aspect-video w-full group">
                            <img 
                                src={character.img_url} 
                                className="w-full h-full object-cover" 
                                alt={character.name} 
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-brand-midnight via-brand-midnight/20 to-transparent" />
                            
                            <div className="absolute bottom-10 left-8 right-8">
                                <motion.div 
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={cn(
                                        "backdrop-blur-md border px-3 py-1 rounded-lg w-fit mb-4",
                                        RARITY_VISUALS[character.rarity]?.border || "border-white/10",
                                        RARITY_VISUALS[character.rarity]?.bg || "bg-white/10"
                                    )}
                                >
                                    <p className={cn(
                                        "text-[10px] font-black uppercase tracking-[0.3em]",
                                        RARITY_VISUALS[character.rarity]?.text || "text-white"
                                    )}>
                                        {character.rarity}
                                    </p>
                                </motion.div>
                                <h2 className="text-4xl sm:text-5xl font-black uppercase italic leading-none text-white tracking-tighter drop-shadow-2xl mb-2">{character.name}</h2>
                                <p className="text-[11px] font-bold text-slate-500 uppercase tracking-[0.3em]">{character.anime}</p>
                            </div>
                        </div>

                        {/* Details Area */}
                        <div className="px-8 pt-4 pb-12 space-y-8">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-white/[0.03] border border-white/5 p-5 rounded-3xl">
                                    <p className="text-[8px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Registry Status</p>
                                    <p className={cn("text-sm font-black", character.owned ? "text-brand-neon" : "text-brand-accent")}>
                                        {character.owned ? "COLLECTED" : "AVAILABLE"}
                                    </p>
                                </div>
                                <div className="bg-white/[0.03] border border-white/5 p-5 rounded-3xl">
                                    <p className="text-[8px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Harem Storage</p>
                                    <p className="text-sm font-black text-white">{character.count > 0 ? `BATCH x${character.count}` : "UNIQUE UNIT"}</p>
                                </div>
                            </div>

                            {actions && <div className="w-full">{actions}</div>}

                            <div className="opacity-40">
                                <div className="flex items-center space-x-2 text-slate-400 mb-3">
                                    <Info size={14} />
                                    <span className="text-[10px] font-black uppercase tracking-widest">Bio Archive Entry</span>
                                </div>
                                <p className="text-xs leading-relaxed italic text-slate-400 uppercase font-bold tracking-tight">
                                    The character {character.name} is from {character.anime}. 
                                    Adding them to your harem unlocks new possibilities.
                                </p>
                            </div>
                        </div>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
};

/**
 * Unified Character/Item Card
 */
export const Card = memo(({ character, onClick }) => {
    const isSpecial = ['Legendary', 'Cosmic', 'Exclusive', 'Limited Edition', 'Royal', 'Antique', 'Celestial'].includes(character.rarity);

    const handleClick = () => {
        window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
        if (onClick) onClick();
    };

    const visuals = RARITY_VISUALS[character.rarity] || RARITY_VISUALS['Common'];

    return (
        <motion.div
            whileHover={{ scale: 1.05, y: -5 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleClick}
            className={cn(
                "relative rounded-[2rem] overflow-hidden aspect-[2/3] group transition-all duration-500 cursor-pointer",
                "border bg-slate-900/60 backdrop-blur-xl shadow-2xl",
                visuals.border,
                visuals.glow,
                isSpecial && "ring-1 ring-white/10"
            )}
        >
            <img
                src={character.img_url || 'https://files.catbox.moe/2hsawz.jpg'}
                alt={character.name}
                decoding="async"
                className="w-full h-full object-cover grayscale-[0.2] group-hover:grayscale-0 transition-all duration-700 group-hover:scale-110"
            />
            
            {/* View Indicator Overlay */}
            <div className="absolute inset-0 bg-brand-midnight/40 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
                <div className="w-12 h-12 rounded-2xl bg-brand-neon/20 backdrop-blur-md border border-brand-neon/40 flex items-center justify-center text-brand-neon transform scale-50 group-hover:scale-100 transition-transform duration-500">
                    <Zap size={20} />
                </div>
            </div>

            <div className="absolute inset-0 bg-gradient-to-t from-brand-midnight via-transparent to-transparent opacity-80" />
            
            <div className="absolute bottom-4 inset-x-4">
                <p className="text-[10px] font-black uppercase text-white tracking-widest line-clamp-1 mb-1">
                    {character.name}
                </p>
                <div className="flex items-center space-x-1.5 opacity-60">
                    <div className={cn("w-1.5 h-1.5 rounded-full", isSpecial ? "animate-pulse" : "bg-slate-500", visuals.text.replace('text-', 'bg-'))} />
                    <span className={cn("text-[8px] font-bold uppercase tracking-widest", visuals.text)}>{character.rarity}</span>
                </div>
            </div>
            
            {character.count > 1 && (
                <div className="absolute top-4 right-4 px-2 py-1 rounded-xl bg-brand-neon text-brand-midnight text-[10px] font-black shadow-xl shadow-brand-neon/20">
                    x{character.count}
                </div>
            )}
        </motion.div>
    );
});

