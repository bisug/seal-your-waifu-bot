import React, { memo, forwardRef } from 'react';
import { CheckCircle2, Gem, ImageOff, Hash } from 'lucide-react';
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

    const rarityLabel = character.rarity.replace(/[\u2700-\u27bf]|[\u2190-\u21ff]|[\u2000-\u206f]|[\u2600-\u26ff]|[\u2b00-\u2bff]|[\u00a0-\u00bf]|\u2013|\u2014/g, '').trim().toUpperCase();
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
    const showPrice = hasPrice && !character.owned && !soldOut;
    const characterId = String(character.id || '');

    const getRarityVariant = (rarity: string) => {
        const r = rarity.toLowerCase();
        if (r.includes('common')) return 'secondary';
        if (r.includes('uncommon')) return 'success';
        if (r.includes('rare')) return 'rare';
        if (r.includes('epic')) return 'epic';
        if (r.includes('legendary') || r.includes('limited')) return 'premium';
        return 'primary';
    };

    const rarityVariant = getRarityVariant(rarityLabel);

    return (
        <motion.div
            ref={ref as any}
            whileHover={{ y: -6 }}
            whileTap={{ scale: 0.96 }}
            onClick={handleClick}
            className={cn(
                "relative rounded-xl overflow-hidden aspect-[3/4.2] group cursor-pointer select-none",
                "bg-[#0a0a0c] border border-white/[0.04] shadow-xl transition-all duration-300",
                "hover:border-brand-accent/30 hover:shadow-[0_12px_40px_rgba(0,0,0,0.4)]",
                soldOut && "border-danger/20"
            )}
        >
            <div className="absolute inset-0 z-10 pointer-events-none transition-opacity duration-300 opacity-0 group-hover:opacity-100">
                <div className="absolute top-2 left-2 w-3 h-3 border-t-2 border-l-2 border-brand-accent/40 rounded-tl-sm" />
                <div className="absolute top-2 right-2 w-3 h-3 border-t-2 border-r-2 border-brand-accent/40 rounded-tr-sm" />
                <div className="absolute bottom-2 left-2 w-3 h-3 border-b-2 border-l-2 border-brand-accent/40 rounded-bl-sm" />
                <div className="absolute bottom-2 right-2 w-3 h-3 border-b-2 border-r-2 border-brand-accent/40 rounded-br-sm" />
            </div>

            <div className="absolute inset-0 bg-brand-surface shimmer opacity-[0.05]" />

            {!imgError ? (
                <img
                    src={character.img_url || 'https://files.catbox.moe/2hsawz.jpg'}
                    alt={character.name}
                    loading="lazy"
                    decoding="async"
                    onError={() => setImgError(true)}
                    className={cn(
                        "absolute inset-0 w-full h-full object-cover transition-all duration-700 group-hover:scale-110 group-hover:brightness-110",
                        soldOut && "grayscale contrast-125 opacity-30"
                    )}
                />
            ) : (
                <div className="absolute inset-0 bg-[#08080a] flex flex-col items-center justify-center">
                    <ImageOff size={24} className="text-neutral-800" />
                </div>
            )}
            
            <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent opacity-90 transition-opacity duration-300 group-hover:opacity-80" />
            <div className="absolute inset-0 bg-scanline opacity-[0.02] pointer-events-none" />

            <div className="absolute left-2.5 top-2.5 z-20 flex flex-col gap-1.5">
                {characterId && (
                    <div className="flex items-center gap-1.5 rounded-md bg-black/60 px-2 py-1 text-[9px] font-black text-white/80 backdrop-blur-md border border-white/[0.05] font-mono shadow-lg group-hover:border-brand-accent/20 transition-colors">
                        <Hash size={10} className="text-brand-accent/60" />
                        <span className="tabular-nums tracking-tighter">{characterId}</span>
                    </div>
                )}
                {character.owned && (
                    <div className="w-6 h-6 rounded-md bg-success text-white flex items-center justify-center shadow-lg border border-success/20 animate-in">
                        <CheckCircle2 size={14} />
                    </div>
                )}
            </div>

            <div className="absolute bottom-0 inset-x-0 p-3.5 space-y-2 z-20">
                <div className="min-w-0">
                    <h3 className="text-xs font-black text-white leading-tight line-clamp-1 uppercase tracking-tight group-hover:text-brand-accent transition-colors duration-300 drop-shadow-md">
                        {character.name}
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                        <Badge variant={rarityVariant} size="xs" className="px-1.5 py-0.5 rounded-sm border-none bg-opacity-80 backdrop-blur-sm">
                            {rarityLabel || 'STANDARD'}
                        </Badge>
                    </div>
                </div>

                <div className="flex items-center justify-between gap-2 pt-0.5">
                    {soldOut ? (
                        <Badge variant="danger" size="xs" className="px-2 py-0.5 rounded-sm font-black tracking-widest border-none">
                            DEPLETED
                        </Badge>
                    ) : character.owned && copyCount > 1 ? (
                        <Badge variant="success" size="xs" className="px-2 py-0.5 rounded-sm font-black border-none bg-emerald-500/20 text-emerald-300">
                            x{copyCount} SECURED
                        </Badge>
                    ) : showPrice ? (
                        <div className="flex items-center gap-1.5 rounded-md bg-brand-accent text-white px-2.5 py-1 text-[10px] font-black tabular-nums shadow-[0_0_15px_rgba(59,130,246,0.35)] group-hover:scale-105 transition-transform duration-300">
                            <Gem size={10} fill="currentColor" />
                            {formatNumber(character.zenith_price)}
                        </div>
                    ) : <div />}
                </div>
            </div>
        </motion.div>
    );
}));
