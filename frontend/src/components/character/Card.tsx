import React, { memo, useEffect, forwardRef } from 'react';
import { Activity } from 'lucide-react';
import { cn } from '../../utils';
import { Character } from '../../context/UserContext';

interface CardProps {
    character: Character;
    onClick?: (character: Character) => void;
}

export const Card = memo(forwardRef<HTMLDivElement, CardProps>(({ character, onClick }, ref) => {
    const handleClick = () => {
        window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
        if (onClick) onClick(character);
    };

    const [imgError, setImgError] = React.useState(false);

    useEffect(() => {
        setImgError(false);
    }, [character.img_url]);

    return (
        <div
            ref={ref}
            onClick={handleClick}
            className={cn(
                "relative rounded-xl overflow-hidden aspect-[3/4] group cursor-pointer",
                "bg-slate-900 border border-white/5 active:scale-95 transition-transform duration-100"
            )}
        >
            {/* Main Character Image */}
            {!imgError ? (
                <img
                    src={character.img_url || 'https://files.catbox.moe/2hsawz.jpg'}
                    alt={character.name}
                    loading="lazy"
                    decoding="async"
                    onError={() => setImgError(true)}
                    className="absolute inset-0 w-full h-full object-cover object-top"
                />
            ) : (
                <div className="absolute inset-0 bg-slate-900 flex flex-col items-center justify-center space-y-1">
                    <Activity size={16} className="text-slate-700" />
                </div>
            )}
            
            {/* Simple Overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
            
            {/* Rarity Badge - Top Left */}
            <div className="absolute top-1.5 left-1.5 px-1.5 py-0.5 rounded bg-black/60 border border-white/10 z-20">
                <span className="text-[7px] font-bold uppercase tracking-wider text-slate-300">
                    {character.rarity.split(' ').pop()}
                </span>
            </div>

            {/* Count Badge - Top Right */}
            {character.count > 1 && (
                <div className="absolute top-1.5 right-1.5 px-1.5 py-0.5 rounded bg-brand-accent text-white text-[8px] font-black z-20">
                    {character.count}
                </div>
            )}

            {/* Bottom Content Area */}
            <div className="absolute bottom-0 inset-x-0 p-2">
                <h3 className="text-[9px] font-bold uppercase text-white tracking-tight leading-tight line-clamp-1">
                    {character.name}
                </h3>
            </div>
        </div>
    );
}));
