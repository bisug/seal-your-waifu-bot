import React, { useEffect, useState } from 'react';
import { useApi } from '../hooks/useApi';
import { useUser, Pet } from '../context/UserContext';
import { Skeleton } from '../components/ui/Skeleton';
import { ErrorState } from '../components/ui/ErrorState';
import { formatNumber, cn } from '../utils';
import { Bone, Lock, CheckCircle2, Loader2, PawPrint, Sparkles, Gem, Target, Activity, ShieldCheck, ArrowRight } from 'lucide-react';
import { apiFetch, getErrorMessage } from '../api/client';
import { useToast } from '../components/ui/Toast';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { motion, AnimatePresence } from 'framer-motion';

interface PetShopProps {
    onPetClick?: (pet: Pet) => void;
}

interface PetShopResponse {
    pets: Pet[];
    owned: string[];
    owned_ids?: string[];
    current_level: number;
}

const getPetRef = (pet: Pet) => String(pet.petid || pet.id || pet.name || '');

const getPetImageSrc = (pet: Pet) => {
    const src = String(pet.img || pet.img_url || pet.image || pet.photo_url || '').trim();
    return /^https?:\/\//i.test(src) || src.startsWith('/') ? src : '';
};

const PetShopImage = ({ pet, className }: { pet: Pet; className?: string }) => {
    const src = getPetImageSrc(pet);
    const [imageFailed, setImageFailed] = useState(false);

    useEffect(() => {
        setImageFailed(false);
    }, [src]);

    return src && !imageFailed ? (
        <img
            key={src}
            src={src}
            alt={pet.name}
            className={className}
            loading="lazy"
            referrerPolicy="no-referrer"
            onError={() => setImageFailed(true)}
        />
    ) : (
        <div className={cn(className, 'flex items-center justify-center text-neutral-800 bg-brand-surface')}>
            <PawPrint size={40} />
        </div>
    );
};

export const PetShop = ({ onPetClick }: PetShopProps) => {
    const { user, triggerRefresh } = useUser();
    const { addToast } = useToast();
    const { data: shopData, loading, error, execute: fetchPets } = useApi<PetShopResponse>('/shop/pets');
    const [buying, setBuying] = useState<string | null>(null);

    const handleBuy = async (pet: Pet) => {
        if (buying) return;
        const petRef = getPetRef(pet);

        window.Telegram?.WebApp?.showConfirm(
            `AUTHORIZE ACQUISITION OF ${pet.name.toUpperCase()}? SYSTEM SYNC WILL BE AUTOMATIC.`,
            async (confirmed) => {
                if (confirmed) {
                    setBuying(petRef);
                    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
                    try {
                        await apiFetch(`/shop/buy/pet/${encodeURIComponent(petRef)}`, { method: 'POST' });
                        addToast(`Success: ${pet.name} acquired and synced.`, 'success');
                        window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
                        triggerRefresh();
                    } catch (err: any) {
                        addToast(getErrorMessage(err), 'error');
                        window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
                    } finally {
                        setBuying(null);
                    }
                }
            }
        );
    };

    if (loading && !shopData) return (
        <div className="pb-32 pt-8 max-w-2xl mx-auto adaptive-px space-y-10">
            <div className="flex flex-col gap-2">
               <Skeleton className="h-10 w-48 rounded-lg" />
               <Skeleton className="h-4 w-64 rounded-lg opacity-50 mb-4" />
            </div>
            {[1,2,3].map(i => <Skeleton key={i} className="h-40 rounded-[28px]" />)}
        </div>
    );

    if (error && !shopData) return (
        <div className="px-5 py-20 max-w-2xl mx-auto">
            <ErrorState message={error} onAction={fetchPets} />
        </div>
    );

    const pets = shopData?.pets || [];
    const ownedIds = shopData?.owned_ids || [];
    const currentLevel = shopData?.current_level || 0;
    const zenithBalance = user?.stats?.zenith ?? user?.zenith ?? 0;

    return (
        <div className="pb-32 pt-8 max-w-3xl mx-auto adaptive-px space-y-10 select-none">
            <header className="space-y-2">
                <div className="flex items-center gap-4">
                   <div className="w-12 h-12 rounded-2xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center shadow-[0_0_20px_rgba(59,130,246,0.1)]">
                        <Bone className="text-brand-accent" size={26} />
                   </div>
                   <div className="flex flex-col gap-1">
                      <h1 className="text-3xl font-black text-white tracking-tighter uppercase leading-none">Breeder</h1>
                      <div className="flex items-center gap-2">
                         <Target size={11} className="text-neutral-600" />
                         <p className="text-[10px] font-black text-neutral-500 uppercase tracking-widest leading-none">
                            COMPANION ACQUISITION TERMINAL
                         </p>
                      </div>
                   </div>
                </div>
            </header>

            <div className="grid grid-cols-1 gap-5">
                <AnimatePresence mode="popLayout">
                {pets.map((pet, i) => {
                    const petRef = getPetRef(pet);
                    const reqLevel = pet.req_level || 0;
                    const price = pet.zenith_price || 0;
                    const isOwned = ownedIds.includes(petRef) || ownedIds.includes(pet.id) || (shopData?.owned || []).includes(pet.name);
                    const isLocked = !isOwned && currentLevel < reqLevel;
                    const canAfford = zenithBalance >= price;

                    return (
                        <motion.div layout key={pet.id || pet.name} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                            <Card
                                variant="tactical"
                                onClick={() => onPetClick?.({ ...pet, shopIndex: i })}
                                className={cn(
                                    "p-6 flex flex-col sm:flex-row gap-6 items-center group cursor-pointer relative overflow-hidden transition-all duration-500",
                                    isOwned ? "border-success/20 bg-success/[0.02]" : "bg-white/[0.01] border-white/[0.04] hover:bg-white/[0.02] hover:border-white/[0.1]",
                                    isLocked && "opacity-40 grayscale"
                                )}
                            >
                                <div className="relative shrink-0 w-full sm:w-auto flex justify-center">
                                    <div className={cn(
                                        "w-32 h-32 rounded-[24px] overflow-hidden border-2 bg-brand-midnight shadow-2xl group-hover:scale-105 transition-all duration-700 relative z-10",
                                        isOwned ? "border-success/40" : "border-white/[0.05]"
                                    )}>
                                        <PetShopImage pet={pet} className="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110" />
                                        <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
                                    </div>

                                    {isOwned && (
                                        <div className="absolute -top-3 -right-3 sm:top-[-10px] sm:right-[-10px] bg-success text-black p-2 rounded-2xl shadow-[0_0_20px_rgba(16,185,129,0.4)] border-4 border-brand-midnight z-20 animate-in">
                                            <CheckCircle2 size={20} strokeWidth={3} />
                                        </div>
                                    )}

                                    {isLocked && (
                                        <div className="absolute inset-0 flex items-center justify-center z-20">
                                            <div className="w-12 h-12 rounded-full bg-black/60 backdrop-blur-md flex items-center justify-center border border-white/10 text-white shadow-2xl">
                                                <Lock size={24} />
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <div className="flex-1 min-w-0 space-y-5 w-full text-center sm:text-left">
                                    <div className="space-y-2">
                                        <h2 className="text-2xl font-black text-white truncate uppercase tracking-tighter drop-shadow-md group-hover:text-brand-accent transition-colors">{pet.name}</h2>
                                        <div className="flex items-center justify-center sm:justify-start gap-2.5">
                                            <Sparkles size={14} className="text-brand-accent shrink-0 animate-pulse" />
                                            <p className="text-[12px] font-black text-brand-accent uppercase tracking-widest truncate">{pet.ability || 'AUTHORIZED_SYSTEM_PERK'}</p>
                                        </div>
                                    </div>

                                    <div className="flex flex-col sm:flex-row items-center justify-between gap-6 pt-4 border-t border-white/[0.04]">
                                        <div className="flex items-center gap-6">
                                            <div className="space-y-1.5">
                                                <span className="text-[9px] font-black text-neutral-600 uppercase tracking-[0.2em] block">PROTOCOL_COST</span>
                                                <div className="flex items-center justify-center sm:justify-start gap-2">
                                                    <Gem size={16} className="text-brand-accent shadow-sm" />
                                                    <span className="text-lg font-black text-white tabular-nums font-mono leading-none">{formatNumber(price)}</span>
                                                </div>
                                            </div>
                                            <div className="h-8 w-px bg-white/[0.04]" />
                                            <div className="space-y-1.5">
                                                <span className="text-[9px] font-black text-neutral-600 uppercase tracking-[0.2em] block">CLASS_RANK</span>
                                                <Badge variant="tactical" size="xs" className="px-2 py-0.5 rounded-md font-mono border-white/10 bg-white/[0.02]">
                                                   {pet.rarity?.toUpperCase() || 'STANDARD'}
                                                </Badge>
                                            </div>
                                        </div>

                                        <div className="w-full sm:w-auto">
                                            {!isOwned && !isLocked && (
                                                <Button
                                                    variant={canAfford ? "tactical" : "secondary"}
                                                    size="lg"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleBuy(pet);
                                                    }}
                                                    isLoading={buying === petRef}
                                                    disabled={!canAfford}
                                                    className="w-full sm:w-auto px-10 h-12 rounded-[18px] uppercase tracking-[0.2em] text-[11px] font-black shadow-xl active:scale-95"
                                                >
                                                    {canAfford ? 'ACQUIRE' : 'INSUFFICIENT'}
                                                </Button>
                                            )}

                                            {isOwned && (
                                                <Badge variant="success" className="py-2.5 px-8 rounded-xl font-black tracking-[0.2em] uppercase text-[10px] border-none shadow-lg bg-success/10 text-success">
                                                    SECURED
                                                </Badge>
                                            )}

                                            {isLocked && (
                                                <div className="flex flex-col items-center sm:items-end gap-2">
                                                    <Badge variant="tactical" icon={Lock} className="py-2.5 px-8 rounded-xl font-black tracking-[0.2em] uppercase text-[10px] opacity-40">
                                                        LOCKED
                                                    </Badge>
                                                    <span className="text-[9px] font-black text-neutral-700 uppercase tracking-widest">MIN_LVL_{reqLevel}_REQ</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </Card>
                        </motion.div>
                    );
                })}
                </AnimatePresence>
            </div>

            <div className="flex items-center justify-center gap-3 opacity-20 py-8">
               <Sparkles size={12} className="text-brand-accent" />
               <span className="text-[9px] font-black uppercase tracking-[0.4em] text-white">Breeding Terminal Secure</span>
            </div>
        </div>
    );
};
