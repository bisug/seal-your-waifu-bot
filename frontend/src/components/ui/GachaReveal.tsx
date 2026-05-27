import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Character } from '../../context/UserContext';
import { RARITY_VISUALS } from '../../constants/rarities';

interface GachaRevealProps {
    character: Character | null;
    onClose: () => void;
}

export const GachaReveal = ({ character, onClose }: GachaRevealProps) => {
    useEffect(() => {
        if (character) {
            window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
            // Play a sound or additional heavy haptic if available
        }
    }, [character]);

    if (!character) return null;

    const visuals = (RARITY_VISUALS as any)[character.rarity] || RARITY_VISUALS['Common'];
    const isSpecial = ['Legendary', 'Cosmic', 'Exclusive', 'Limited Edition'].includes(character.rarity);

    return (
        <AnimatePresence>
            <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-brand-midnight/90 backdrop-blur-xl"
                onClick={onClose}
            >
                {/* Background Rays */}
                <motion.div 
                    initial={{ scale: 0, rotate: -45 }}
                    animate={{ scale: 2, rotate: 0 }}
                    transition={{ duration: 10, ease: "linear", repeat: Infinity }}
                    className="absolute inset-0 pointer-events-none opacity-20"
                    style={{
                        background: 'conic-gradient(from 0deg, transparent 0 45deg, rgba(255,255,255,0.1) 45deg 90deg, transparent 90deg 135deg, rgba(255,255,255,0.1) 135deg 180deg, transparent 180deg 225deg, rgba(255,255,255,0.1) 225deg 270deg, transparent 270deg 315deg, rgba(255,255,255,0.1) 315deg 360deg)'
                    }}
                />

                <motion.div 
                    initial={{ scale: 0.5, y: 50, opacity: 0 }}
                    animate={{ scale: 1, y: 0, opacity: 1 }}
                    transition={{ type: "spring", damping: 15, stiffness: 100 }}
                    className={`relative w-full max-w-sm aspect-[3/4] rounded-3xl overflow-hidden shadow-2xl ${visuals.glow}`}
                    onClick={(e) => e.stopPropagation()}
                >
                    <img 
                        src={character.img_url} 
                        alt={character.name}
                        className="absolute inset-0 w-full h-full object-cover"
                    />
                    
                    <div className="absolute inset-0 bg-gradient-to-t from-brand-midnight via-transparent to-black/30" />
                    
                    <motion.div 
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.5 }}
                        className="absolute bottom-0 inset-x-0 p-6 flex flex-col items-center text-center"
                    >
                        <span className={`text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-full mb-2 ${visuals.text} ${visuals.bg} border ${visuals.border}`}>
                            {character.rarity}
                        </span>
                        <h2 className="text-2xl font-black text-white uppercase tracking-tight drop-shadow-lg mb-4">
                            {character.name}
                        </h2>
                        
                        <button 
                            onClick={onClose}
                            className="w-full py-4 bg-white text-brand-midnight font-black uppercase tracking-widest text-[11px] rounded-xl shadow-lg active:scale-95 transition-transform"
                        >
                            Continue
                        </button>
                    </motion.div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
};
