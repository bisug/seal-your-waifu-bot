import React, { memo, useEffect, forwardRef } from 'react';
import { CheckCircle2, Gem, Shield } from 'lucide-react';
import { cn, formatNumber } from '../../utils';
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

    const rarityLabel = character.rarity.replace(/[\u2700-\u27bf]|[\u2190-\u21ff]|[\u2000-\u206f]|[\u2600-\u26ff]|[\u2b00-\u2bff]|[\u00a0-\u00bf]|\u2013|\u2014/g, '').trim();
    const hasPrice = typeof character.zenith_price === 'number' && character.zenith_price > 0;
    const stockLimit = typeof character.stock_limit === 'number' ? character.stock_limit : null;
    const stockRemaining = typeof character.stock_remaining === 'number'
        ? character.stock_remaining
        : stockLimit !== null && typeof character.sold_count === 'number'
            ? Math.max(0, stockLimit - character.sold_count)
            : null;
    const hasStock = stockLimit !== null && stockRemaining !== null;
    const soldOut = character.sold_out || (hasStock && stockRemaining <= 0);
    const copyCount = Number(character.count || 0);
    const statusLabel = soldOut ? 'Sold out' : character.owned ? 'Owned' : copyCount > 1 ? `x${copyCount}` : null;
    const showPrice = hasPrice && !character.owned && !soldOut;

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
                    className={cn(
                        "absolute inset-0 w-full h-full object-cover transition-transform duration-300 group-hover:scale-105",
                        soldOut && "grayscale opacity-70"
                    )}
                />
            ) : (
                <div className="absolute inset-0 bg-brand-deep flex flex-col items-center justify-center">
                    <Shield size={24} className="text-neutral-800" />
                </div>
            )}
            
            <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-black/90 via-black/35 to-transparent" />
            {soldOut && (
                <div className="absolute inset-0 bg-black/15" />
            )}

            <div className="absolute bottom-0 inset-x-0 p-2">
                <h3 className="text-xs font-semibold text-white leading-tight line-clamp-1 drop-shadow">
                    {character.name}
                </h3>

                <div className="mt-1 flex min-w-0 items-center gap-1">
                    <span className="min-w-0 flex-1 truncate rounded bg-black/35 px-1.5 py-0.5 text-[9px] font-semibold text-neutral-300 backdrop-blur-sm">
                        {rarityLabel || 'Unknown'}
                    </span>

                    {statusLabel && (
                        <span className={cn(
                            "inline-flex shrink-0 items-center gap-1 rounded px-1.5 py-0.5 text-[9px] font-bold tabular-nums backdrop-blur-sm",
                            soldOut ? "bg-red-500/20 text-red-200" :
                            character.owned ? "bg-emerald-500/15 text-emerald-300" :
                            "bg-brand-accent/20 text-brand-accent"
                        )}>
                            {character.owned && <CheckCircle2 size={9} />}
                            {statusLabel}
                        </span>
                    )}

                    {showPrice && (
                        <span className="inline-flex shrink-0 items-center gap-0.5 rounded bg-black/35 px-1.5 py-0.5 text-[9px] font-bold tabular-nums text-white/90 backdrop-blur-sm">
                            <Gem size={9} className="text-brand-accent" />
                            {formatNumber(character.zenith_price)}
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
}));
