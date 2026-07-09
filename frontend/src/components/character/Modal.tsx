import { useEffect, type ReactNode } from 'react';
import { Gem, Hash, Package, ShieldCheck, Tag, X } from 'lucide-react';
import { cn, formatNumber } from '../../utils';
import { Character } from '../../context/UserContext';
import { Badge } from '../ui/Badge';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';

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

    const rarityLabel = character.rarity.replace(/[\u2700-\u27bf]|[\u2190-\u21ff]|[\u2000-\u206f]|[\u2600-\u26ff]|[\u2b00-\u2bff]|[\u00a0-\u00bf]|\u2013|\u2014/g, '').trim().toUpperCase();
    const stockLimit = typeof character.stock_limit === 'number' ? character.stock_limit : null;
    const stockRemaining = typeof character.stock_remaining === 'number'
        ? character.stock_remaining
        : stockLimit !== null && typeof character.sold_count === 'number'
            ? Math.max(0, stockLimit - character.sold_count)
            : null;
    const hasStock = stockLimit !== null && stockRemaining !== null;
    const soldOut = character.sold_out || (hasStock && stockRemaining <= 0);
    const hasPrice = typeof character.zenith_price === 'number' && character.zenith_price > 0;
    const characterId = String(character.id || '');

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/90 backdrop-blur-md p-4">
            <div className="absolute inset-0" onClick={onClose} />

            <div className="relative w-full max-w-md max-h-[90vh] bg-brand-midnight rounded-[2rem] flex flex-col overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)] border border-white/5">
                <Button
                    variant="secondary"
                    onClick={onClose}
                    className="absolute right-4 top-4 z-20 w-10 h-10 p-0 rounded-full bg-black/60 backdrop-blur-xl border-white/10 hover:bg-white/10"
                    aria-label="Close preview"
                >
                    <X size={20} />
                </Button>

                <div className="relative aspect-square flex-shrink-0 bg-brand-deep flex items-center justify-center overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-t from-brand-midnight via-transparent to-black/20" />
                    <img
                        src={character.img_url}
                        className="relative z-10 w-full h-full object-contain p-8 drop-shadow-[0_20px_50px_rgba(0,0,0,0.5)] transition-transform duration-700 hover:scale-105"
                        alt={character.name}
                    />
                </div>

                <div className="flex-1 border-t border-white/5 bg-brand-midnight p-6 space-y-6 overflow-y-auto no-scrollbar">
                    <div className="space-y-3">
                        <div className="flex flex-wrap items-center gap-2">
                            <Badge variant="primary" icon={Tag} size="xs" className="rounded-lg py-1 px-2 uppercase tracking-widest font-black">
                                {rarityLabel || 'STANDARD'}
                            </Badge>
                            {characterId && (
                                <Badge variant="secondary" icon={Hash} size="xs" className="rounded-lg py-1 px-2 font-black tabular-nums">
                                    {characterId}
                                </Badge>
                            )}
                        </div>
                        <div>
                            <h2 className="text-2xl font-black text-white leading-tight uppercase tracking-tight">{character.name}</h2>
                            <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest mt-1">{character.anime}</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-3 gap-3">
                        <Card className="p-3 bg-white/[0.02]">
                            <ShieldCheck size={14} className={cn("mb-2", character.owned ? "text-emerald-500" : "text-neutral-600")} />
                            <span className="block text-[8px] font-black text-neutral-600 uppercase tracking-widest">Ownership</span>
                            <span className={cn("block truncate text-[10px] font-black uppercase tracking-tight mt-0.5", character.owned ? "text-emerald-500" : "text-neutral-400")}>
                                {character.owned ? "SECURED" : "AVAILABLE"}
                            </span>
                        </Card>
                        <Card className="p-3 bg-white/[0.02]">
                            <Package size={14} className={cn("mb-2", soldOut ? "text-red-500" : "text-neutral-500")} />
                            <span className="block text-[8px] font-black text-neutral-600 uppercase tracking-widest">Global Stock</span>
                            <span className={cn("block truncate text-[10px] font-black uppercase tracking-tight mt-0.5 tabular-nums", soldOut ? "text-red-400" : "text-white")}>
                                {hasStock ? (soldOut ? "SOLD OUT" : `${stockRemaining}/${stockLimit}`) : (character.count > 0 ? `x${character.count}` : "UNLIMITED")}
                            </span>
                        </Card>
                        <Card className="p-3 bg-white/[0.02]">
                            <Gem size={14} className="mb-2 text-brand-accent" />
                            <span className="block text-[8px] font-black text-neutral-600 uppercase tracking-widest">Market Value</span>
                            <span className="block truncate text-[10px] font-black text-white tabular-nums uppercase mt-0.5">
                                {hasPrice ? formatNumber(character.zenith_price) : 'N/A'}
                            </span>
                        </Card>
                    </div>

                    {actions && <div className="pt-2">{actions}</div>}
                </div>
            </div>
        </div>
    );
};
