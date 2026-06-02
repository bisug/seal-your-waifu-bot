import React, { memo, useEffect, forwardRef } from 'react';
import { Gem, Shield } from 'lucide-react';
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
    const hasPrice = typeof character.zenith_price === 'number' && character.zenith_price > 0;

    return (
        <div
            ref={ref}
            onClick={handleClick}
            className={cn(
                "relative rounded-xl overflow-hidden aspect-[3/4] group cursor-pointer select-none",
                "bg-brand-deep border border-white/5 active:scale-[0.98] transition-all duration-200"
            )}
        >
            {!imgError ? (
                <img
                    src={character.img_url || 'https://files.catbox.moe/2hsawz.jpg'}
                    alt={character.name}
                    loading="lazy"
                    decoding="async"
                    onError={() => setImgError(true)}
                    className="absolute inset-0 w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                />
            ) : (
                <div className="absolute inset-0 bg-brand-deep flex flex-col items-center justify-center">
                    <Shield size={24} className="text-neutral-800" />
                </div>
            )}
            
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-80" />
            
            {/* Top Bar Indicators */}
            <div className="absolute top-2 left-2 right-2 flex justify-between items-start pointer-events-none">
                <div className="px-2 py-1 rounded bg-black/60 backdrop-blur-sm border border-white/10">
                    <span className="text-[10px] font-semibold text-neutral-300">
                        {rarityLabel}
                    </span>
                </div>

                {character.owned ? (
                    <div className="px-2 py-1 rounded bg-emerald-500 text-white shadow-sm">
                        <span className="text-[10px] font-bold">
                            Owned
                        </span>
                    </div>
                ) : character.count > 1 && (
                    <div className="px-2 py-1 rounded bg-brand-accent text-white shadow-sm">
                        <span className="text-[10px] font-bold tabular-nums">
                            x{character.count}
                        </span>
                    </div>
                )}
            </div>

            {/* Bottom Content Area */}
            <div className="absolute bottom-0 inset-x-0 p-3">
                <h3 className="text-xs font-semibold text-white leading-tight line-clamp-1">
                    {character.name}
                </h3>
                {hasPrice && (
                    <div className="mt-1 inline-flex items-center gap-1 rounded bg-black/50 px-1.5 py-0.5 text-[10px] font-bold text-white/90">
                        <Gem size={10} className="text-brand-accent" />
                        <span>{character.zenith_price} Zenith</span>
                    </div>
                )}
            </div>
        </div>
    );
}));
