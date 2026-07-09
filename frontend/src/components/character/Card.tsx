import React, { memo, useEffect, forwardRef } from 'react';
import { CheckCircle2, Gem, Hash, ImageOff } from 'lucide-react';
import { cn, formatNumber } from '../../utils';
import { Character } from '../../context/UserContext';
import { Badge } from '../ui/Badge';

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
    const statusLabel = soldOut ? 'SOLD OUT' : character.owned ? 'OWNED' : copyCount > 1 ? `x${copyCount}` : null;
    const showPrice = hasPrice && !character.owned && !soldOut;
    const characterId = String(character.id || '');

    return (
        <div
            ref={ref}
            onClick={handleClick}
            className={cn(
                "relative rounded-2xl overflow-hidden aspect-[3/4.2] group cursor-pointer select-none",
                "bg-brand-deep border border-white/5 active:scale-[0.98] transition-all duration-300",
                "hover:border-white/20 hover:shadow-[0_8px_30px_rgb(0,0,0,0.5)]"
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
                        "absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-110",
                        soldOut && "grayscale opacity-50"
                    )}
                />
            ) : (
                <div className="absolute inset-0 bg-brand-deep flex flex-col items-center justify-center">
                    <ImageOff size={24} className="text-neutral-800" />
                </div>
            )}
            
            <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent opacity-80 group-hover:opacity-90 transition-opacity" />

            {characterId && (
                <div className="absolute left-2.5 top-2.5 z-10">
                    <div className="flex items-center gap-1 rounded-lg bg-black/60 px-2 py-1 text-[9px] font-black text-white/90 backdrop-blur-md border border-white/10">
                        <Hash size={10} className="text-brand-accent" />
                        <span className="tabular-nums">{characterId}</span>
                    </div>
                </div>
            )}

            <div className="absolute bottom-0 inset-x-0 p-3 space-y-2">
                <div>
                    <h3 className="text-xs font-black text-white leading-tight line-clamp-2 uppercase tracking-tight drop-shadow-md group-hover:text-brand-accent transition-colors">
                        {character.name}
                    </h3>
                    <p className="text-[9px] font-bold text-neutral-400 truncate uppercase tracking-widest mt-0.5">
                        {rarityLabel || 'STANDARD'}
                    </p>
                </div>

                <div className="flex items-center justify-between gap-2">
                    {statusLabel ? (
                        <Badge
                            variant={soldOut ? "danger" : character.owned ? "success" : "primary"}
                            size="xs"
                            className="rounded-lg border-none bg-opacity-80"
                        >
                            {character.owned && <CheckCircle2 size={10} />}
                            {statusLabel}
                        </Badge>
                    ) : <div />}

                    {showPrice && (
                        <div className="flex items-center gap-1 rounded-lg bg-white/10 px-2 py-1 text-[10px] font-black tabular-nums text-white backdrop-blur-md">
                            <Gem size={10} className="text-brand-accent" />
                            {formatNumber(character.zenith_price)}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}));
