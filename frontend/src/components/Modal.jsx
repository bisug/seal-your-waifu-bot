import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { cn } from '../utils';
import { RARITY_VISUALS } from './Rarity';

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
                    className="relative w-[95vw] max-w-[400px] max-h-[min(94vh,620px)] bg-brand-midnight sm:border border-white/5 rounded-[2.5rem] overflow-hidden shadow-[0_0_100px_rgba(0,0,0,0.5)] flex flex-col"
                >
                    {/* Floating Close Button */}
                    <button 
                        onClick={onClose} 
                        className="absolute top-6 right-6 z-50 w-10 h-10 rounded-2xl bg-brand-midnight/60 backdrop-blur-xl border border-white/10 flex items-center justify-center text-white/50 active:scale-95 transition-all hover:text-white"
                    >
                        <X size={24} />
                    </button>

                    <div className="flex-1 overflow-y-auto no-scrollbar">
                        {/* Hero Section */}
                        <div className="relative aspect-[4/3] w-full bg-slate-900/50 group">
                            <img 
                                src={character.img_url} 
                                className="w-full h-full object-contain p-2" 
                                alt={character.name} 
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-brand-midnight via-transparent to-transparent" />
                            
                            <div className="absolute bottom-4 left-5 right-5">
                                <motion.div 
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={cn(
                                        "backdrop-blur-md border px-2 py-0.5 rounded-lg w-fit mb-1.5",
                                        RARITY_VISUALS[character.rarity]?.border || "border-white/10",
                                        RARITY_VISUALS[character.rarity]?.bg || "bg-white/10"
                                    )}
                                >
                                    <p className={cn(
                                        "text-[7px] font-black uppercase tracking-[0.3em]",
                                        RARITY_VISUALS[character.rarity]?.text || "text-white"
                                    )}>
                                        {character.rarity}
                                    </p>
                                </motion.div>
                                <h2 className="text-[clamp(1.25rem,5vw,1.5rem)] font-black uppercase italic leading-none text-white tracking-tighter drop-shadow-2xl mb-1">{character.name}</h2>
                                <p className="text-[clamp(0.45rem,2vw,0.5rem)] font-bold text-slate-500 uppercase tracking-[0.3em]">{character.anime}</p>
                            </div>
                        </div>

                        {/* Details Area */}
                        <div className="px-5 pb-8 space-y-5">
                            <div className="grid grid-cols-2 gap-2.5">
                                <div className="bg-white/[0.03] border border-white/5 p-3.5 rounded-2xl">
                                    <p className="text-[7px] font-bold text-slate-500 uppercase tracking-widest mb-1">Status</p>
                                    <p className={cn("text-[10px] font-black", character.owned ? "text-brand-neon" : "text-brand-accent")}>
                                        {character.owned ? "COLLECTED" : "AVAILABLE"}
                                    </p>
                                </div>
                                <div className="bg-white/[0.03] border border-white/5 p-3.5 rounded-2xl">
                                    <p className="text-[7px] font-bold text-slate-500 uppercase tracking-widest mb-1">Quantity</p>
                                    <p className="text-[10px] font-black text-white">{character.count > 0 ? `Batch x${character.count}` : "Unique"}</p>
                                </div>
                            </div>

                            {actions && <div className="w-full">{actions}</div>}
                        </div>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
};
