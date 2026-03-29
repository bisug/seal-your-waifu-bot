import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Info } from 'lucide-react';

/**
 * Animated Progress Bar for XP, Health, or Pass levels.
 */
export const ProgressBar = ({ current, total, color = "bg-brand-neon", label }) => {
  const percentage = Math.min(100, Math.max(0, (current / total) * 100));

  return (
    <div className="w-full space-y-1">
      {label && (
        <div className="flex justify-between text-xs font-medium text-slate-400 px-1 uppercase tracking-widest">
          <span>{label}</span>
          <span>{current.toLocaleString()} / {total.toLocaleString()}</span>
        </div>
      )}
      <div className="h-2 w-full bg-slate-800/50 rounded-full overflow-hidden border border-white/5">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1, ease: 'easeOut' }}
          className={`h-full ${color} neon-shadow shadow-current transition-all`}
        />
      </div>
    </div>
  );
};

/**
 * Cinematic Detail Modal
 */
export const Modal = ({ character, onClose }) => {
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
                className={`relative w-full max-w-md glass-panel rounded-3xl overflow-hidden border-t-2 border-x border-white/10 flex flex-col pt-2 bg-gradient-to-b ${rarityColors[character.rarity] || 'from-slate-800/10 to-slate-900'}`}
            >
                <div className="w-12 h-1.5 bg-white/10 rounded-full mx-auto mb-4" />
                
                <button 
                  onClick={onClose}
                  className="absolute top-4 right-4 p-2 rounded-full bg-white/5 text-white/50 hover:text-white transition-colors"
                >
                    <X size={20} />
                </button>

                <div className="px-6 pb-6 overflow-y-auto">
                    <div className={`aspect-[3/4] rounded-2xl overflow-hidden border-2 border-white/5 mb-6 shadow-2xl ${glowColors[character.rarity]}`}>
                        <img 
                          src={character.img_url} 
                          alt={character.name}
                          className="w-full h-full object-cover"
                        />
                    </div>

                    <div className="space-y-4 text-left">
                        <div>
                            <span className="px-2 py-0.5 rounded-lg bg-white/10 text-[10px] font-black uppercase tracking-widest text-brand-neon border border-white/5">
                                {character.rarity}
                            </span>
                            <h2 className="text-2xl font-black mt-2 leading-tight uppercase tracking-tight">{character.name}</h2>
                            <p className="text-slate-400 font-medium italic text-sm">{character.anime}</p>
                        </div>

                        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/5">
                            <div className="space-y-1">
                                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Global ID</p>
                                <p className="font-mono text-sm text-brand-neon">#{character.id}</p>
                            </div>
                            <div className="space-y-1">
                                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Duplicates</p>
                                <p className="font-bold text-sm">x{character.count || 1}</p>
                            </div>
                        </div>
                        
                        <div className="flex items-center space-x-2 p-3 rounded-xl bg-white/5 border border-white/5 text-[10px] text-slate-400 font-medium italic">
                            <Info size={14} className="text-brand-neon shrink-0" />
                            <span>This character was captured in a group chat by this collector.</span>
                        </div>
                    </div>
                </div>
                
                <div className="px-6 pb-6 pt-2">
                    <button 
                      onClick={onClose}
                      className="w-full py-4 rounded-2xl bg-white text-brand-midnight font-black uppercase tracking-widest text-xs hover:scale-[1.02] transition-transform active:scale-95"
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
 */
export const Card = ({ character, onClick }) => {
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
                    src={imgSrc} 
                    alt={character.name}
                    className={`w-full h-full object-cover transition-opacity duration-300 ${isLoaded ? 'opacity-100' : 'opacity-0'}`}
                    onLoad={() => setIsLoaded(true)}
                    onError={handleImageError}
                    loading="lazy"
                />
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-brand-midnight/90 to-transparent p-2.5 pt-6 text-left">
                    <div className="flex justify-between items-end">
                        <div className="flex-1 truncate">
                             <p className="text-[8px] font-black text-brand-neon uppercase tracking-widest mb-0.5 opacity-80">{character.rarity}</p>
                             <h3 className="text-[11px] font-bold truncate leading-tight uppercase tracking-tighter">{character.name}</h3>
                        </div>
                        {character.count > 1 && (
                            <span className="ml-1 bg-brand-neon text-brand-midnight text-[8px] font-black px-1 rounded-sm shadow-sm">x{character.count}</span>
                        )}
                    </div>
                </div>
            </div>
        </motion.div>
    );
};
