import React, { memo, useEffect, forwardRef } from 'react';
import { Shield } from 'lucide-react';
import { cn } from '../../utils';
import { Character } from '../../context/UserContext';

interface CardProps {
    character: Character;
    onClick?: (character: Character) => void;
}

export const Card = memo(forwardRef<HTMLDivElement, CardProps>(({ character, onClick }, ref) => {
    const handleClick = () => {
        window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
        if (onClick) onClick(character);
    };

    const [imgError, setImgError] = React.useState(false);

    useEffect(() => {
        setImgError(false);
    }, [character.img_url]);

    // Rarity name without emojis
    const rarityLabel = character.rarity.replace(/[\u2700-\u27bf]|[\u2190-\u21ff]|[\u2000-\u206f]|[\u2600-\u26ff]|[\u2b00-\u2bff]|[\u00a0-\u00bf]|\u2013|\u2014/g, '').trim();

    return (
        <div
            ref={ref}
            onClick={handleClick}
            className={cn(
                "relative rounded-lg overflow-hidden aspect-[3/4] group cursor-pointer select-none",
                "bg-zinc-900 border border-white/5 active:scale-[0.98] transition-all duration-200"
            )}
        >
            {!imgError ? (
                <img
                    src={character.img_url || 'https://files.catbox.moe/2hsawz.jpg'}
                    alt={character.name}
                    loading="lazy"
                    decoding="async"
                    onError={() => setImgError(true)}
                    className="absolute inset-0 w-full h-full object-cover grayscale-[0.1] group-hover:grayscale-0 transition-all duration-300"
                />
            ) : (
                <div className="absolute inset-0 bg-zinc-900 flex flex-col items-center justify-center">
                    <Shield size={16} className="text-zinc-800" />
                </div>
            )}
            
            <div className="absolute inset-0 bg-gradient-to-t from-zinc-950/80 via-transparent to-transparent opacity-60" />
            
            {/* Top Bar Indicators */}
            <div className="absolute top-1 left-1 right-1 flex justify-between items-start pointer-events-none">
                <div className="px-1.5 py-0.5 rounded-sm bg-zinc-950/80 border border-white/5">
                    <span className="text-[7px] font-bold text-zinc-400 uppercase tracking-widest">
                        {rarityLabel}
                    </span>
                </div>

                {character.count > 1 && (
                    <div className="px-1.5 py-0.5 rounded-sm bg-brand-accent border border-white/5">
                        <span className="text-[7px] font-bold text-white tabular-nums">
                            {character.count}
                        </span>
                    </div>
                )}
            </div>

            {/* Bottom Content Area */}
            <div className="absolute bottom-0 inset-x-0 p-2">
                <h3 className="text-[9px] font-bold text-zinc-100 leading-tight line-clamp-1 uppercase tracking-wider">
                    {character.name}
                </h3>
            </div>
        </div>
    );
}));
