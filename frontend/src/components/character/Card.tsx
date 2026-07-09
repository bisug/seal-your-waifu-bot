import React, { memo, useEffect, forwardRef } from 'react';
import { CheckCircle2, Gem, Hash, ImageOff, ScanLine } from 'lucide-react';
import { cn, formatNumber } from '../../utils';
import { Character } from '../../context/UserContext';
import { Badge } from '../ui/Badge';
import { motion } from 'framer-motion';

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
    const statusLabel = soldOut ? 'DEPLETED' : character.owned ? 'LOCKED' : copyCount > 1 ? `x${copyCount}` : null;
    const showPrice = hasPrice && !character.owned && !soldOut;
    const characterId = String(character.id || '');

    return (
        <motion.div
            ref={ref as any}
            whileHover={{ y: -4 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleClick}
            className={cn(
                "relative rounded-md overflow-hidden aspect-[3/4.2] group cursor-pointer select-none",
                "bg-[#0a0a0c] border border-white/[0.05] shadow-lg transition-all duration-200",
                "hover:border-brand-accent/40 hover:shadow-brand-accent/10"
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
                        "absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-105",
                        soldOut && "grayscale contrast-125 opacity-40"
                    )}
                />
            ) : (
                <div className="absolute inset-0 bg-[#08080a] flex flex-col items-center justify-center">
                    <ImageOff size={20} className="text-neutral-900" />
                </div>
            )}
            
            {/* Tactical Overlays */}
            <div className="absolute inset-0 bg-gradient-to-t from-black via-black/30 to-transparent opacity-80" />
            <div className="absolute inset-0 bg-scanline opacity-[0.02] pointer-events-none" />

            {/* Corner Indicators */}
            <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <div className="w-1.5 h-1.5 border-t border-r border-brand-accent/60" />
            </div>
            <div className="absolute bottom-1 left-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <div className="w-1.5 h-1.5 border-b border-l border-brand-accent/60" />
            </div>

            {characterId && (
                <div className="absolute left-1.5 top-1.5 z-10">
                    <div className="flex items-center gap-1 rounded-sm bg-black/60 px-1.5 py-0.5 text-[8px] font-black text-white/70 backdrop-blur-md border border-white/[0.05] font-mono">
                        <span className="text-brand-accent/60">#</span>
                        <span className="tabular-nums">{characterId}</span>
                    </div>
                </div>
            )}

            <div className="absolute bottom-0 inset-x-0 p-2 space-y-1.5">
                <div className="min-w-0">
                    <h3 className="text-[10px] font-black text-white leading-tight line-clamp-1 uppercase tracking-tight group-hover:text-brand-accent transition-colors">
                        {character.name}
                    </h3>
                    <p className="text-[8px] font-bold text-neutral-500 truncate uppercase tracking-widest mt-0.5 leading-none">
                        {rarityLabel || 'STANDARD'}
                    </p>
                </div>

                <div className="flex items-center justify-between gap-1.5">
                    {statusLabel ? (
                        <Badge
                            variant={soldOut ? "danger" : character.owned ? "success" : "primary"}
                            size="xs"
                            className="rounded-xs border-none bg-opacity-90 py-0.5 px-1"
                        >
                            {character.owned && <CheckCircle2 size={8} />}
                            {statusLabel}
                        </Badge>
                    ) : <div />}

                    {showPrice && (
                        <div className="flex items-center gap-1 rounded-sm bg-brand-accent/10 px-1.5 py-0.5 text-[9px] font-black tabular-nums text-brand-accent border border-brand-accent/20">
                            <Gem size={8} />
                            {formatNumber(character.zenith_price)}
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
}));
