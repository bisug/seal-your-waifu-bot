import React, { memo, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Activity } from 'lucide-react';
import { cn } from '../utils';
import { RARITY_VISUALS } from './Rarity';

export const Card = memo(({ character, onClick }) => {
    const isSpecial = ['Legendary', 'Cosmic', 'Exclusive', 'Limited Edition', 'Royal', 'Antique', 'Celestial'].includes(character.rarity);

    const handleClick = () => {
        window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
        if (onClick) onClick(character);
    };

    const visuals = RARITY_VISUALS[character.rarity] || RARITY_VISUALS['Common'];
    const [imgError, setImgError] = React.useState(false);

    useEffect(() => {
        setImgError(false);
    }, [character.img_url]);

    return (
        <motion.div
            whileHover={{ scale: 1.02, y: -5 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleClick}
            className={cn(
                "relative rounded-[1.5rem] overflow-hidden aspect-[3/4] group transition-all duration-500 cursor-pointer",
                "border bg-slate-900 shadow-lg",
                visuals.border,
                visuals.glow,
                isSpecial && "ring-1 ring-white/20"
            )}
        >
            {/* Main Character Image */}
            {!imgError ? (
                <img
                    src={character.img_url || 'https://files.catbox.moe/2hsawz.jpg'}
                    alt={character.name}
                    decoding="async"
                    onError={() => setImgError(true)}
                    className="absolute inset-0 w-full h-full object-cover object-top transition-all duration-700 group-hover:scale-110"
                />
            ) : (
                <div className="absolute inset-0 bg-slate-900/40 flex flex-col items-center justify-center space-y-1 opacity-50">
                    <Activity size={18} className="text-slate-600 opacity-60" />
                    <span className="text-[7px] font-black uppercase tracking-[0.2em] text-slate-700 text-center">Missing</span>
                </div>
            )}
            
            {/* Cinematic Gradient Overlays */}
            <div className="absolute inset-0 bg-gradient-to-t from-brand-midnight via-transparent to-black/20" />
            
            {/* Rarity Badge - Top Left */}
            <div className={cn(
                "absolute top-2 left-2 px-1.5 py-0.5 rounded-full border backdrop-blur-md z-20 flex items-center space-x-1 shadow-lg",
                visuals.pill || 'bg-slate-700/40',
                visuals.border
            )}>
                <div className={cn("w-1 h-1 rounded-full", isSpecial ? "animate-pulse" : "", visuals.text.replace('text-', 'bg-'))} />
                <span className={cn("text-[7px] font-black uppercase tracking-widest", visuals.text)}>
                    {character.rarity}
                </span>
            </div>

            {/* Count Badge - Top Right */}
            {character.count > 1 && (
                <div className="absolute top-2 right-2 px-1.5 py-0.5 rounded-full bg-brand-midnight/60 backdrop-blur-md border border-white/10 text-white text-[8px] font-black z-20">
                    x{character.count}
                </div>
            )}

            {/* Bottom Content Area */}
            <div className="absolute bottom-0 inset-x-0 p-3 pt-8 bg-gradient-to-t from-brand-midnight to-transparent">
                <h3 className="text-[10px] font-black uppercase text-white tracking-[0.1em] leading-tight drop-shadow-md group-hover:text-brand-accent transition-colors line-clamp-2">
                    {character.name}
                </h3>
            </div>

            {/* Interaction Glow */}
            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
                <div className={cn("absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t opacity-40", visuals.bg.split(' ')[0])} />
            </div>
        </motion.div>
    );
});
