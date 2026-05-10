import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { cn } from '../utils';
import { RARITY_VISUALS } from './Rarity';

export const Modal = ({ character, onClose, actions }) => {
    useEffect(() => {
        if (character) {
            document.body.classList.add('no-scroll');
            return () => document.body.classList.remove('no-scroll');
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
                    <div className="absolute top-[-20%] left-[-20%] w-[80%] h-[80%] bg-brand-accent/10 blur-[150px] rounded-full" />
                    <div className="absolute bottom-[-20%] right-[-20%] w-[80%] h-[80%] bg-brand-accent/5 blur-[150px] rounded-full" />
                </div>

                <div className="absolute inset-0" onClick={onClose} />

                <motion.div 
                    initial={{ scale: 0.95, opacity: 0, y: 100 }}
                    animate={{ scale: 1, opacity: 1, y: 0 }}
                    exit={{ scale: 0.95, opacity: 0, y: 100 }}
                    transition={{ type: "spring", damping: 28, stiffness: 220 }}
                    className="relative w-[98vw] max-w-[650px] h-[96vh] bg-brand-midnight sm:border border-white/10 rounded-[3.5rem] overflow-hidden shadow-[0_0_150px_rgba(0,0,0,0.8)] flex flex-col"
                >
                    {/* Floating Close Button */}
                    <button 
                        onClick={onClose} 
                        className="absolute top-6 right-6 z-50 w-11 h-11 rounded-2xl bg-brand-midnight/60 backdrop-blur-xl border border-white/10 flex items-center justify-center text-white/50 active:scale-95 transition-all hover:text-white"
                    >
                        <X size={24} />
                    </button>

                    <div className="flex-1 overflow-y-auto no-scrollbar">
                        {/* Hero Section */}
                        <div className="relative w-full bg-slate-900/50 group" style={{ height: 'min(55vh, 420px)' }}>
                            <img 
                                src={character.img_url} 
                                className="w-full h-full object-contain p-2" 
                                alt={character.name} 
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-brand-midnight via-brand-midnight/40 to-transparent opacity-100" />
                            
                            <div className="absolute bottom-10 left-8 right-8">
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
                                <h2 className="text-[clamp(2rem,10vw,3.5rem)] font-black uppercase italic leading-[0.85] text-white tracking-tighter drop-shadow-lg mb-4">{character.name}</h2>
                                <p className="text-[clamp(0.6rem,3vw,0.8rem)] font-bold text-slate-400 uppercase tracking-[0.5em]">{character.anime}</p>
                            </div>
                        </div>

                        {/* Details Area */}
                        <div className="px-8 pb-12 space-y-10">
                            <div className="grid grid-cols-2 gap-2.5">
                                <div className="bg-white/[0.03] border border-white/5 p-3.5 rounded-2xl">
                                    <p className="text-[8px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Status</p>
                                    <p className={cn("text-[11px] font-black tracking-wider", character.owned ? "text-brand-accent" : "text-brand-accent")}>
                                        {character.owned ? "COLLECTED" : "AVAILABLE"}
                                    </p>
                                </div>
                                <div className="bg-white/[0.03] border border-white/5 p-4 rounded-2xl">
                                    <p className="text-[8px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Quantity</p>
                                    <p className="text-[11px] font-black text-white">{character.count > 0 ? `Batch x${character.count}` : "Unique"}</p>
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
