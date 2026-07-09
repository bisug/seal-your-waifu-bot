import { useEffect, type ReactNode } from 'react';
import { Gem, Hash, Package, ShieldCheck, X, Target, Info, Sparkles } from 'lucide-react';
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
        <AnimatePresence>
            <div className="fixed inset-0 z-[1000] flex items-end sm:items-center justify-center p-0 sm:p-6">
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 bg-black/80 backdrop-blur-md"
                    onClick={onClose}
                />

                <motion.div
                    initial={{ y: '100%' }}
                    animate={{ y: 0 }}
                    exit={{ y: '100%' }}
                    transition={{ type: 'spring', damping: 30, stiffness: 300, mass: 0.8 }}
                    className="relative w-full max-w-[420px] bg-brand-midnight rounded-t-[32px] sm:rounded-[32px] flex flex-col overflow-hidden shadow-2xl border-t sm:border border-white/[0.08]"
                >
                    {/* Header Controls */}
                    <div className="absolute right-6 top-6 z-20">
                        <Button
                            variant="ghost"
                            onClick={onClose}
                            className="w-10 h-10 p-0 rounded-full bg-black/40 backdrop-blur-xl border border-white/5 hover:bg-white/10"
                            aria-label="Close"
                        >
                            <X size={20} />
                        </Button>
                    </div>

                    {/* Image Section */}
                    <div className="relative aspect-[4/3] flex-shrink-0 bg-brand-deep/30 flex items-center justify-center overflow-hidden group">
                        <div className="absolute inset-0 bg-gradient-to-t from-brand-midnight via-transparent to-black/40" />
                        <div className="absolute inset-0 bg-scanline opacity-[0.03] pointer-events-none" />
                        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.1),transparent_70%)]" />

                        <motion.img
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            transition={{ delay: 0.1, duration: 0.5 }}
                            src={character.img_url}
                            className="relative z-10 w-full h-full object-contain p-8 drop-shadow-[0_20px_50px_rgba(0,0,0,0.6)] transition-transform duration-1000 group-hover:scale-105"
                            alt={character.name}
                        />

                        <div className="absolute bottom-6 left-6 z-20 flex gap-2">
                            <Badge variant={rarityVariant} size="sm" className="px-3 py-1 border-none shadow-xl backdrop-blur-md font-black">
                                {rarityLabel || 'STANDARD'}
                            </Badge>
                            {character.owned && (
                                <Badge variant="success" size="sm" className="px-3 py-1 border-none shadow-xl backdrop-blur-md font-black">
                                    SECURED
                                </Badge>
                            )}
                        </div>
                    </div>

                    {/* Content Section */}
                    <div className="flex-1 bg-brand-midnight p-6 sm:p-8 space-y-6">
                        <div className="space-y-2">
                            <div className="flex items-center gap-2 opacity-50">
                                <Target size={12} className="text-brand-accent" />
                                <span className="text-[10px] font-black uppercase tracking-[0.4em] text-white font-mono">ASSET_ID: {characterId}</span>
                            </div>
                            <h2 className="text-2xl font-black text-white leading-tight uppercase tracking-tighter drop-shadow-sm">{character.name}</h2>
                            <div className="flex items-center gap-2">
                               <Info size={12} className="text-neutral-600" />
                               <p className="text-[11px] font-bold text-neutral-500 uppercase tracking-widest leading-none">{character.anime}</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-3 gap-3">
                            {[
                                { icon: ShieldCheck, label: 'STATUS', value: character.owned ? "SECURED" : "PENDING", variant: character.owned ? "success" : "secondary" },
                                { icon: Package, label: 'QUANTITY', value: hasStock ? (soldOut ? "DEPLETED" : `${stockRemaining}/${stockLimit}`) : (character.count > 0 ? `x${character.count}` : "UNLIMITED"), variant: soldOut ? "danger" : "default" },
                                { icon: Gem, label: 'ASSET_VAL', value: hasPrice ? formatNumber(character.zenith_price) : '0', variant: 'primary' },
                            ].map((stat, i) => (
                                <Card key={i} variant="tactical" className="p-3 bg-white/[0.02] flex flex-col justify-between border-white/[0.04]">
                                    <stat.icon size={14} className={cn(
                                        stat.variant === 'success' && "text-success",
                                        stat.variant === 'danger' && "text-danger",
                                        stat.variant === 'primary' && "text-brand-accent",
                                        stat.variant === 'default' && "text-neutral-500",
                                        stat.variant === 'secondary' && "text-neutral-700"
                                    )} />
                                    <div className="mt-3">
                                        <span className="block text-[8px] font-black text-neutral-700 uppercase tracking-widest mb-1">{stat.label}</span>
                                        <span className={cn(
                                            "block truncate text-[10px] font-black uppercase tracking-tight tabular-nums font-mono leading-none",
                                            stat.variant === 'success' ? "text-success" : stat.variant === 'danger' ? "text-danger" : "text-white"
                                        )}>
                                            {stat.value}
                                        </span>
                                    </div>
                                </Card>
                            ))}
                        </div>

                        {actions && (
                            <div className="pt-6 border-t border-white/[0.06] flex flex-col gap-4">
                                {actions}
                            </div>
                        )}

                        <div className="flex items-center justify-center gap-2 py-2 opacity-20">
                            <Sparkles size={10} className="text-brand-accent" />
                            <span className="text-[8px] font-black uppercase tracking-[0.4em] text-white">End of Record</span>
                        </div>
                    </div>

                    {/* Safe Area Padding for Mobile Bottom Sheet */}
                    <div className="h-[calc(var(--sab,24px)+4px)] sm:hidden" />
                </motion.div>
            </div>
        </AnimatePresence>
    );
};
