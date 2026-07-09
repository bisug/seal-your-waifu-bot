import { useEffect, type ReactNode } from 'react';
import { Gem, Hash, Package, ShieldCheck, Tag, X, Target } from 'lucide-react';
import { cn, formatNumber } from '../../utils';
import { Character } from '../../context/UserContext';
import { Badge } from '../ui/Badge';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { motion, AnimatePresence } from 'framer-motion';

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
        <AnimatePresence>
            <div className="fixed inset-0 z-[1000] flex items-center justify-center p-4">
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 bg-black/95 backdrop-blur-sm"
                    onClick={onClose}
                />

                <motion.div
                    initial={{ scale: 0.95, opacity: 0, y: 20 }}
                    animate={{ scale: 1, opacity: 1, y: 0 }}
                    exit={{ scale: 0.95, opacity: 0, y: 20 }}
                    className="relative w-full max-w-[360px] bg-[#050506] rounded-xl flex flex-col overflow-hidden shadow-[0_0_80px_rgba(0,0,0,0.8)] border border-white/[0.05]"
                >
                    {/* Header Controls */}
                    <div className="absolute right-3 top-3 z-20 flex gap-2">
                        <Button
                            variant="ghost"
                            onClick={onClose}
                            className="w-8 h-8 p-0 rounded-md bg-black/40 backdrop-blur-xl border border-white/5 hover:bg-white/10"
                            aria-label="Close"
                        >
                            <X size={16} />
                        </Button>
                    </div>

                    {/* Image Section */}
                    <div className="relative aspect-square flex-shrink-0 bg-brand-deep/30 flex items-center justify-center overflow-hidden group">
                        <div className="absolute inset-0 bg-gradient-to-t from-[#050506] via-transparent to-black/40" />
                        <div className="absolute inset-0 bg-scanline opacity-[0.03] pointer-events-none" />

                        <img
                            src={character.img_url}
                            className="relative z-10 w-full h-full object-contain p-6 drop-shadow-[0_15px_40px_rgba(0,0,0,0.8)] transition-transform duration-1000 group-hover:scale-105"
                            alt={character.name}
                        />

                        <div className="absolute bottom-4 left-4 z-20">
                            <Badge variant="tactical" size="xs" className="bg-brand-accent text-white border-none px-2 py-1">
                                {rarityLabel || 'STANDARD'}
                            </Badge>
                        </div>
                    </div>

                    {/* Content Section */}
                    <div className="flex-1 bg-[#050506] p-5 space-y-5">
                        <div className="space-y-1">
                            <div className="flex items-center gap-1.5 opacity-40">
                                <Target size={10} className="text-brand-accent" />
                                <span className="text-[8px] font-black uppercase tracking-[0.3em] text-white">Registry Entry #{characterId}</span>
                            </div>
                            <h2 className="text-xl font-black text-white leading-tight uppercase tracking-tight">{character.name}</h2>
                            <p className="text-[10px] font-bold text-neutral-600 uppercase tracking-[0.2em]">{character.anime}</p>
                        </div>

                        <div className="grid grid-cols-3 gap-2">
                            <Card variant="tactical" className="p-2.5 bg-white/[0.02] flex flex-col justify-between">
                                <ShieldCheck size={12} className={cn(character.owned ? "text-emerald-500" : "text-neutral-700")} />
                                <div className="mt-2">
                                    <span className="block text-[7px] font-black text-neutral-700 uppercase tracking-widest">STATUS</span>
                                    <span className={cn("block truncate text-[9px] font-black uppercase tracking-tight", character.owned ? "text-emerald-500" : "text-neutral-500")}>
                                        {character.owned ? "SECURED" : "PENDING"}
                                    </span>
                                </div>
                            </Card>
                            <Card variant="tactical" className="p-2.5 bg-white/[0.02] flex flex-col justify-between">
                                <Package size={12} className={cn(soldOut ? "text-red-500" : "text-neutral-500")} />
                                <div className="mt-2">
                                    <span className="block text-[7px] font-black text-neutral-700 uppercase tracking-widest">STOCK</span>
                                    <span className={cn("block truncate text-[9px] font-black uppercase tracking-tight tabular-nums font-mono", soldOut ? "text-red-400" : "text-white")}>
                                        {hasStock ? (soldOut ? "0/0" : `${stockRemaining}/${stockLimit}`) : (character.count > 0 ? `x${character.count}` : "∞")}
                                    </span>
                                </div>
                            </Card>
                            <Card variant="tactical" className="p-2.5 bg-white/[0.02] flex flex-col justify-between">
                                <Gem size={12} className="text-brand-accent" />
                                <div className="mt-2">
                                    <span className="block text-[7px] font-black text-neutral-700 uppercase tracking-widest">VALUE</span>
                                    <span className="block truncate text-[9px] font-black text-white tabular-nums uppercase font-mono">
                                        {hasPrice ? formatNumber(character.zenith_price) : '0'}
                                    </span>
                                </div>
                            </Card>
                        </div>

                        {actions && (
                            <div className="pt-2 border-t border-white/[0.04]">
                                {actions}
                            </div>
                        )}
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    );
};
