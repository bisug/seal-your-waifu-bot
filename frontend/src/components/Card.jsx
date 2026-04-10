import React, { memo } from 'react';
import { motion } from 'framer-motion';
import { Zap } from 'lucide-react';
import { cn } from '../utils';
import { RARITY_VISUALS } from './Rarity';

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
                className="w-full h-full object-cover object-top grayscale-[0.2] group-hover:grayscale-0 transition-all duration-700 group-hover:scale-110"
            />
            
            {/* View Indicator Overlay */}
            <div className="absolute inset-0 bg-brand-midnight/40 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
                <div className="w-12 h-12 rounded-2xl bg-brand-neon/20 backdrop-blur-md border border-brand-neon/40 flex items-center justify-center text-brand-neon transform scale-50 group-hover:scale-100 transition-transform duration-500">
                    <Zap size={20} />
                </div>
            </div>

            <div className="absolute inset-0 bg-gradient-to-t from-brand-midnight via-transparent to-transparent opacity-80" />
            
            <div className="absolute bottom-3 inset-x-3">
                <p className="text-[clamp(0.55rem,2.5vw,0.65rem)] font-black uppercase text-white tracking-widest line-clamp-1 mb-0.5">
                    {character.name}
                </p>
                <div className="flex items-center space-x-1 opacity-60">
                    <div className={cn("w-1 h-1 rounded-full", isSpecial ? "animate-pulse" : "bg-slate-500", visuals.text.replace('text-', 'bg-'))} />
                    <span className={cn("text-[clamp(0.45rem,2vw,0.5rem)] font-bold uppercase tracking-widest", visuals.text)}>{character.rarity}</span>
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
