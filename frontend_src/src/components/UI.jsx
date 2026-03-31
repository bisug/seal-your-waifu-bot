import React, { useState, createContext, useContext, useEffect, useCallback, useMemo, memo, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Info, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { apiFetch } from '../api';

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
          <span className="text-white/80 tabular-nums">{current.toLocaleString()} / {total.toLocaleString()}</span>
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

/**
 * Standardized API Hook for managed loading/error/data states.
 * Includes optional caching and automatic dependency tracking.
 */
export const useApi = (endpoint, options = {}, deps = []) => {
  const [data, setData] = useState(options.initialData || null);
  const [loading, setLoading] = useState(!options.manual);
  const [error, setError] = useState(null);

  const optionsRef = useRef(options);
  
  // Shallow array comparison utility
  const isShallowEqual = (obj1, obj2) => {
    const keys1 = Object.keys(obj1);
    const keys2 = Object.keys(obj2);
    if (keys1.length !== keys2.length) return false;
    for (let key of keys1) {
        if (obj1[key] !== obj2[key]) return false;
    }
    return true;
  };

  if (!isShallowEqual(optionsRef.current, options)) {
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
export const Modal = ({ character, onClose }) => {
    // Audit: Scroll Lock for background content
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

    const rarityColors = {
        'Common': 'from-slate-500/20 to-slate-900',
        'Rare': 'from-blue-500/20 to-slate-900',
        'Epic': 'from-purple-500/20 to-slate-900',
        'Legendary': 'from-amber-500/20 to-slate-900',
        'Mythical': 'from-red-500/20 to-slate-900',
        'Celestial': 'from-cyan-400/20 to-slate-900',
    };

    const glowColors = {
        'Common': 'shadow-slate-500/20',
        'Rare': 'shadow-blue-500/40',
        'Epic': 'shadow-purple-500/40',
        'Legendary': 'shadow-amber-500/40',
        'Mythical': 'shadow-red-500/40',
        'Celestial': 'shadow-cyan-400/50 neon-shadow',
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-end justify-center px-4 pb-12 pt-20"
        >
            <div className="absolute inset-0 bg-brand-midnight/80 backdrop-blur-md" onClick={onClose} />
            
            <motion.div
                initial={{ y: "100%" }}
                animate={{ y: 0 }}
                exit={{ y: "100%" }}
                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                className={`relative w-full max-w-sm glass-panel rounded-t-[2.5rem] overflow-hidden border-t-2 border-x border-white/20 flex flex-col pt-2 bg-gradient-to-b ${rarityColors[character.rarity] || 'from-slate-800/10 to-slate-900'}`}
            >
                <div className="w-12 h-1.5 bg-white/20 rounded-full mx-auto mb-4" />
                
                <button 
                  onClick={onClose}
                  className="absolute top-3 right-3 p-1.5 rounded-full bg-white/5 text-white/50 hover:text-white transition-colors"
                >
                    <X size={18} />
                </button>

                <div className="px-6 pb-8 overflow-y-auto">
                    <div className={`aspect-[4/5] rounded-3xl overflow-hidden border border-white/10 mb-6 shadow-[0_0_50px_rgba(0,0,0,0.5)] ${glowColors[character.rarity]}`}>
                        <img 
                          src={character.img_url} 
                          alt={character.name}
                          className="w-full h-full object-cover"
                        />
                    </div>

                    <div className="space-y-4 text-left">
                        <div>
                            <span className="px-2 py-1 rounded-md bg-white/10 text-[10px] font-black uppercase tracking-[0.2em] text-brand-neon border border-white/10 backdrop-blur-md">
                                {character.rarity}
                            </span>
                            <h2 className="text-2xl font-black mt-2 leading-tight uppercase tracking-tight text-white drop-shadow-sm line-clamp-2">{character.name}</h2>
                            <p className="text-slate-400 font-medium italic text-xs tracking-wide truncate">{character.anime}</p>
                        </div>

                        <div className="grid grid-cols-2 gap-3 pt-3 border-t border-white/5">
                            <div className="space-y-0.5">
                                <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Global ID</p>
                                <p className="font-mono text-xs text-brand-neon">#{character.id}</p>
                            </div>
                            <div className="space-y-0.5">
                                <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Duplicates</p>
                                <p className="font-bold text-xs">x{character.count || 1}</p>
                            </div>
                        </div>

                        {character.count > 1 && (
                            <button 
                              onClick={async () => {
                                try {
                                    const confirm = window.confirm(`Recycle 1 x ${character.name} for Zenith?`);
                                    if (!confirm) return;
                                    await apiFetch('/recycle', { 
                                        method: 'POST', 
                                        body: JSON.stringify([character.id]) 
                                    });
                                    toast.success('Nexus Fusion Complete');
                                    onClose();
                                    window.dispatchEvent(new CustomEvent('user-data-refresh'));
                                } catch (err) {
                                    toast.error(err.message || 'Fusion failed');
                                }
                              }}
                              className="w-full py-2.5 rounded-lg bg-brand-accent/10 border border-brand-accent/20 text-brand-accent text-[10px] font-black uppercase tracking-widest hover:bg-brand-accent/20 transition-all flex items-center justify-center space-x-2"
                            >
                                <Zap size={12} />
                                <span>Recycle Duplicate</span>
                            </button>
                        )}
                        
                        <div className="flex items-center space-x-2 p-2.5 rounded-lg bg-white/5 border border-white/5 text-[9px] text-slate-400 font-medium italic">
                            <Info size={12} className="text-brand-neon shrink-0" />
                            <span>Captured in group by this collector.</span>
                        </div>
                    </div>
                </div>
                
                <div className="px-5 pb-5 pt-1">
                    <button 
                      onClick={onClose}
                      className="w-full py-3 rounded-xl bg-white text-brand-midnight font-black uppercase tracking-widest text-[10px] hover:scale-[1.02] transition-transform active:scale-95"
                    >
                        CLOSE DETAIL
                    </button>
                </div>
            </motion.div>
        </motion.div>
    );
};

/**
 * Unified Character/Item Card with rarity color coding.
 * Memoized to prevent redundant re-renders in large grids.
 */
export const Card = memo(({ character, onClick }) => {
    const [imgSrc, setImgSrc] = useState(character.img_url);
    const [isLoaded, setIsLoaded] = useState(false);
    
    const DEFAULT_AVATAR = 'https://files.catbox.moe/2hsawz.jpg';

    const rarityColors = {
        'Common': 'border-slate-500/30 shadow-slate-500/10',
        'Rare': 'border-blue-500/30 shadow-blue-500/20',
        'Epic': 'border-purple-500/30 shadow-purple-500/20',
        'Legendary': 'border-amber-500/30 shadow-amber-500/20',
        'Mythical': 'border-red-500/30 shadow-red-500/20',
        'Celestial': 'border-cyan-400/40 shadow-cyan-400/30 neon-shadow',
    };

    const getRarityClass = (rarity) => rarityColors[rarity] || 'border-slate-700/20 shadow-slate-700/5';

    const handleImageError = () => {
        if (imgSrc !== DEFAULT_AVATAR) {
            setImgSrc(DEFAULT_AVATAR);
        }
    };

    const handleClick = () => {
        window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
        if (onClick) onClick();
    };

    return (
        <motion.div
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleClick}
            className={`cursor-pointer overflow-hidden rounded-2xl glass-panel border transition-all ${getRarityClass(character.rarity)}`}
        >
            <div className="aspect-[3/4] relative bg-slate-900/50">
                {!isLoaded && (
                    <div className="absolute inset-0 animate-pulse bg-gradient-to-r from-transparent via-white/10 to-transparent" />
                )}
                <img
                    src={imgSrc || DEFAULT_AVATAR}
                    alt={character.name}
                    className={cn(
                        "w-full h-full object-cover transition-all duration-700",
                        isLoaded ? "scale-100 blur-0 opacity-100" : "scale-110 blur-xl opacity-0"
                    )}
                    onLoad={() => setIsLoaded(true)}
                    onError={() => setImgSrc(DEFAULT_AVATAR)}
                    loading="lazy"
                />
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-brand-midnight via-brand-midnight/60 to-transparent p-2.5 pt-8 text-left">
                    <div className="flex justify-between items-end">
                        <div className="flex-1 truncate pr-1">
                             <p className="text-[8px] font-black text-brand-neon uppercase tracking-widest mb-0.5 opacity-90 drop-shadow-[0_0_8px_rgba(0,255,255,0.4)]">{character.rarity}</p>
                             <h3 className="text-[11px] font-black truncate leading-none uppercase tracking-tight text-white/95">{character.name}</h3>
                        </div>
                        {character.count > 1 && (
                            <span className="ml-1 bg-brand-neon text-brand-midnight text-[8px] font-black px-1.5 py-0.5 rounded-sm shadow-lg shadow-brand-neon/20 ring-1 ring-white/10">x{character.count}</span>
                        )}
                    </div>
                </div>
            </div>
        </motion.div>
    );
});
