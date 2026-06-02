import React, { useEffect, ReactNode } from 'react';
import { Gem, Package, ShieldCheck, Tag, X } from 'lucide-react';
import { cn, formatNumber } from '../../utils';
import { Character } from '../../context/UserContext';

interface ModalProps {
    character: Character | null;
    onClose: () => void;
    actions?: ReactNode;
}

export const Modal = ({ character, onClose, actions }: ModalProps) => {
    useEffect(() => {
        if (character) {
            document.body.style.overflow = 'hidden';
            return () => { document.body.style.overflow = 'unset'; };
        }
    }, [character]);

    if (!character) return null;

    const rarityLabel = character.rarity.replace(/[\u2700-\u27bf]|[\u2190-\u21ff]|[\u2000-\u206f]|[\u2600-\u26ff]|[\u2b00-\u2bff]|[\u00a0-\u00bf]|\u2013|\u2014/g, '').trim();
    const stockLimit = typeof character.stock_limit === 'number' ? character.stock_limit : null;
    const stockRemaining = typeof character.stock_remaining === 'number'
        ? character.stock_remaining
        : stockLimit !== null && typeof character.sold_count === 'number'
            ? Math.max(0, stockLimit - character.sold_count)
            : null;
    const hasStock = stockLimit !== null && stockRemaining !== null;
    const soldOut = character.sold_out || (hasStock && stockRemaining <= 0);
    const hasPrice = typeof character.zenith_price === 'number' && character.zenith_price > 0;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-3">
            <div className="absolute inset-0" onClick={onClose} />

            <div className="relative w-full max-w-sm max-h-[92vh] bg-brand-midnight rounded-2xl flex flex-col overflow-hidden shadow-2xl border border-white/10">
                <button
                    onClick={onClose}
                    className="absolute right-3 top-3 z-20 p-2 rounded-lg bg-black/45 text-neutral-300 border border-white/10 backdrop-blur-sm hover:text-white hover:bg-white/10 transition-colors"
                    aria-label="Close preview"
                >
                    <X size={18} />
                </button>

                <div className="relative min-h-[300px] flex-1 bg-brand-deep flex items-center justify-center overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-b from-black/25 via-transparent to-black/45" />
                    <img
                        src={character.img_url}
                        className="relative z-10 w-full h-full max-h-[58vh] object-contain p-5 drop-shadow-2xl"
                        alt={character.name}
                    />
                </div>

                <div className="shrink-0 border-t border-white/10 bg-brand-midnight/95 p-4 space-y-4 max-h-[44vh] overflow-y-auto no-scrollbar">
                    <div className="min-w-0">
                        <div className="mb-2 flex items-center gap-2">
                            <span className="inline-flex min-w-0 max-w-full items-center gap-1.5 rounded-lg bg-brand-accent/12 px-2 py-1 text-[10px] font-bold text-brand-accent">
                                <Tag size={11} />
                                <span className="truncate">{rarityLabel || 'Unknown rarity'}</span>
                            </span>
                        </div>
                        <h2 className="text-xl font-bold text-white leading-tight line-clamp-2">{character.name}</h2>
                        <p className="mt-1 text-sm font-medium text-neutral-400 line-clamp-1">{character.anime}</p>
                    </div>

                    <div className="grid grid-cols-3 gap-2">
                        <div className="min-w-0 rounded-xl border border-white/5 bg-brand-deep p-3">
                            <ShieldCheck size={15} className={cn("mb-2", character.owned ? "text-emerald-400" : "text-neutral-600")} />
                            <span className="block text-[10px] font-semibold text-neutral-500">Status</span>
                            <span className={cn("block truncate text-xs font-bold", character.owned ? "text-emerald-400" : "text-neutral-300")}>
                                {character.owned ? "Owned" : "Available"}
                            </span>
                        </div>
                        <div className="min-w-0 rounded-xl border border-white/5 bg-brand-deep p-3">
                            <Package size={15} className={cn("mb-2", soldOut ? "text-red-400" : "text-neutral-500")} />
                            <span className="block text-[10px] font-semibold text-neutral-500">Stock</span>
                            <span className={cn("block truncate text-xs font-bold tabular-nums", soldOut ? "text-red-300" : "text-white")}>
                                {hasStock ? (soldOut ? "Sold out" : `${stockRemaining}/${stockLimit}`) : (character.count > 0 ? `x${character.count}` : "None")}
                            </span>
                        </div>
                        <div className="min-w-0 rounded-xl border border-white/5 bg-brand-deep p-3">
                            <Gem size={15} className="mb-2 text-brand-accent" />
                            <span className="block text-[10px] font-semibold text-neutral-500">Price</span>
                            <span className="block truncate text-xs font-bold text-white tabular-nums">
                                {hasPrice ? formatNumber(character.zenith_price) : 'Not listed'}
                            </span>
                        </div>
                    </div>

                    {actions && <div className="pt-1">{actions}</div>}
                </div>
            </div>
        </div>
    );
};
